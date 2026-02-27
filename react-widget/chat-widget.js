/**
 * SUPPORT STARTER AI - CHAT WIDGET
 * =====================================
 * Clean, minimalist embeddable chat widget
 * Compatible with iOS, Android and all modern browsers
 */

(function() {
    'use strict';

    // Widget configuration
    const CONFIG = {
        API_URL: window.CHAT_WIDGET_API_URL || 'http://localhost:8000/chat',
        TENANT_ID: window.CHAT_WIDGET_TENANT_ID || 'default',
        POSITION: window.CHAT_WIDGET_POSITION || 'bottom-right',
        COMPANY_NAME: window.CHAT_WIDGET_COMPANY_NAME || 'Vallhamragruppen',
        WELCOME_MESSAGE: window.CHAT_WIDGET_WELCOME_MESSAGE || 'Hej! Hur kan jag hjälpa dig idag?'
    };

    // CSS styles - Minimalist gray/white design matching Vallhamragruppen.se
    const STYLES = `
        .chat-widget-container * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }

        /* Announcement text above button */
        .chat-widget-announcement {
            position: fixed;
            bottom: 85px;
            right: 20px;
            background: white;
            color: #333;
            padding: 12px 18px;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.15);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            font-weight: 500;
            z-index: 9997;
            opacity: 0;
            animation: fadeInUp 0.5s ease forwards;
            animation-delay: 1.5s;
            max-width: 250px;
            text-align: center;
            line-height: 1.4;
        }

        .chat-widget-announcement.position-bottom-left {
            right: auto;
            left: 20px;
        }

        .chat-widget-announcement::after {
            content: '';
            position: absolute;
            bottom: -6px;
            right: 20px;
            width: 12px;
            height: 12px;
            background: white;
            transform: rotate(45deg);
        }

        .chat-widget-announcement.position-bottom-left::after {
            right: auto;
            left: 20px;
        }

        .chat-widget-announcement.hidden {
            display: none;
        }

        /* Chat toggle button */
        .chat-widget-button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 64px;
            height: 64px;
            background: #2c2c2c;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease;
            z-index: 9998;
            -webkit-transform: translateZ(0);
            transform: translateZ(0);
        }

        .chat-widget-button:hover {
            transform: scale(1.08);
            box-shadow: 0 6px 28px rgba(0,0,0,0.2);
        }

        .chat-widget-button:active {
            transform: scale(0.95);
        }

        /* Chat icon */
        .chat-widget-button svg {
            width: 30px;
            height: 30px;
            fill: white;
            transition: transform 0.3s ease;
        }

        /* Close icon state */
        .chat-widget-button.open svg {
            transform: rotate(90deg);
        }

        .chat-widget-button.position-bottom-left {
            right: auto;
            left: 20px;
        }

        /* Chat window */
        .chat-widget-window {
            position: fixed;
            bottom: 95px;
            right: 20px;
            width: 380px;
            height: 550px;
            max-height: calc(100vh - 115px);
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 50px rgba(0,0,0,0.15);
            display: none;
            flex-direction: column;
            z-index: 9999;
            overflow: hidden;
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.3s ease, transform 0.3s ease;
            -webkit-overflow-scrolling: touch;
        }

        .chat-widget-window.open {
            display: flex;
            opacity: 1;
            transform: translateY(0);
        }

        .chat-widget-window.position-bottom-left {
            right: auto;
            left: 20px;
        }

        /* Header */
        .chat-widget-header {
            background: #2c2c2c;
            color: white;
            padding: 16px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
            -webkit-box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .chat-widget-header .title {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .chat-widget-header .avatar {
            width: 38px;
            height: 38px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            color: #2c2c2c;
            font-size: 13px;
            flex-shrink: 0;
        }

        /* House icon for avatar */
        .chat-widget-header .avatar svg {
            width: 20px;
            height: 20px;
            fill: #2c2c2c;
        }

        .chat-widget-header .info h3 {
            font-size: 16px;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            letter-spacing: -0.3px;
        }

        .chat-widget-header .info p {
            font-size: 12px;
            opacity: 0.8;
            font-weight: 400;
        }

        .chat-widget-header .close-btn {
            background: rgba(255,255,255,0.1);
            border: none;
            color: white;
            cursor: pointer;
            padding: 8px;
            border-radius: 8px;
            transition: background 0.2s;
            -webkit-tap-highlight-color: transparent;
        }

        .chat-widget-header .close-btn:hover {
            background: rgba(255,255,255,0.2);
        }

        .chat-widget-header .close-btn:active {
            background: rgba(255,255,255,0.15);
        }

        /* Messages area */
        .chat-widget-messages {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
            overflow-x: hidden;
            background: #f7f7f7;
            display: flex;
            flex-direction: column;
            gap: 12px;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: thin;
            scrollbar-color: #ddd transparent;
        }

        .chat-widget-messages::-webkit-scrollbar {
            width: 4px;
        }

        .chat-widget-messages::-webkit-scrollbar-track {
            background: transparent;
        }

        .chat-widget-messages::-webkit-scrollbar-thumb {
            background: #ddd;
            border-radius: 2px;
        }

        /* Message bubbles */
        .chat-widget-message {
            display: flex;
            animation: messageIn 0.3s ease;
        }

        .chat-widget-message.user {
            justify-content: flex-end;
        }

        .chat-widget-message.bot {
            justify-content: flex-start;
        }

        .chat-widget-bubble {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.5;
            word-wrap: break-word;
            word-break: break-word;
            -webkit-hyphens: auto;
            hyphens: auto;
        }

        .chat-widget-message.user .chat-widget-bubble {
            background: #2c2c2c;
            color: white;
            border-bottom-right-radius: 6px;
        }

        .chat-widget-message.bot .chat-widget-bubble {
            background: white;
            color: #1a1a1a;
            border-bottom-left-radius: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        /* Welcome screen */
        .chat-widget-welcome {
            text-align: center;
            padding: 24px 20px;
            background: white;
            border-radius: 12px;
            margin: 8px;
        }

        .chat-widget-welcome .icon {
            width: 54px;
            height: 54px;
            background: #2c2c2c;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 14px;
        }

        .chat-widget-welcome .icon svg {
            width: 26px;
            height: 26px;
            fill: white;
        }

        .chat-widget-welcome p {
            color: #333;
            margin-bottom: 16px;
            font-size: 15px;
            line-height: 1.5;
        }

        .chat-widget-welcome .company-name {
            font-weight: 600;
            color: #2c2c2c;
            margin-bottom: 4px;
            font-size: 16px;
        }

        /* Action buttons */
        .chat-widget-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
        }

        .chat-widget-action-btn {
            padding: 9px 16px;
            background: white;
            border: 1.5px solid #e0e0e0;
            border-radius: 20px;
            font-size: 13px;
            color: #2c2c2c;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-weight: 500;
            -webkit-tap-highlight-color: transparent;
        }

        .chat-widget-action-btn:hover {
            background: #2c2c2c;
            color: white;
            border-color: #2c2c2c;
        }

        .chat-widget-action-btn:active {
            transform: scale(0.96);
        }

        /* Input area */
        .chat-widget-input {
            padding: 12px 16px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
            flex-shrink: 0;
        }

        .chat-widget-input input {
            flex: 1;
            padding: 12px 16px;
            border: 1.5px solid #e0e0e0;
            border-radius: 24px;
            outline: none;
            font-size: 14px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f7f7f7;
            transition: border-color 0.2s, background 0.2s;
            -webkit-appearance: none;
            -webkit-border-radius: 24px;
            border-radius: 24px;
        }

        .chat-widget-input input:focus {
            border-color: #2c2c2c;
            background: white;
        }

        .chat-widget-input input::placeholder {
            color: #999;
        }

        .chat-widget-input button {
            width: 44px;
            height: 44px;
            background: #2c2c2c;
            border: none;
            border-radius: 50%;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s, background 0.2s;
            flex-shrink: 0;
            -webkit-tap-highlight-color: transparent;
        }

        .chat-widget-input button:hover {
            background: #1a1a1a;
        }

        .chat-widget-input button:active {
            transform: scale(0.92);
        }

        .chat-widget-input button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .chat-widget-input button svg {
            width: 18px;
            height: 18px;
            fill: none;
            stroke: white;
            stroke-width: 2.5;
            stroke-linecap: round;
            stroke-linejoin: round;
        }

        /* Typing indicator */
        .chat-widget-typing {
            display: flex;
            gap: 5px;
            padding: 12px 16px;
        }

        .chat-widget-typing span {
            width: 8px;
            height: 8px;
            background: #bbb;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }

        .chat-widget-typing span:nth-child(2) { animation-delay: 0.2s; }
        .chat-widget-typing span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
            30% { transform: translateY(-8px); opacity: 1; }
        }

        @keyframes messageIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Mobile responsive - iOS & Android */
        @media (max-width: 480px) {
            .chat-widget-window {
                width: 100%;
                height: 100%;
                max-height: none;
                bottom: 0;
                right: 0;
                left: 0;
                border-radius: 0;
            }

            .chat-widget-button {
                width: 60px;
                height: 60px;
                bottom: 16px;
                right: 16px;
            }

            .chat-widget-button.position-bottom-left {
                right: auto;
                left: 16px;
            }

            .chat-widget-announcement {
                bottom: 80px;
                right: 16px;
                left: 16px;
                max-width: none;
            }

            .chat-widget-announcement.position-bottom-left {
                left: 16px;
            }

            .chat-widget-window {
                border-radius: 16px 16px 0 0;
            }
        }

        /* Safe area for iPhone X+ */
        @supports (padding-bottom: env(safe-area-inset-bottom)) {
            .chat-widget-button {
                bottom: calc(20px + env(safe-area-inset-bottom));
            }

            .chat-widget-window {
                bottom: calc(95px + env(safe-area-inset-bottom));
                max-height: calc(100vh - 115px - env(safe-area-inset-bottom));
            }

            @media (max-width: 480px) {
                .chat-widget-button {
                    bottom: calc(16px + env(safe-area-inset-bottom));
                }

                .chat-widget-window {
                    bottom: env(safe-area-inset-bottom);
                    max-height: calc(100% - env(safe-area-inset-bottom));
                }
            }
        }

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .chat-widget-window {
                background: #1c1c1e;
            }

            .chat-widget-messages {
                background: #000;
            }

            .chat-widget-input {
                background: #1c1c1e;
                border-top-color: #333;
            }

            .chat-widget-input input {
                background: #2c2c2e;
                border-color: #3a3a3c;
                color: white;
            }

            .chat-widget-input input:focus {
                background: #1c1c1e;
                border-color: #666;
            }

            .chat-widget-welcome {
                background: #2c2c2e;
            }

            .chat-widget-welcome p {
                color: #eee;
            }

            .chat-widget-message.bot .chat-widget-bubble {
                background: #2c2c2e;
                color: #eee;
            }

            .chat-widget-action-btn {
                background: #2c2c2e;
                border-color: #3a3a3c;
                color: #eee;
            }

            .chat-widget-action-btn:hover {
                background: #3a3a3c;
            }

            .chat-widget-announcement {
                background: #2c2c2e;
                color: #eee;
            }

            .chat-widget-announcement::after {
                background: #2c2c2e;
            }
        }
    `;

    // Create widget elements
    function createWidget() {
        // Add styles
        const styleEl = document.createElement('style');
        styleEl.textContent = STYLES;
        document.head.appendChild(styleEl);

        // Create announcement
        const announcement = document.createElement('div');
        announcement.className = 'chat-widget-announcement';
        announcement.textContent = '👋 Hej! Behöver du hjälp? Chatta med vår kundtjänst här.';
        if (CONFIG.POSITION === 'bottom-left') {
            announcement.classList.add('position-bottom-left');
        }
        document.body.appendChild(announcement);

        // Create toggle button with chat icon
        const toggleBtn = document.createElement('div');
        toggleBtn.className = 'chat-widget-button';
        if (CONFIG.POSITION === 'bottom-left') {
            toggleBtn.classList.add('position-bottom-left');
        }

        // Chat bubble icon
        toggleBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C12.67 22 13.32 21.92 13.95 21.78C14.36 22.45 15.36 22.86 16.5 22.5C17.64 22.14 18.36 21.14 18.5 20C18.64 18.86 18.14 17.86 17.5 17.36C17.36 16.64 16.64 16 16 16C15.36 16 14.64 16.64 14.5 17.36C14.5 17.36 14.5 17.36 14.5 17.36C14.5 17.36 13.86 18 13 18C12.14 18 11.5 17.36 11.5 16.5C11.5 15.64 12.14 15 13 15C13.86 15 14.5 15.64 14.5 16.5C14.5 16.5 14.5 16.5 14.5 16.5C14.64 17.22 15.36 17.86 16 17.86C16.64 17.86 17.36 17.22 17.5 16.5C17.86 16.5 18.5 15.86 18.5 15C18.5 14.14 17.86 13.5 17 13.5H7C5.9 13.5 5 12.6 5 11.5V5C5 3.9 5.9 3 7 3H17C18.1 3 19 3.9 19 5V11.5C19 12.6 18.1 13.5 17 13.5H16.5V16.5C16.5 17.36 15.86 18 15 18C14.14 18 13.5 17.36 13.5 16.5V13.5H7V5H17V11.5C17.86 11.5 18.5 12.14 18.5 13C18.5 13.86 17.86 14.5 17 14.5C16.14 14.5 15.5 13.86 15.5 13V16C15.5 16.86 14.86 17.5 14 17.5C13.14 17.5 12.5 16.86 12.5 16V13.5H7V5H17V11.5Z"/>
            </svg>
        `;
        document.body.appendChild(toggleBtn);

        // Create chat window
        const chatWindow = document.createElement('div');
        chatWindow.className = 'chat-widget-window';
        if (CONFIG.POSITION === 'bottom-left') {
            chatWindow.classList.add('position-bottom-left');
        }

        chatWindow.innerHTML = `
            <div class="chat-widget-header">
                <div class="title">
                    <div class="avatar">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 3L4 9v12h16V9l-8-6zm0 2.5L18 10v9H6v-9l6-4.5z"/>
                            <rect x="9" y="13" width="6" height="6"/>
                        </svg>
                    </div>
                    <div class="info">
                        <h3>${CONFIG.COMPANY_NAME}</h3>
                        <p>Digital kundtjänst</p>
                    </div>
                </div>
                <button class="close-btn">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            <div class="chat-widget-messages" id="chatWidgetMessages">
                <div class="chat-widget-welcome" id="chatWidgetWelcome">
                    <div class="icon">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 3L4 9v12h16V9l-8-6zm0 2.5L18 10v9H6v-9l6-4.5z"/>
                            <rect x="9" y="13" width="6" height="6"/>
                        </svg>
                    </div>
                    <p class="company-name">${CONFIG.COMPANY_NAME}</p>
                    <p>${CONFIG.WELCOME_MESSAGE}</p>
                    <div class="chat-widget-actions">
                        <button class="chat-widget-action-btn" data-msg="Hur gör jag en felanmälan?">Felanmälan</button>
                        <button class="chat-widget-action-btn" data-msg="Vilka områden verkar ni i?">Områden</button>
                        <button class="chat-widget-action-btn" data-msg="Vad är öppettiderna?">Öppettider</button>
                    </div>
                </div>
            </div>
            <div class="chat-widget-input">
                <input type="text" id="chatWidgetInput" placeholder="Skriv ditt meddelande..." autocomplete="off" autocorrect="off" autocapitalize="sentences">
                <button id="chatWidgetSend" aria-label="Skicka">
                    <svg viewBox="0 0 24 24">
                        <path d="M22 2L11 13M22 2l-7 20-4-9-9 4 20-7z"/>
                    </svg>
                </button>
            </div>
        `;

        document.body.appendChild(chatWindow);

        // Initialize widget functionality
        initWidget(toggleBtn, chatWindow, announcement);

        return { toggleBtn, chatWindow, announcement };
    }

    function initWidget(toggleBtn, chatWindow, announcement) {
        let isOpen = false;
        let sessionId = 'widget_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        let messageHistory = [];

        const messagesContainer = chatWindow.querySelector('#chatWidgetMessages');
        const welcomeMessage = chatWindow.querySelector('#chatWidgetWelcome');
        const inputField = chatWindow.querySelector('#chatWidgetInput');
        const sendBtn = chatWindow.querySelector('#chatWidgetSend');

        // Toggle chat window
        toggleBtn.addEventListener('click', () => {
            isOpen = !isOpen;
            chatWindow.classList.toggle('open', isOpen);
            toggleBtn.classList.toggle('open', isOpen);

            // Hide announcement when chat is opened
            if (isOpen && announcement) {
                announcement.classList.add('hidden');
            }

            if (isOpen) {
                setTimeout(() => inputField.focus(), 100);
            }
        });

        // Close button
        chatWindow.querySelector('.close-btn').addEventListener('click', () => {
            isOpen = false;
            chatWindow.classList.remove('open');
            toggleBtn.classList.remove('open');
        });

        // Send message
        async function sendMessage(text) {
            if (!text || !text.trim()) return;

            // Hide welcome message
            if (welcomeMessage) {
                welcomeMessage.style.display = 'none';
            }

            // Add user message
            addMessage(text.trim(), true);
            messageHistory.push({ role: 'user', content: text.trim() });
            inputField.value = '';

            // Show typing indicator
            showTyping();

            try {
                const response = await fetch(CONFIG.API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: text.trim(),
                        session_id: sessionId,
                        conversation_history: messageHistory,
                        tenant_id: CONFIG.TENANT_ID
                    })
                });

                hideTyping();

                if (response.ok) {
                    const data = await response.json();
                    addMessage(data.reply, false, data.suggested_responses);
                    messageHistory.push({ role: 'assistant', content: data.reply });
                } else {
                    throw new Error('API error');
                }
            } catch (error) {
                hideTyping();
                // Fallback responses
                const fallback = getFallbackResponse(text);
                addMessage(fallback, false);
            }
        }

        function addMessage(text, isUser, suggestedActions = null) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `chat-widget-message ${isUser ? 'user' : 'bot'}`;

            const bubble = document.createElement('div');
            bubble.className = 'chat-widget-bubble';
            bubble.textContent = text;

            msgDiv.appendChild(bubble);
            messagesContainer.appendChild(msgDiv);

            // Add suggested actions if any
            if (suggestedActions && suggestedActions.length > 0) {
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'chat-widget-message bot';
                actionsDiv.style.marginTop = '-4px';

                const actionsContainer = document.createElement('div');
                actionsContainer.style.cssText = 'display: flex; gap: 6px; flex-wrap: wrap;';

                suggestedActions.forEach(action => {
                    const btn = document.createElement('button');
                    btn.className = 'chat-widget-action-btn';
                    btn.textContent = action;
                    btn.style.fontSize = '12px';
                    btn.style.padding = '7px 14px';
                    btn.onclick = () => sendMessage(action);
                    actionsContainer.appendChild(btn);
                });

                actionsDiv.appendChild(actionsContainer);
                messagesContainer.appendChild(actionsDiv);
            }

            // Smooth scroll to bottom
            messagesContainer.scrollTo({
                top: messagesContainer.scrollHeight,
                behavior: 'smooth'
            });
        }

        function showTyping() {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'chat-widget-message bot';
            typingDiv.id = 'chatWidgetTyping';
            typingDiv.innerHTML = `
                <div class="chat-widget-bubble chat-widget-typing">
                    <span></span><span></span><span></span>
                </div>
            `;
            messagesContainer.appendChild(typingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function hideTyping() {
            const typing = document.getElementById('chatWidgetTyping');
            if (typing) typing.remove();
        }

        function getFallbackResponse(msg) {
            const lower = msg.toLowerCase();
            if (lower.includes('fel') || lower.includes('anmäl') || lower.includes('problem')) {
                return 'För felanmälan, kontakta oss på info@vallhamragruppen.se eller ring 0793-006638 under telefontid tis-tors 9-12. Vid akuta ärenden, ring journummer dygnet runt.';
            }
            if (lower.includes('pris') || lower.includes('kostnad') || lower.includes('hyra')) {
                return 'Hyror varierar beroende på fastighetens läge, storlek och standard. Kontakta oss på 0793-006638 för mer information.';
            }
            if (lower.includes('akut')) {
                return 'För akuta ärenden (vattenläckor, strömavbrott), ring journummer 0793-006638 direkt dygnet runt. Vid fara för liv, ring 112.';
            }
            return 'Tack för ditt meddelande! Kontakta oss på 0793-006638 eller info@vallhamragruppen.se så hjälper vi dig.';
        }

        // Event listeners
        sendBtn.addEventListener('click', () => sendMessage(inputField.value));

        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage(inputField.value);
            }
        });

        // Quick action buttons
        chatWindow.querySelectorAll('.chat-widget-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                sendMessage(btn.dataset.msg);
            });
        });

        // Handle escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isOpen) {
                isOpen = false;
                chatWindow.classList.remove('open');
                toggleBtn.classList.remove('open');
            }
        });
    }

    // Initialize widget when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createWidget);
    } else {
        createWidget();
    }

})();
