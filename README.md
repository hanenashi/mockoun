# Mockoun

**Repository:** [https://github.com/hanenashi/mockoun](https://github.com/hanenashi/mockoun)

## 📌 TL;DR
Mockoun is a lightweight local sandbox designed to mimic the legacy HTML structure and endpoints of the okoun.cz message board. It allows developers to safely build, test, and iterate on scraping tools, automated proxies, and modern decoupled GUIs without hammering the live production servers, triggering rate limits, or risking IP bans. 

It's the dummy target for the MurkyPond harvester.

## ⚙️ Technical Details
* **Core Technology:** Lightweight Python web server (Flask).
* **Architecture:** In-memory state mimicking Okoun's database to allow for rapid read/write testing during development.
* **Mocked Endpoints:**
  * `/myBoards.jsp`: Replicates the exact `form.login` structure and handles dummy session cookies to test authentication logic.
  * `/boards/{club_id}`: Generates the legacy DOM structure expected by headless browsers (`div.item[id^='article-']`, `span.user`, `div.content`).
* **Pagination Simulation:** Dynamically generates `a.older` links to test scraper loops and stopping conditions.

---

## 📋 TODO List

- [ ] Initialize Python environment and `requirements.txt`
- [ ] Create base Flask application skeleton (`app.py`)
- [ ] Implement the `/myBoards.jsp` GET (return HTML form) and POST (set dummy cookie) routes
- [ ] Implement the `/boards/<club_id>` GET route with dynamic legacy HTML generation
- [ ] Add basic pagination logic (append `a.older` if mock page < max pages)
- [ ] Add an array of dummy posts to act as the in-memory database
- [ ] Implement a POST route to accept new messages and append them to the in-memory database

---

## 🗺️ Roadmap & Brainstorming

### Pre-Alpha: The "Truman Show" Phase
**Goal:** Trick the existing harvester into thinking it's on the real site.
* Get the Flask server running locally on port 5000.
* Point the Playwright engine to `127.0.0.1:5000`.
* Ensure the harvester can successfully "log in", navigate pages, scrape the mocked JSON, and push it to Firestore without throwing a single DOM error.

### Alpha: The Two-Way Loop
**Goal:** Establish full read/write capabilities using the custom modern GUI.
* Build a mock `/post` endpoint in Mockoun that accepts form-encoded data.
* Develop the first draft of the new modern GUI frontend.
* Connect the new GUI directly to Firestore (Read).
* Wire the new GUI to send post requests to the Mockoun `/post` endpoint (Write).
* Verify that sending a message from the new GUI hits Mockoun, which then gets scraped by the harvester, synced to Firestore, and instantly appears on the new GUI.

### Beta: The Live Switch
**Goal:** Unplug from the Matrix and connect to the real Okoun.cz.
* Swap the harvester URLs from `localhost` back to `https://www.okoun.cz`.
* Create the actual proxy middleware (or Cloud Function) that will handle incoming POST requests from the new GUI and forward them to the live Okoun servers using Playwright/Requests.
* Implement robust error handling for real-world scenarios: 502 Bad Gateway errors from Okoun, session timeouts, and stale cookies.
* Optimize the harvester's loop frequency to respect Okoun's actual server load.
* 
