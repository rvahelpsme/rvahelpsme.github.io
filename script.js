const CONFIG = {
    isLocal: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    get backendUrl() { return this.isLocal ? "http://127.0.0.1:8080" : "https://rhonda-backend-1071663876445.us-east4.run.app"; },
    rotationIntervalMs: 3500,
    placeholders: [
        "Ask me anything...", "Pregúntame cualquier cosa...", "اسألني أي شيء...",
        "هر چیزی از من بپرسید...", "له ما څخه هر څه وپوښتئ...", "Pergunte-me qualquer coisa...",
        "मलाई जे पनि सोध्नुहोस्...", "ကျွန်မကို ဘာမဆိုမေးပါ..."
    ],
    rtlIndices: [2, 3, 4],
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
    isListening: false, audio: new Audio(), secretPassphrase: null, dynamicCount: 0, hasRevealedPassport: false
};

const DOM = {
    chat: document.getElementById('chat-container'),
    input: document.getElementById('user-input'),
    sendBtn: document.getElementById('send-btn'),
    micBtn: document.getElementById('mic-btn'),
    header: document.getElementById('app-header')
};

const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = SpeechAPI ? new SpeechAPI() : null;
if (recognition) { recognition.continuous = true; recognition.interimResults = true; }

const MicController = {
    start() {
        if (!recognition) return;
        UI.stopRotation();
        DOM.input.value = '';
        recognition.lang = CONFIG.speechLangs[STATE.lang] || 'en-US';
        recognition.start();
        DOM.micBtn.classList.add('listening');
        STATE.isListening = true;
    },
    stop() {
        if (!STATE.isListening || !recognition) return;
        STATE.isListening = false;
        recognition.stop();
        DOM.micBtn.classList.remove('listening');
    },
    toggle() { STATE.isListening ? this.stop() : this.start(); },
    handleResult(e) {
        if (!STATE.isListening) return;
        let transcript = '';
        for (let i = 0; i < e.results.length; ++i) transcript += e.results[i][0].transcript;
        DOM.input.value = transcript;
        UI.autoResizeInput();
        UI.toggleSendButton();
    },
    handleEnd() { DOM.micBtn.classList.remove('listening'); STATE.isListening = false; }
};

