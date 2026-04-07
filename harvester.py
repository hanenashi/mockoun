import os
import time
import logging
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright, BrowserContext, Page
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================
CONFIG = {
    "TARGET_CLUB_ID": os.getenv("OKOUN_CLUB", "nepotrebny_pokus"),
    "FIREBASE_KEY_PATH": "serviceAccountKey.json",
    "USER_DATA_DIR": os.path.join("data", "browser_profile"),
    "BASE_URL": os.getenv("OKOUN_BASE_URL", "http://127.0.0.1:5000"),
    "OKOUN_USER": os.getenv("OKOUN_USER", "blaznik"),
    "OKOUN_PASS": os.getenv("OKOUN_PASS", "dummy_pass"), 
    "PAGES_TO_SCRAPE": 3,   
    "HEADLESS": True,  
    "KEEP_BROWSER_OPEN": True,
}

# ==========================================
# LOGGING SETUP
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pondweller.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

NOISE_BLOCKLIST = ["xgemius", "gemius.pl", "googletagmanager", "google-analytics", "hit.gemius.pl", "lsget"]

def launch_context(headless: bool = False) -> tuple[Any, BrowserContext, Page]:
    os.makedirs(CONFIG["USER_DATA_DIR"], exist_ok=True)
    pw = sync_playwright().start()
    
    args = [
        "--disable-blink-features=AutomationControlled",
        "--no-default-browser-check",
        "--disable-infobars",
        "--start-maximized" if not headless else "--window-size=1920,1080"
    ]

    context = pw.chromium.launch_persistent_context(
        user_data_dir=CONFIG["USER_DATA_DIR"],
        headless=headless,
        args=args,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        viewport=None, 
    )
    
    page = context.pages[0] if context.pages else context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
    
    def route_interceptor(route):
        if any(noise in route.request.url for noise in NOISE_BLOCKLIST):
            route.abort()
        else:
            route.continue_()
            
    page.route("**/*", route_interceptor)
    return pw, context, page

def teardown(pw, context):
    try: context.close()
    except: pass
    try: pw.stop()
    except: pass

def init_firebase():
    logger.info("Initializing Firebase Vault...")
    cred = credentials.Certificate(CONFIG["FIREBASE_KEY_PATH"])
    firebase_admin.initialize_app(cred)
    return firestore.client()

def ensure_login(page):
    logger.info("Checking authentication status...")
    page.goto(f"{CONFIG['BASE_URL']}/myBoards.jsp", wait_until="domcontentloaded")
    
    if page.locator("form.login").count() > 0:
        logger.info(f"Login required. Authenticating as '{CONFIG['OKOUN_USER']}'...")
        page.fill("form.login input[name='login']", CONFIG["OKOUN_USER"])
        page.fill("form.login input[name='password']", CONFIG["OKOUN_PASS"])
        page.click("form.login button.submit")
        
        try:
            page.wait_for_selector("div.user b, a.logout", timeout=5000)
            logger.info("Login successful.")
        except Exception:
            logger.warning("Login submitted but could not strictly verify. Proceeding...")
    else:
        logger.info("Session active. Already logged in.")

# ==========================================
# ---> THE NEW DIRECT API PIPELINE <---
# ==========================================
def process_outbox(page, db):
    outbox_ref = db.collection('outbox').where(filter=FieldFilter('status', '==', 'pending')).stream()
    messages = list(outbox_ref)
    
    if not messages: return 

    for doc in messages:
        msg = doc.to_dict()
        logger.info(f"Found pending message for {msg['club_id']}! Preparing to post...")
        
        try:
            url = f"{CONFIG['BASE_URL']}/boards/{msg['club_id']}"
            page.goto(url, wait_until="domcontentloaded")
            
            logger.info("Extracting Okoun security tokens (tukan) for direct API submission...")
            
            # Extract the hidden IDs Okoun needs to accept a post
            form_data = page.evaluate("""() => {
                return {
                    boardId: document.querySelector('input[name="boardId"]')?.value,
                    tukan: document.querySelector('input[name="tukan"]')?.value
                };
            }""")
            
            if not form_data or not form_data.get('boardId') or not form_data.get('tukan'):
                raise Exception("Could not find required security tokens (boardId or tukan) on the page.")

            # Build the exact HTTP POST payload the server expects
            payload = {
                "boardId": form_data["boardId"],
                "title": "",
                "body": msg['text'],
                "bodyType": "html",
                "tukan": form_data["tukan"],
                "post": "Odeslat"  # <--- THIS IS THE MAGIC KEY WE WERE MISSING
            }

            logger.info("Bypassing UI entirely: Firing raw HTTP POST request...")
            response = page.request.post(f"{CONFIG['BASE_URL']}/postArticle.do", form=payload)
            
            if not response.ok:
                raise Exception(f"Server rejected the post. HTTP Status: {response.status}")
            
            # Wait a second, then reload the page so the scrape catches the new post
            time.sleep(1)
            page.reload(wait_until="domcontentloaded")
            
            # Mark as sent
            doc.reference.update({"status": "sent"})
            logger.info("Message successfully posted via direct API and marked as 'sent'.")
            
        except Exception as e:
            logger.error(f"Failed to post message: {e}")

