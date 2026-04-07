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