const UI = {
    startRotation() {
        if (STATE.hasEngaged) return;
        STATE.timer = setInterval(() => {
            STATE.placeholderIdx = (STATE.placeholderIdx + 1) % CONFIG.placeholders.length;
            DOM.input.placeholder = CONFIG.placeholders[STATE.placeholderIdx];
            DOM.input.dir = CONFIG.rtlIndices.includes(STATE.placeholderIdx) ? "rtl" : "ltr";
        }, CONFIG.rotationIntervalMs);
    },
    stopRotation() { clearInterval(STATE.timer); DOM.input.placeholder = ""; DOM.input.dir = "ltr"; },
    autoResizeInput() { DOM.input.style.height = 'auto'; DOM.input.style.height = DOM.input.scrollHeight + 'px'; },
    toggleSendButton() {
        const hasText = DOM.input.value.trim().length > 0;
        DOM.sendBtn.classList.toggle('active', hasText);
        DOM.sendBtn.disabled = !hasText;
        DOM.input.dir = hasText ? "auto" : "ltr";
    },
    scrollToBottom() { DOM.chat.scrollTop = DOM.chat.scrollHeight; },
    showTyping() {
        const indicator = document.getElementById('typing-indicator');
        indicator.style.display = 'flex';
        DOM.chat.appendChild(indicator);
        this.scrollToBottom();
    },
    hideTyping() { document.getElementById('typing-indicator').style.display = 'none'; },

    appendUserMessage(text) {
        const row = document.createElement('div');
        row.className = 'message-row user';
        const msg = document.createElement('div');
        msg.className = 'message';
        msg.textContent = text;
        row.appendChild(msg);
        DOM.chat.appendChild(row);
        this.scrollToBottom();
    },

    appendRhondaMessage(text, lang, isGreeting = false) {
        const row = document.createElement('div');
        row.className = 'message-row rhonda';
        const msg = document.createElement('div');
        msg.className = 'message';
        if (isGreeting) msg.id = 'greeting-bubble';

        // NEW: Proper Markdown Bolding and Line Breaks
        let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
        msg.innerHTML = formattedText;

        const actions = document.createElement('div');
        actions.className = 'actions';
        const speakerBtn = document.createElement('div');
        speakerBtn.className = 'action-icon';
        speakerBtn.innerHTML = CONFIG.icons.speaker;

        const cleanText = text.replace(/'/g, "\\'").replace(/"/g, '\\"');
        speakerBtn.onclick = () => API.fetchAudio(cleanText, speakerBtn, lang);

        actions.appendChild(speakerBtn);
        row.appendChild(msg);
        row.appendChild(actions);
        DOM.chat.appendChild(row);
        this.scrollToBottom();
    },

    updateLocalizedUI(translations) {
        const greetingMsg = document.getElementById('greeting-bubble');
        if (greetingMsg && translations.greeting) {
            greetingMsg.innerHTML = translations.greeting.replace(/\n/g, '<br>');
        }

        const labels = translations.button_labels;
        const grid = document.querySelector('.intent-grid');
        if (grid && labels) {
            const btnMap = {
                'SIGNAL_HOUSING': labels.housing,
                'SIGNAL_FOOD': labels.food,
                'SIGNAL_LEGAL': labels.legal,
                'SIGNAL_HEALTH': labels.health,
                'SIGNAL_TRANSIT': labels.transit,
                'SIGNAL_WORK': labels.education
            };
            grid.querySelectorAll('.intent-btn').forEach(btn => {
                const onclickStr = btn.getAttribute('onclick');
                for (const [key, text] of Object.entries(btnMap)) {
                    if (onclickStr.includes(key)) {
                        const labelSpan = btn.querySelector('.intent-label');
                        if (labelSpan) labelSpan.textContent = text;
                    }
                }
            });
        }
    },

    renderIntentGrid(labels) {
        const l = labels || { housing: "Housing", food: "Food", legal: "Legal", health: "Health", transit: "Transit", education: "Education" };
        const oldGrid = document.querySelector('.intent-grid');
        if (oldGrid) oldGrid.closest('.message-row').remove();

        const wrapper = document.createElement('div');
        wrapper.className = `message-row rhonda`;
        wrapper.innerHTML = `
            <div class="intent-grid">
                <button class="intent-btn" onclick="API.sendMessage('SIGNAL_HOUSING')">
                    ${CONFIG.icons.housing} <span class="intent-label">${l.housing}</span>
                </button>
                <button class="intent-btn" onclick="API.sendMessage('SIGNAL_FOOD')">
                    ${CONFIG.icons.food} <span class="intent-label">${l.food}</span>
                </button>
                <button class="intent-btn" onclick="API.sendMessage('SIGNAL_LEGAL')">
                    ${CONFIG.icons.legal} <span class="intent-label">${l.legal}</span>
                </button>
                <button class="intent-btn" onclick="API.sendMessage('SIGNAL_HEALTH')">
                    ${CONFIG.icons.health} <span class="intent-label">${l.health}</span>
                </button>
                <button class="intent-btn" onclick="API.sendMessage('SIGNAL_TRANSIT')">
                    ${CONFIG.icons.transit} <span class="intent-label">${l.transit}</span>
                </button>
                <button class="intent-btn" onclick="API.sendMessage('SIGNAL_WORK')">
                    ${CONFIG.icons.work} <span class="intent-label">${l.education}</span>
                </button>
            </div>`;
        DOM.chat.appendChild(wrapper);
        this.scrollToBottom();
    },

    clearInput() {
        DOM.input.value = '';
        this.autoResizeInput();
        this.toggleSendButton();
    }
};

