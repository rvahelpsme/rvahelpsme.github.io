// ==========================================================================
// Configuration & State
// ==========================================================================
const CONFIG = {
    isLocal: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    get backendUrl() { return this.isLocal ? "http://127.0.0.1:8080" : "https://rhonda-backend-1071663876445.us-east4.run.app"; },
    rotationInterval: 3500,
    placeholders: [
        "Ask me anything...", "Pregúntame cualquier cosa...", "اسألني أي شيء...",
        "هر چیزی از من بپرسید...", "له ما څخه هر څه وپوښتئ...", "Pergunte-me qualquer coisa...",
        "मलाई जे पनि सोध्नुहोस्...", "ကျွန်မကို ဘာမဆိုမေးပါ..."
    ],
    speechLangs: { en: 'en-US', es: 'es-US', ar: 'ar-SA', fa: 'fa-IR', ps: 'ps-AF', pt: 'pt-BR', ne: 'ne-NP', my: 'my-MM' },
    icons: {
        speaker: `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>`,
        housing: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>`,
        food: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"></path><path d="M7 2v20"></path><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"></path></svg>`,
        legal: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 14h2M19 14h2M12 2v20M8 6h8M2 14c0 3 2 5 5 5s5-2 5-5M12 14c0 3 2 5 5 5s5-2 5-5"></path></svg>`,
        health: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>`,
        transit: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M3 11V6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v5"></path><circle cx="7" cy="18" r="2"></circle><circle cx="17" cy="18" r="2"></circle></svg>`,
        work: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>`
    }
};

const STATE = {
    sessionHash: null, lang: 'en', hasEngaged: false, placeholderIdx: 0, timer: null,
    isListening: false, audio: new Audio(),
    secretPassphrase: null, dynamicCount: 0, hasRevealedPassport: false
};

// ==========================================================================
// DOM Elements
// ==========================================================================
const DOM = {
    chat: document.getElementById('chat-container'),
    input: document.getElementById('user-input'),
    send: document.getElementById('send-btn'),
    mic: document.getElementById('mic-btn'),
    header: document.getElementById('app-header')
};

// ==========================================================================
// UI Controllers
// ==========================================================================
const UI = {
    startRotation() {
        if (STATE.hasEngaged) return;
        STATE.timer = setInterval(() => {
            STATE.placeholderIdx = (STATE.placeholderIdx + 1) % CONFIG.placeholders.length;
            DOM.input.placeholder = CONFIG.placeholders[STATE.placeholderIdx];
            DOM.input.dir = [2, 3, 4].includes(STATE.placeholderIdx) ? "rtl" : "ltr";
        }, CONFIG.rotationInterval);
    },
    stopRotation() { clearInterval(STATE.timer); DOM.input.placeholder = ""; DOM.input.dir = "ltr"; },
    autoResize() { DOM.input.style.height = 'auto'; DOM.input.style.height = DOM.input.scrollHeight + 'px'; },
    updateSendBtn() {
        const hasText = DOM.input.value.trim().length > 0;
        DOM.send.classList.toggle('active', hasText);
        DOM.send.disabled = !hasText;
        DOM.input.dir = hasText ? "auto" : "ltr";
    },
    scrollToBottom() { DOM.chat.scrollTop = DOM.chat.scrollHeight; },
    appendMessage(sender, text, lang = STATE.lang) {
        const row = document.createElement('div');
        row.className = `message-row ${sender}`;
        const msg = document.createElement('div');
        msg.className = 'message';
        msg.innerHTML = text.replace(/\n/g, '<br>');

        if (sender === 'rhonda') {
            const actions = document.createElement('div');
            actions.className = 'actions';
            const speaker = document.createElement('div');
            speaker.className = 'action-icon';
            speaker.innerHTML = CONFIG.icons.speaker;
            const cleanText = text.replace(/'/g, "\\'").replace(/"/g, '\\"');
            speaker.onclick = () => API.fetchAudio(cleanText, speaker, lang);
            actions.appendChild(speaker);
            row.appendChild(msg);
            row.appendChild(actions);
        } else {
            row.appendChild(msg);
        }
        DOM.chat.appendChild(row);
        this.scrollToBottom();
    },
    renderIntentGrid() {
        const wrapper = document.createElement('div');
        wrapper.className = `message-row rhonda`;
        const gridDiv = document.createElement('div');
        gridDiv.className = 'intent-grid';
        gridDiv.innerHTML = `
            <button class="intent-btn" onclick="API.sendMessage('I need help finding stable housing.')">
                ${CONFIG.icons.housing} <span class="intent-label">Housing</span>
            </button>
            <button class="intent-btn" onclick="API.sendMessage('I need help getting food for my family.')">
                ${CONFIG.icons.food} <span class="intent-label">Food</span>
            </button>
            <button class="intent-btn" onclick="API.sendMessage('I need legal help.')">
                ${CONFIG.icons.legal} <span class="intent-label">Legal</span>
            </button>
            <button class="intent-btn" onclick="API.sendMessage('I need healthcare.')">
                ${CONFIG.icons.health} <span class="intent-label">Health</span>
            </button>
            <button class="intent-btn" onclick="API.sendMessage('I need help with transportation.')">
                ${CONFIG.icons.transit} <span class="intent-label">Transit</span>
            </button>
            <button class="intent-btn" onclick="API.sendMessage('I need help with jobs or school.')">
                ${CONFIG.icons.work} <span class="intent-label">Education</span>
            </button>
        `;
        wrapper.appendChild(gridDiv);
        DOM.chat.appendChild(wrapper);
        this.scrollToBottom();
    }
};

// ==========================================================================
// Speech Recognition
// ==========================================================================
const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = SpeechAPI ? new SpeechAPI() : null;
if (recognition) { recognition.continuous = true; recognition.interimResults = true; }

const MIC = {
    start() {
        if (!recognition) return;
        UI.stopRotation();
        DOM.input.value = '';
        recognition.lang = CONFIG.speechLangs[STATE.lang] || 'en-US';
        recognition.start();
        DOM.mic.classList.add('listening');
        STATE.isListening = true;
    },
    stop() {
        if (!STATE.isListening || !recognition) return;
        STATE.isListening = false;
        recognition.stop();
        DOM.mic.classList.remove('listening');
    },
    toggle() { STATE.isListening ? this.stop() : this.start(); }
};

// ==========================================================================
// API & Logic
// ==========================================================================
const API = {
    async fetchAudio(text, btn, lang) {
        btn.style.opacity = "0.5";
        try {
            const res = await fetch(`${CONFIG.backendUrl}/tts`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, lang }) });
            const data = await res.json();
            if (data.audio_base64) {
                STATE.audio.src = `data:audio/mp3;base64,${data.audio_base64}`;
                STATE.audio.play();
                STATE.audio.onended = () => btn.style.opacity = "1";
            }
        } catch (e) { btn.style.opacity = "1"; }
    },
    async sendMessage(triggerText = null, isHidden = false) {
        const text = triggerText || DOM.input.value.trim();
        if (!text) return;

        // Display user bubble only if it's not a silent system trigger
        if (!isHidden && text !== "INIT_GREETING" && !text.startsWith("SYSTEM_")) {
            STATE.hasEngaged = true;
            UI.stopRotation();
            MIC.stop();
            UI.appendMessage('user', text);
            DOM.input.value = '';
            UI.autoResize();
            UI.updateSendBtn();
        }

        try {
            const res = await fetch(`${CONFIG.backendUrl}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, session_hash: STATE.sessionHash })
            });
            const data = await res.json();

            if (res.ok && data.status === 'success') {
                if (data.session_hash) STATE.sessionHash = data.session_hash;
                if (data.language) STATE.lang = data.language;
                if (data.new_passphrase) STATE.secretPassphrase = data.new_passphrase;

                // Admin UI Indicator feature (Phase 6)
                if (data.session_hash && data.session_hash !== STATE.sessionHash && text.split(' ').length === 4) {
                    DOM.input.parentElement.style.border = "2px solid #0F794B";
                }

                if (text === "INIT_GREETING") {
                    UI.appendMessage('rhonda', data.response, STATE.lang);
                    UI.renderIntentGrid(); // Spawns the grid immediately after the welcome text
                } else if (isHidden && text.startsWith("SYSTEM_") || isHidden && text === "How do you protect my privacy and data?") {
                    // Silently append Rhonda's follow-up texts without a user bubble prompting it
                    UI.appendMessage('rhonda', data.response, STATE.lang);
                } else {
                    UI.appendMessage('rhonda', data.response, STATE.lang);

                    // ============================================
                    // ONBOARDING TIMING LOGIC (Phases 2, 3 & 4)
                    // ============================================
                    if (!data.is_static) {
                        STATE.dynamicCount++; // Only count messages that actually query Gemini

                        // Phase 2: Follow up with Privacy text 1.5s after answering their very first question
                        if (STATE.dynamicCount === 1) {
                            setTimeout(() => API.sendMessage("How do you protect my privacy and data?", true), 1500);
                        }

                        // Phase 3 & 4: Passport Morph after 3 messages
                        if (STATE.dynamicCount >= 3 && !STATE.hasRevealedPassport && STATE.secretPassphrase) {
                            STATE.hasRevealedPassport = true;
                            setTimeout(() => {
                                DOM.header.innerHTML = `<span>${STATE.secretPassphrase}</span>`;
                                DOM.header.classList.add("passphrase-mode", "glow");
                                API.sendMessage("SYSTEM_PASSPORT_REVEAL", true);
                            }, 2000);

                            setTimeout(() => {
                                API.sendMessage("SYSTEM_SUMMARY_HINT", true);
                            }, 5000);
                        }
                    }
                }
            }
        } catch (e) {
            if (!isHidden) UI.appendMessage('rhonda', "Connection error.");
        }
    }
};

