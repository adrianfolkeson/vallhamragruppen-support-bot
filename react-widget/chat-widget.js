/**
 * SUPPORT STARTER AI - REACT CHAT WIDGET
 * =====================================
 * Embeddable React component for the chat bot
 * Can be embedded on any website with a simple script tag
 */

(function() {
    'use strict';

    // Widget configuration
    const CONFIG = {
        API_URL: window.CHAT_WIDGET_API_URL || 'http://localhost:8001/chat',
        TENANT_ID: window.CHAT_WIDGET_TENANT_ID || null,
        POSITION: window.CHAT_WIDGET_POSITION || 'bottom-right', // bottom-right, bottom-left
        PRIMARY_COLOR: window.CHAT_WIDGET_PRIMARY_COLOR || '#667eea',
        COMPANY_NAME: window.CHAT_WIDGET_COMPANY_NAME || 'Vallhamragruppen',
        WELCOME_MESSAGE: window.CHAT_WIDGET_WELCOME_MESSAGE || 'Hej! 👋 Hur kan jag hjälpa dig idag?'
    };

    // CSS styles
    const STYLES = `
        .chat-widget-container * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .chat-widget-button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, ${CONFIG.PRIMARY_COLOR} 0%, #764ba2 100%);
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s, box-shadow 0.2s;
            z-index: 9998;
        }

        .chat-widget-button:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 25px rgba(0,0,0,0.25);
        }

        .chat-widget-button svg {
            width: 28px;
            height: 28px;
            fill: white;
        }

        .chat-widget-window {
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 380px;
            height: 600px;
            max-height: calc(100vh - 120px);
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            display: none;
            flex-direction: column;
            z-index: 9999;
            overflow: hidden;
            animation: slideUp 0.3s ease;
        }

        .chat-widget-window.open {
            display: flex;
        }

        .chat-widget-window.position-bottom-left {
            right: auto;
            left: 20px;
        }

        .chat-widget-header {
            background: linear-gradient(135deg, ${CONFIG.PRIMARY_COLOR} 0%, #764ba2 100%);
            color: white;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
        }

        .chat-widget-header .title {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .chat-widget-header .avatar {
            width: 36px;
            height: 36px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: ${CONFIG.PRIMARY_COLOR};
            font-size: 0.9rem;
        }

        .chat-widget-header .info h3 {
            font-size: 1rem;
            font-weight: 600;
        }

        .chat-widget-header .info p {
            font-size: 0.75rem;
            opacity: 0.9;
        }

        .chat-widget-header .close-btn {
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 4px;
            opacity: 0.8;
            transition: opacity 0.2s;
        }

        .chat-widget-header .close-btn:hover {
            opacity: 1;
        }

        .chat-widget-messages {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
            background: #f8f9fa;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

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
            border-radius: 16px;
            font-size: 0.9rem;
            line-height: 1.4;
        }

        .chat-widget-message.user .chat-widget-bubble {
            background: linear-gradient(135deg, ${CONFIG.PRIMARY_COLOR} 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }

        .chat-widget-message.bot .chat-widget-bubble {
            background: white;
            color: #1a1a2e;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }

        .chat-widget-welcome {
            text-align: center;
            padding: 20px;
        }

        .chat-widget-welcome .icon {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, ${CONFIG.PRIMARY_COLOR} 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 12px;
            font-weight: bold;
            color: white;
        }

        .chat-widget-welcome p {
            color: #333;
            margin-bottom: 12px;
        }

        .chat-widget-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            justify-content: center;
        }

        .chat-widget-action-btn {
            padding: 6px 12px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 16px;
            font-size: 0.8rem;
            color: ${CONFIG.PRIMARY_COLOR};
            cursor: pointer;
            transition: all 0.2s;
        }

        .chat-widget-action-btn:hover {
            background: ${CONFIG.PRIMARY_COLOR};
            color: white;
            border-color: ${CONFIG.PRIMARY_COLOR};
        }

        .chat-widget-input {
            padding: 12px 16px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
            flex-shrink: 0;
        }

        .chat-widget-input input {
            flex: 1;
            padding: 10px 14px;
            border: 1px solid #e0e0e0;
            border-radius: 20px;
            outline: none;
            font-size: 0.9rem;
        }

        .chat-widget-input input:focus {
            border-color: ${CONFIG.PRIMARY_COLOR};
        }

        .chat-widget-input button {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, ${CONFIG.PRIMARY_COLOR} 0%, #764ba2 100%);
            border: none;
            border-radius: 50%;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s;
        }

        .chat-widget-input button:hover {
            transform: scale(1.05);
        }

        .chat-widget-input button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .chat-widget-typing {
            display: flex;
            gap: 4px;
            padding: 12px 16px;
        }

        .chat-widget-typing span {
            width: 8px;
            height: 8px;
            background: #ccc;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }

        .chat-widget-typing span:nth-child(2) { animation-delay: 0.2s; }
        .chat-widget-typing span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }

        @keyframes messageIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Mobile responsive */
        @media (max-width: 480px) {
            .chat-widget-window {
                width: calc(100vw - 40px);
                height: calc(100vh - 120px);
                bottom: 80px;
                right: 20px;
                left: 20px;
            }
        }
    `;

    // Create widget elements
    function createWidget() {
        // Add styles
        const styleEl = document.createElement('style');
        styleEl.textContent = STYLES;
        document.head.appendChild(styleEl);

        // Create toggle button
        const toggleBtn = document.createElement('div');
        toggleBtn.className = 'chat-widget-button';
        toggleBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 2v3H4V4h16v3zm0 5v4H4V9h16zm0 6v6H4v-6h16z"/>
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
                    <div class="avatar">${CONFIG.COMPANY_NAME.substring(0, 2).toUpperCase()}</div>
                    <div class="info">
                        <h3>${CONFIG.COMPANY_NAME}</h3>
                        <p>Digital assistent</p>
                    </div>
                </div>
                <button class="close-btn">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            <div class="chat-widget-messages" id="chatWidgetMessages">
                <div class="chat-widget-welcome" id="chatWidgetWelcome">
                    <div class="icon">${CONFIG.COMPANY_NAME.substring(0, 2).toUpperCase()}</div>
                    <p>${CONFIG.WELCOME_MESSAGE}</p>
                    <div class="chat-widget-actions">
                        <button class="chat-widget-action-btn" data-msg="Hur gör jag en felanmälan?">Felanmälan</button>
                        <button class="chat-widget-action-btn" data-msg="Vilka områden verkar ni i?">Områden</button>
                        <button class="chat-widget-action-btn" data-msg="Vad kostar er förvaltning?">Priser</button>
                    </div>
                </div>
            </div>
            <div class="chat-widget-input">
                <input type="text" id="chatWidgetInput" placeholder="Skriv ditt meddelande..." autocomplete="off">
                <button id="chatWidgetSend">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 2L11 13M22 2l-7 20-4-9-9 4 20-7z"/>
                    </svg>
                </button>
            </div>
        `;

        document.body.appendChild(chatWindow);

        // Initialize widget functionality
        initWidget(toggleBtn, chatWindow);

        return { toggleBtn, chatWindow };
    }

    function initWidget(toggleBtn, chatWindow) {
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
            if (isOpen) {
                inputField.focus();
            }
        });

        // Close button
        chatWindow.querySelector('.close-btn').addEventListener('click', () => {
            isOpen = false;
            chatWindow.classList.remove('open');
        });

        // Send message
        async function sendMessage(text) {
            if (!text) return;

            // Hide welcome message
            if (welcomeMessage) {
                welcomeMessage.style.display = 'none';
            }

            // Add user message
            addMessage(text, true);
            messageHistory.push({ role: 'user', content: text });
            inputField.value = '';

            // Show typing indicator
            showTyping();

            try {
                const response = await fetch(CONFIG.API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: text,
                        session_id: sessionId,
                        conversation_history: messageHistory
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
                actionsDiv.style.cssText = 'display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;';

                suggestedActions.forEach(action => {
                    const btn = document.createElement('button');
                    btn.className = 'chat-widget-action-btn';
                    btn.textContent = action;
                    btn.style.fontSize = '0.75rem';
                    btn.style.padding = '4px 10px';
                    btn.onclick = () => sendMessage(action);
                    actionsDiv.appendChild(btn);
                });

                messagesContainer.appendChild(actionsDiv);
            }

            messagesContainer.scrollTop = messagesContainer.scrollHeight;
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
            if (lower.includes('fel') || lower.includes('anmäl')) {
                return 'För felanmälan, ring oss på 0793-006638 eller använd formuläret på vår hemsida.';
            }
            if (lower.includes('pris') || lower.includes('kostnad')) {
                return 'Priser varierar beroende på fastighet. Ring 0793-006638 för offert.';
            }
            return 'Tack för ditt meddelande! Vi hjälper dig gärna. Ring 0793-006638 för snabbast svar.';
        }

        // Event listeners
        sendBtn.addEventListener('click', () => sendMessage(inputField.value));
        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage(inputField.value);
        });

        // Quick action buttons
        chatWindow.querySelectorAll('.chat-widget-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                sendMessage(btn.dataset.msg);
            });
        });
    }

    // Initialize widget when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createWidget);
    } else {
        createWidget();
    }

})();