const API = {
    async fetchAudio(text, btn, lang) {
        btn.classList.add('playing');
        try {
            const res = await fetch(`${CONFIG.backendUrl}/tts`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, lang })
            });
            const data = await res.json();
            if (data.audio_base64) {
                STATE.audio.src = `data:audio/mp3;base64,${data.audio_base64}`;
                STATE.audio.play();
                STATE.audio.onended = () => btn.classList.remove('playing');
            } else { btn.classList.remove('playing'); }
        } catch (e) { btn.classList.remove('playing'); }
    },

    async sendMessage(triggerText = null, isHidden = false) {
        const text = triggerText || DOM.input.value.trim();
        if (!text) return;

        const isSignal = text.startsWith("SIGNAL_");

        if (!isHidden && !isSignal) {
            STATE.hasEngaged = true;
            UI.stopRotation();
            MicController.stop();
            UI.appendUserMessage(text);
            UI.clearInput();
            UI.showTyping();
        } else if (isSignal && text !== "SIGNAL_INIT") {
            UI.showTyping();
        }

        if (!isHidden && !isSignal) {
            STATE.dynamicCount++;
            if (STATE.dynamicCount === 1 && !STATE.hasRevealedPassport && STATE.secretPassphrase) {
                STATE.hasRevealedPassport = true;
                setTimeout(() => {
                    DOM.header.innerHTML = `<span>${STATE.secretPassphrase}</span>`;
                    DOM.header.classList.add("passphrase-mode", "glow");
                }, 1500);
            }
        }

        try {
            const res = await fetch(`${CONFIG.backendUrl}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, session_hash: STATE.sessionHash })
            });
            const data = await res.json();

            if (!isHidden && text !== "SIGNAL_INIT") UI.hideTyping();

            if (res.ok && data.status === 'success') {
                if (data.session_hash) STATE.sessionHash = data.session_hash;
                if (data.language) STATE.lang = data.language;
                if (data.new_passphrase) STATE.secretPassphrase = data.new_passphrase;

                if (data.ui_translations) {
                    UI.updateLocalizedUI(data.ui_translations);
                }

                if (text === "SIGNAL_INIT") {
                    UI.appendRhondaMessage(data.response, STATE.lang, true);
                    UI.renderIntentGrid(data.ui_translations?.button_labels);
                } else {
                    UI.appendRhondaMessage(data.response, STATE.lang);
                }
            }
        } catch (e) {
            if (!isHidden) {
                UI.hideTyping();
                UI.appendRhondaMessage("Connection error. Please try again.", STATE.lang);
            }
        }
    }
};

DOM.input.addEventListener('focus', UI.stopRotation);
DOM.input.addEventListener('blur', () => { if (!DOM.input.value.trim() && !STATE.hasEngaged) UI.startRotation(); });
DOM.input.addEventListener('input', () => { UI.autoResizeInput(); UI.toggleSendButton(); });
DOM.input.addEventListener('keydown', (e) => {
    MicController.stop();
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (!DOM.sendBtn.disabled) API.sendMessage(); }
});
DOM.sendBtn.addEventListener('click', () => API.sendMessage());

if (recognition) {
    DOM.micBtn.addEventListener('click', () => MicController.toggle());
    recognition.addEventListener('result', MicController.handleResult);
    recognition.addEventListener('end', MicController.handleEnd);
    recognition.addEventListener('error', MicController.handleEnd);
}

// NEW: Passport Generation Logic
DOM.header.addEventListener('click', async () => {
    if (!DOM.header.classList.contains('passphrase-mode')) return;
    DOM.header.classList.remove('glow');

    UI.showTyping(); // Triggers the bouncing dots while it loads

    try {
        const res = await fetch(`${CONFIG.backendUrl}/summary`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_hash: STATE.sessionHash, lang: STATE.lang })
        });
        const data = await res.json();

        UI.hideTyping(); // Hides dots when complete

        if (res.ok && data.status === 'success') {

            // Render English only if language is English, else split screen
            let columnsHtml = '';
            if (STATE.lang === 'en' || !data.translated) {
                columnsHtml = `<div style="flex:1;">${data.english}</div>`;
            } else {
                columnsHtml = `
                    <div style="flex:1; border-right:1px solid var(--pi-user-bubble); padding-right:15px;">${data.english}</div>
                    <div style="flex:1;" dir="auto">${data.translated}</div>
                `;
            }

            const cardHtml = `
                <div class="summary-card" style="background:#FFF; border:2px solid var(--pi-send-active); border-radius:16px; padding:20px; margin-top:10px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                    <div style="color:var(--pi-send-active); font-weight:800; margin-bottom:15px; text-transform:uppercase; font-size:13px; letter-spacing: 1px;">Provider Handoff Summary</div>
                    <div style="display:flex; gap:15px; font-size: 15px; line-height: 1.5;">
                        ${columnsHtml}
                    </div>
                </div>`;

            const row = document.createElement('div');
            row.className = 'message-row rhonda';
            row.innerHTML = cardHtml;
            DOM.chat.appendChild(row);
            UI.scrollToBottom();

            // Append the hardcoded explanation message immediately after
            if (data.explanation) {
                setTimeout(() => {
                    UI.appendRhondaMessage(data.explanation, STATE.lang);
                }, 500);
            }
        }
    } catch (err) {
        UI.hideTyping();
        UI.appendRhondaMessage("Failed to generate summary.", STATE.lang);
    }
});

UI.startRotation();
API.sendMessage("SIGNAL_INIT", true);