// ==========================================================================
// Initialization & Listeners
// ==========================================================================
DOM.input.onfocus = UI.stopRotation;
DOM.input.onblur = () => { if (!DOM.input.value.trim() && !STATE.hasEngaged) UI.startRotation(); };
DOM.input.oninput = () => { UI.autoResize(); UI.updateSendBtn(); };
DOM.input.onkeydown = (e) => {
    MIC.stop();
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (!DOM.send.disabled) API.sendMessage(); }
};
DOM.send.onclick = () => API.sendMessage();

if (recognition) {
    DOM.mic.onclick = () => MIC.toggle();
    recognition.onresult = (e) => {
        if (!STATE.isListening) return;
        let transcript = '';
        for (let i = 0; i < e.results.length; ++i) transcript += e.results[i][0].transcript;
        DOM.input.value = transcript;
        UI.autoResize();
        UI.updateSendBtn();
    };
    recognition.onend = () => { DOM.mic.classList.remove('listening'); STATE.isListening = false; };
    recognition.onerror = () => { DOM.mic.classList.remove('listening'); STATE.isListening = false; };
}

// Provider Handoff Click Listener (Phase 5)
DOM.header.addEventListener('click', async () => {
    if (!DOM.header.classList.contains('passphrase-mode')) return;
    DOM.header.classList.remove('glow');
    UI.appendMessage('rhonda', "Generating your bilingual provider summary...", STATE.lang);

    try {
        const res = await fetch(`${CONFIG.backendUrl}/summary`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_hash: STATE.sessionHash, lang: STATE.lang })
        });
        const data = await res.json();

        if (res.ok && data.status === 'success') {
            const cardHtml = `
                <div class="summary-card" style="background:#FFF; border:2px solid var(--pi-send-active); border-radius:24px; padding:20px; margin-top:10px;">
                    <div style="color:var(--pi-send-active); font-weight:bold; margin-bottom:15px; text-transform:uppercase; font-size:14px;">Provider Handoff Summary</div>
                    <div style="display:flex; gap:15px;">
                        <div style="flex:1; border-right:1px solid var(--pi-user-bubble); padding-right:15px;">${data.english}</div>
                        <div style="flex:1;" dir="auto">${data.translated}</div>
                    </div>
                </div>
            `;
            const row = document.createElement('div');
            row.className = 'message-row rhonda';
            row.innerHTML = cardHtml;
            DOM.chat.appendChild(row);
            UI.scrollToBottom();
        }
    } catch (err) { UI.appendMessage('rhonda', "Failed to generate summary.", STATE.lang); }
});

// Start the flow automatically on page load
UI.startRotation();
API.sendMessage("INIT_GREETING", true);