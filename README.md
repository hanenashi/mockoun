# MurkyPond / Mockoun Ecosystem

**Repository:** [https://github.com/hanenashi/mockoun](https://github.com/hanenashi/mockoun)

## 📌 TL;DR
What started as **Mockoun** (a lightweight local sandbox to mimic okoun.cz endpoints) has evolved into the **MurkyPond Ecosystem**: a fully decoupled, modern, real-time web architecture layered over a 20-year-old legacy message board. 

It allows users to browse and post to Okoun via a lightning-fast, mobile-friendly Tailwind/React-style GUI, completely bypassing Okoun's legacy frontend, CORS restrictions, and CSS traps.

## 🏗️ Architecture Overview

The system is split into four distinct, synchronized components:

1. **The Sandbox (Mockoun Backend)**
   * *Tech:* Python + Flask.
   * *Role:* A local dummy server (`localhost:5000`) that safely replicates Okoun's DOM structure, pagination, and `/post` endpoints for risk-free testing without triggering production IP bans.
2. **The Engine (MurkyPond Harvester)**
   * *Tech:* Python + Playwright.
   * *Role:* A headless background daemon. It continuously scrapes the target club, converts the nested HTML DOM into clean JSON, and syncs it to the cloud. It also acts as the "Postman," picking up pending messages from the cloud and firing direct API POST requests to Okoun's backend using extracted `tukan` CSRF tokens.
3. **The Vault (Firebase Firestore)**
   * *Tech:* Google Cloud NoSQL Database.
   * *Role:* The central brain. Holds real-time syncs of scraped posts (`clubs`), cross-device read states (`users`), and pending outbound messages (`outbox`).
4. **The Modern GUI (Alpha Web App)**
   * *Tech:* HTML, Vanilla JS, Tailwind CSS.
   * *Role:* The serverless frontend. Connected directly to Firestore via websockets, it renders posts instantly, tracks read states, and drops new posts into the "Outbox" queue for the Harvester to deliver.

## 🚀 How to Run

1. **Configure `.env`**
   Create a `.env` file in the root directory with your target credentials:
   ```env
   OKOUN_BASE_URL=[https://www.okoun.cz](https://www.okoun.cz)
   OKOUN_USER=your_username
   OKOUN_PASS=your_password
   OKOUN_CLUB=nepotrebny_pokus
   ```

2. **Boot the Matrix**
   Run the `run.bat` script. This executes the initialization sequence:
   * **[0/3] Python Bridge:** Reads your `.env` and generates a Javascript config for the frontend.
   * **[1/3] Mockoun Backend:** Spins up the local Flask sandbox (Optional, if targeting live site).
   * **[2/3] Frontend UI:** Starts the Python HTTP server and opens your browser to the new GUI.
   * **[3/3] Harvester Daemon:** Launches Playwright in headless mode to begin the infinite Scrape/Sync/Post loop.

---

## ✅ Changelog & Completed Milestones

- [x] **Pre-Alpha (The Truman Show):** Built Flask sandbox with dummy `/myBoards.jsp` and pagination routing.
- [x] **Alpha (The Two-Way Loop):** Established read/write to Firestore. Built the Tailwind GUI with unread badges and cross-device sync.
- [x] **The Outbox Pattern:** Solved CORS by turning Firebase into a messaging queue. GUI drops to `outbox`, Python picks up and delivers.
- [x] **The Bridge:** Dynamically inject `.env` configurations into the browser sandbox via pre-boot Python script.
- [x] **The API Strike (Beta Breakthrough):** Bypassed Okoun's CSS invisibility traps and legacy YUI button scripts by extracting the `tukan` token and injecting raw HTTP POST requests directly into `postArticle.do`.

---

## 🗺️ Roadmap: V1.0 Release

### Media & Formatting
- [ ] **Image Parsing:** Update the Harvester to properly extract image URLs from legacy Okoun tags and render them natively in the Tailwind GUI.
- [ ] **Markdown Support:** Ensure formatting translates cleanly between the modern GUI and Okoun's legacy parsers.

### Interaction
- [ ] **Threaded Replies:** Wire up the "Odpovědět" UI button to pass a `reply_to_id` into the Outbox. Update the Harvester's API payload to correctly link replies on the Okoun backend.
- [ ] **Club Switching:** Allow dynamic navigation between multiple clubs via the GUI without restarting the Harvester.

### Deployment
- [ ] **Cloud / Pi Hosting:** Migrate the Harvester daemon from the local desktop to a Raspberry Pi or cheap cloud VPS so the engine runs 24/7 without needing an open terminal.