def scrape_club(page, club_id: str, pages_to_scrape: int) -> List[Dict]:
    url = f"{CONFIG['BASE_URL']}/boards/{club_id}"
    page.goto(url, wait_until="domcontentloaded")
    
    try:
        newest_link = page.locator("a:has-text('nejnovější')").first
        if newest_link.count() > 0:
            newest_link.click()
            page.wait_for_load_state("domcontentloaded")
            time.sleep(1) 
    except Exception:
        pass 
    
    all_posts = []

    for current_page in range(1, pages_to_scrape + 1):
        try:
            page.wait_for_selector("div.item[id^='article-']", timeout=10000)
        except Exception:
            break

        posts_on_page = page.evaluate("""() => {
            const results = [];
            const elements = document.querySelectorAll('div.item[id^="article-"]'); 
            
            elements.forEach(el => {
                try {
                    const p_id = parseInt(el.id.replace('article-', ''), 10);
                    const auth_el = el.querySelector('span.user');
                    const auth = auth_el ? auth_el.innerText.trim() : 'Anon';
                    const body_el = el.querySelector('div.content');
                    let html = body_el ? body_el.innerHTML.trim() : '';

                    if (p_id && html) {
                        results.push({ p_id, auth, html, ts: Date.now() });
                    }
                } catch (err) {}
            });
            return results;
        }""")
        all_posts.extend(posts_on_page)

        if current_page < pages_to_scrape:
            try:
                older_link = page.locator("a.older:has-text('starší')").first
                if older_link.count() > 0:
                    older_link.click()
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(1.5)
                else:
                    break
            except Exception:
                break

    unique_posts = {p['p_id']: p for p in all_posts}.values()
    return list(unique_posts)

def push_to_vault(db, club_id: str, posts: List[Dict]):
    if not posts: return
    collection_ref = db.collection('clubs').document(club_id).collection('posts')
    chunks = [posts[i:i + 450] for i in range(0, len(posts), 450)]
    for chunk in chunks:
        batch = db.batch()
        for post in chunk:
            doc_ref = collection_ref.document(str(post['p_id']))
            batch.set(doc_ref, post, merge=True)
        batch.commit()

def run_harvester():
    db = init_firebase()
    logger.info("Booting Playwright Engine (PIKER Engine) in HEADLESS mode...")
    pw, context, page = launch_context(headless=CONFIG["HEADLESS"])
    
    try:
        ensure_login(page)
        logger.info("🔄 Starting infinite harvest loop! Press Ctrl+C in this terminal to stop.")
        
        while True:
            process_outbox(page, db)
            posts = scrape_club(page, CONFIG["TARGET_CLUB_ID"], CONFIG["PAGES_TO_SCRAPE"])
            push_to_vault(db, CONFIG["TARGET_CLUB_ID"], posts)
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("🛑 User manually interrupted the harvester loop.")
    except Exception as e:
        logger.error(f"Harvester encountered a failure: {e}")
    finally:
        logger.info("Shutting down Harvester.")
        teardown(pw, context)
        
if __name__ == "__main__":
    logger.info("=== MURKYPOND HARVESTER STARTED ===")
    run_harvester()