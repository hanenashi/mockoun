import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import { getFirestore, collection, query, orderBy, onSnapshot, doc, getDoc, setDoc, addDoc } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-firestore.js";

// ---> NEW: Import from the Python Bridge! <---
import { ENV_USER, ENV_CLUB } from './env_config.js';

// Your Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyA1_4kUExI_Ra7L-Dk7qGhoxai7Xc2caaX",
  authDomain: "murkypond-vault-fc61c.firebaseapp.com",
  projectId: "murkypond-vault-fc61c",
  storageBucket: "murkypond-vault-fc61c.firebasestorage.app",
  messagingSenderId: "81248398306",
  appId: "1:81248398306:web:491204f0fa954c6e1867bb"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

// ---> NEW: Dynamically assign from the .env file! <---
const TARGET_CLUB = ENV_CLUB;
const USER_ID = ENV_USER; 

const feedContainer = document.getElementById('feedContainer');
const markReadBtn = document.getElementById('markReadBtn');
const sendPostBtn = document.getElementById('sendPostBtn');
const newPostText = document.getElementById('newPostText');

let lastReadId = 0;
let highestLoadedId = 0;

// Update Header to show the dynamic club name
document.getElementById('clubNameDisplay').innerText = `Club: ${TARGET_CLUB}`;

// ==========================================
// 1. CLOUD SYNC (READ STATE)
// ==========================================
async function initializeVault() {
    feedContainer.innerHTML = `<div class="text-center text-blue-500 py-8 animate-pulse">Syncing profile for ${USER_ID}...</div>`;
    const userRef = doc(db, 'users', USER_ID);
    
    try {
        const userSnap = await getDoc(userRef);
        if (userSnap.exists() && userSnap.data()[TARGET_CLUB]) {
            lastReadId = userSnap.data()[TARGET_CLUB];
        } else {
            await setDoc(userRef, { [TARGET_CLUB]: 0 }, { merge: true });
        }
    } catch (error) {
        console.error("Profile sync failed:", error);
    }
    
    listenToVault();
}

// ==========================================
// 2. LISTEN TO FEED (REAL-TIME POSTS)
// ==========================================
function listenToVault() {
    const postsRef = collection(db, 'clubs', TARGET_CLUB, 'posts');
    const q = query(postsRef, orderBy('ts', 'desc'));

    onSnapshot(q, (snapshot) => {
        feedContainer.innerHTML = ''; 
        highestLoadedId = 0;
        
        if (snapshot.empty) {
            feedContainer.innerHTML = '<div class="text-center text-gray-500 py-8">No posts found in Vault.</div>';
            return;
        }
        
        snapshot.forEach((doc) => {
            const post = doc.data();
            if (post.p_id > highestLoadedId) highestLoadedId = post.p_id;
            renderPost(post);
        });
    });
}

// ==========================================
// 3. RENDER POST UI
// ==========================================
function renderPost(post) {
    const postDiv = document.createElement('div');
    const isUnread = post.p_id > lastReadId;
    
    postDiv.className = isUnread 
        ? "bg-blue-50 p-4 rounded-lg shadow border-l-4 border-blue-500 transition duration-300"
        : "bg-white p-4 rounded-lg shadow border-l-4 border-transparent transition duration-300";
    
    let timeString = "Unknown Time";
    if (post.ts) {
        const date = new Date(post.ts);
        timeString = date.toLocaleTimeString('cs-CZ', { hour: '2-digit', minute: '2-digit' });
    }

    postDiv.innerHTML = `
        <div class="flex justify-between items-baseline mb-2 border-b pb-2 ${isUnread ? 'border-blue-200' : 'border-gray-200'}">
            <span class="font-bold ${isUnread ? 'text-blue-800' : 'text-gray-800'}">${post.auth || 'Anon'}</span>
            <div class="text-xs text-gray-400 space-x-2">
                ${isUnread ? '<span class="text-blue-500 font-bold uppercase tracking-wider">Nový</span>' : ''}
                <span>ID: ${post.p_id || 'N/A'}</span>
                <span>${timeString}</span>
            </div>
        </div>
        <div class="text-gray-700 prose prose-sm max-w-none break-words">
            ${post.html || ''}
        </div>
    `;
    feedContainer.appendChild(postDiv);
}

// ==========================================
// 4. MARK ALL AS READ
// ==========================================
markReadBtn.addEventListener('click', async () => {
    if (highestLoadedId > 0 && highestLoadedId > lastReadId) {
        const originalText = markReadBtn.innerText;
        markReadBtn.innerText = "Ukládám...";
        markReadBtn.disabled = true;
        
        try {
            await setDoc(doc(db, 'users', USER_ID), { [TARGET_CLUB]: highestLoadedId }, { merge: true });
            lastReadId = highestLoadedId;
            location.reload(); 
        } catch (error) {
            console.error("Mark Read Error:", error);
            markReadBtn.innerText = "Chyba!";
            setTimeout(() => { markReadBtn.innerText = originalText; markReadBtn.disabled = false; }, 2000);
        }
    }
});

// ==========================================
// 5. OUTBOX (SEND POST)
// ==========================================
sendPostBtn.addEventListener('click', async (e) => {
    e.preventDefault(); 
    
    const text = newPostText.value.trim();
    if (!text) return; 

    sendPostBtn.innerText = "Odesílám...";
    sendPostBtn.disabled = true;
    sendPostBtn.classList.replace('bg-blue-600', 'bg-gray-400');

    try {
        await addDoc(collection(db, 'outbox'), {
            club_id: TARGET_CLUB,
            text: text,
            ts: Date.now(),
            status: "pending"
        });

        newPostText.value = '';
        sendPostBtn.innerText = "✓ Ve frontě";
        sendPostBtn.classList.replace('bg-gray-400', 'bg-green-500');
        
        setTimeout(() => {
            sendPostBtn.innerText = "Odeslat";
            sendPostBtn.classList.replace('bg-green-500', 'bg-blue-600');
            sendPostBtn.disabled = false;
        }, 2000);

    } catch (error) {
        console.error("Outbox Error:", error);
        sendPostBtn.innerText = "Chyba odeslání!";
        sendPostBtn.classList.replace('bg-gray-400', 'bg-red-500');
        
        setTimeout(() => {
            sendPostBtn.innerText = "Odeslat";
            sendPostBtn.classList.replace('bg-red-500', 'bg-blue-600');
            sendPostBtn.disabled = false;
        }, 3000);
    }
});

// Boot the app
initializeVault();
