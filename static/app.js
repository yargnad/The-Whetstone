/**
 * The Whetstone - Web UI JavaScript
 * Handles API communication and UI interactions
 */

// API Base URL
const API_BASE = '';

// State
let currentPersona = null;
let currentModel = null;
let isStreaming = false;
let currentView = 'chat';
let symposiumActive = false;

// DOM Elements - Chat
const personaSelect = document.getElementById('persona-select');
const modelSelect = document.getElementById('model-select');
const deepModeToggle = document.getElementById('deep-mode-toggle');
const clarityModeToggle = document.getElementById('clarity-mode-toggle');
const loggingToggle = document.getElementById('logging-toggle');
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

// DOM Elements - Navigation
const menuBtn = document.getElementById('menu-btn');
const menuDropdown = document.getElementById('menu-dropdown');

// DOM Elements - Symposium
const symposiumPersonaA = document.getElementById('symposium-persona-a');
const symposiumPersonaB = document.getElementById('symposium-persona-b');
const symposiumTopic = document.getElementById('symposium-topic');
const symposiumStartBtn = document.getElementById('symposium-start-btn');
const symposiumNextBtn = document.getElementById('symposium-next-btn');
const symposiumStopBtn = document.getElementById('symposium-stop-btn');
const symposiumMessages = document.getElementById('symposium-messages');
const symposiumTopicText = document.getElementById('symposium-status-text'); // Reused subtitle for topic
const personaGrid = document.getElementById('persona-grid');

// DOM Elements - Persona Manager
const scanModeSelect = document.getElementById('scan-mode-select');
const scanPersonasBtn = document.getElementById('scan-personas-btn');
const personaModal = document.getElementById('persona-modal');
const modalPersonaName = document.getElementById('modal-persona-name');
const personaPreamble = document.getElementById('persona-preamble');
const personaPrompt = document.getElementById('persona-prompt');
const modalCloseBtn = document.getElementById('modal-close-btn');
const modalSelectBtn = document.getElementById('modal-select-btn');
const modalSaveBtn = document.getElementById('modal-save-btn');

// Status elements
const statusBackend = document.getElementById('status-backend');
const statusPersonas = document.getElementById('status-personas');

// =============================================
// Initialization
// =============================================

document.addEventListener('DOMContentLoaded', () => {
    init();
});

async function init() {
    await loadStatus();
    await loadPersonas();
    await loadModels();
    await loadChatHistory();
    populateSymposiumPersonas();
    populatePersonaGrid();
    setupEventListeners();
    setupNavigation();
    setupSymposium();
    setupPersonaManager();
}

// =============================================
// API Functions
// =============================================

async function loadStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();

        statusBackend.textContent = data.backend || '—';
        statusPersonas.textContent = data.persona_count || 0;

        deepModeToggle.checked = data.deep_mode || false;
        clarityModeToggle.checked = data.clarity_mode || false;
        loggingToggle.checked = data.logging_enabled || false;

        if (data.current_persona) {
            currentPersona = data.current_persona;
        }
    } catch (error) {
        console.error('Failed to load status:', error);
        statusBackend.textContent = 'Error';
    }
}

async function loadPersonas() {
    try {
        const response = await fetch(`${API_BASE}/api/personas`);
        const data = await response.json();

        personaSelect.innerHTML = '<option value="">Select a persona...</option>';

        data.personas.forEach(persona => {
            const option = document.createElement('option');
            option.value = persona.name;
            option.textContent = persona.name;
            if (persona.name === data.current) {
                option.selected = true;
                currentPersona = persona.name;
                enableChat();
            }
            personaSelect.appendChild(option);
        });

    } catch (error) {
        console.error('Failed to load personas:', error);
        personaSelect.innerHTML = '<option value="">Failed to load</option>';
    }
}

async function selectPersona(name) {
    if (!name) return;

    try {
        const response = await fetch(`${API_BASE}/api/personas/select`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ persona_name: name })
        });

        const data = await response.json();
        if (data.success) {
            currentPersona = name;
            enableChat();
            clearWelcomeMessage();
        }
    } catch (error) {
        console.error('Failed to select persona:', error);
    }
}

async function toggleDeepMode(enabled) {
    try {
        await fetch(`${API_BASE}/api/settings/deep-mode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled })
        });
    } catch (error) {
        console.error('Failed to toggle deep mode:', error);
    }
}

async function toggleLogging(enabled) {
    try {
        await fetch(`${API_BASE}/api/settings/logging`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled })
        });
    } catch (error) {
        console.error('Failed to toggle logging:', error);
    }
}

async function toggleClarityMode(enabled) {
    try {
        await fetch(`${API_BASE}/api/settings/clarity-mode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled })
        });
    } catch (error) {
        console.error('Failed to toggle clarity mode:', error);
    }
}

async function loadModels() {
    try {
        const response = await fetch(`${API_BASE}/api/models`);
        const data = await response.json();

        modelSelect.innerHTML = '<option value="">Select a model...</option>';

        if (data.models && data.models.length > 0) {
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                if (model === data.current) {
                    option.selected = true;
                    currentModel = model;
                }
                modelSelect.appendChild(option);
            });
        } else {
            modelSelect.innerHTML = '<option value="">No models found</option>';
        }
    } catch (error) {
        console.error('Failed to load models:', error);
        modelSelect.innerHTML = '<option value="">Failed to load</option>';
    }
}

async function selectModel(name) {
    if (!name) return;

    try {
        modelSelect.disabled = true;
        modelSelect.style.opacity = '0.5';

        const response = await fetch(`${API_BASE}/api/models/select`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model_name: name })
        });

        const data = await response.json();
        if (data.success) {
            currentModel = name;
            statusBackend.textContent = `Ollama (${name})`;
        } else {
            alert('Failed to switch model: ' + (data.detail || 'Unknown error'));
            // Revert selection
            await loadModels();
        }
    } catch (error) {
        console.error('Failed to select model:', error);
        alert('Failed to switch model');
    } finally {
        modelSelect.disabled = false;
        modelSelect.style.opacity = '1';
    }
}

async function loadChatHistory() {
    try {
        const response = await fetch(`${API_BASE}/api/history?limit=20`);
        const data = await response.json();

        if (data.history && data.history.length > 0) {
            // Clear welcome message
            clearWelcomeMessage();

            // Display history (oldest first, so reverse)
            const historyReversed = [...data.history].reverse();

            for (const entry of historyReversed) {
                // Add user message
                addMessage('You', entry.user_query, true);

                // Add AI message
                const personaName = entry.persona_name || 'AI';
                addMessage(personaName, entry.ai_response, false);

                // Set current persona if not already set
                if (!currentPersona && entry.persona_name) {
                    currentPersona = entry.persona_name;
                    personaSelect.value = entry.persona_name;
                    enableChat();
                }
            }

            scrollToBottom();
        }
    } catch (error) {
        console.error('Failed to load chat history:', error);
    }
}

// =============================================
// Chat Functions
// =============================================

async function sendMessage(message) {
    if (!message.trim() || !currentPersona || isStreaming) return;

    // Add user message
    addMessage('You', message, true);
    chatInput.value = '';
    autoResizeTextarea();

    // Create AI message placeholder
    const aiMessage = addMessage(currentPersona, '', false, true);
    const bubble = aiMessage.querySelector('.message-bubble');

    isStreaming = true;
    disableInput();

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Normalize line endings (handle \r\n from Windows)
            buffer = buffer.replace(/\r\n/g, '\n');

            // Process complete SSE messages (end with double newline)
            let doubleNewline;
            while ((doubleNewline = buffer.indexOf('\n\n')) !== -1) {
                const message = buffer.substring(0, doubleNewline);
                buffer = buffer.substring(doubleNewline + 2);

                // Parse the SSE message
                let eventType = '';
                let eventData = '';

                for (const line of message.split('\n')) {
                    if (line.startsWith('event:')) {
                        eventType = line.substring(6).trim();
                    } else if (line.startsWith('data:')) {
                        // Keep the space after 'data:' but don't trim - preserve whitespace in tokens
                        const dataContent = line.substring(5);
                        // Only remove the single leading space that SSE format adds
                        eventData = dataContent.startsWith(' ') ? dataContent.substring(1) : dataContent;
                    }
                }

                // Handle based on event type
                if (eventType === 'done' || eventData === '[DONE]') {
                    const cursor = bubble.querySelector('.streaming-cursor');
                    if (cursor) cursor.remove();
                } else if (eventData !== '' && eventData !== '[DONE]') {
                    // Decode escaped newlines from SSE
                    const decodedData = eventData.replace(/\\n/g, '\n');
                    fullText += decodedData;
                    bubble.innerHTML = formatMessage(fullText) + '<span class="streaming-cursor"></span>';
                    scrollToBottom();
                }
            }
        }

        // Final update without cursor
        bubble.innerHTML = formatMessage(fullText);

    } catch (error) {
        console.error('Chat error:', error);
        bubble.innerHTML = '<em style="color: #ef4444;">Error: Failed to get response</em>';
    } finally {
        isStreaming = false;
        enableInput();
        scrollToBottom();
    }
}

function addMessage(sender, text, isUser = false, isStreaming = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'ai'}`;

    const avatar = isUser ? '👤' : '🏛️';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-sender">${sender}</div>
            <div class="message-bubble">
                ${isStreaming ? '<span class="streaming-cursor"></span>' : formatMessage(text)}
            </div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv;
}

function formatMessage(text) {
    if (!text) return '';

    // Escape HTML first to prevent XSS
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Code blocks (```)
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
    });

    // Inline code (`)
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Headers (# ## ###)
    html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');

    // Bold (**text**)
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Italic (*text* or _text_)
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/_([^_]+)_/g, '<em>$1</em>');

    // Bullet lists (- or *)
    html = html.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Numbered lists (1. 2. etc)
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

    // Blockquotes (>)
    html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

    // Horizontal rule (---)
    html = html.replace(/^---$/gm, '<hr>');

    // Paragraphs - split by double newlines
    const blocks = html.split(/\n\n+/);
    html = blocks.map(block => {
        block = block.trim();
        if (!block) return '';
        // Don't wrap already-wrapped elements
        if (block.startsWith('<h') || block.startsWith('<ul') ||
            block.startsWith('<ol') || block.startsWith('<pre') ||
            block.startsWith('<blockquote') || block.startsWith('<hr')) {
            return block;
        }
        // Convert single newlines to <br> within paragraphs
        block = block.replace(/\n/g, '<br>');
        return `<p>${block}</p>`;
    }).join('\n');

    return html;
}

// =============================================
// UI Helpers
// =============================================

function enableChat() {
    chatInput.disabled = false;
    sendBtn.disabled = false;
    chatInput.placeholder = `Ask ${currentPersona} a question...`;
}

function disableInput() {
    chatInput.disabled = true;
    sendBtn.disabled = true;
}

function enableInput() {
    chatInput.disabled = false;
    sendBtn.disabled = false;
    chatInput.focus();
}

function clearWelcomeMessage() {
    const welcome = chatMessages.querySelector('.welcome-message');
    if (welcome) {
        welcome.remove();
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function autoResizeTextarea() {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 200) + 'px';
}

// =============================================
// Event Listeners
// =============================================

function setupEventListeners() {
    // Persona selection
    personaSelect.addEventListener('change', (e) => {
        selectPersona(e.target.value);
    });

    // Settings toggles
    deepModeToggle.addEventListener('change', (e) => {
        toggleDeepMode(e.target.checked);
    });

    loggingToggle.addEventListener('change', (e) => {
        toggleLogging(e.target.checked);
    });

    clarityModeToggle.addEventListener('change', (e) => {
        toggleClarityMode(e.target.checked);
    });

    // Model selection
    modelSelect.addEventListener('change', (e) => {
        selectModel(e.target.value);
    });

    // Chat form submission
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        sendMessage(chatInput.value);
    });

    // Auto-resize textarea
    chatInput.addEventListener('input', autoResizeTextarea);

    // Enter to send (Shift+Enter for newline)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(chatInput.value);
        }
    });
}

// =============================================
// Navigation
// =============================================

function setupNavigation() {
    // Toggle hamburger menu
    menuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        menuDropdown.classList.toggle('open');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!menuDropdown.contains(e.target) && e.target !== menuBtn) {
            menuDropdown.classList.remove('open');
        }
    });

    // Menu item clicks
    menuDropdown.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', () => {
            switchView(item.dataset.view);
            menuDropdown.classList.remove('open');
        });
    });
}

function switchView(viewName) {
    currentView = viewName;

    // Update view containers
    document.querySelectorAll('.view-container').forEach(view => {
        view.classList.toggle('active', view.id === `view-${viewName}`);
    });

    // Toggle sidebar content
    const chatControls = document.getElementById('sidebar-content-chat');
    const symposiumControls = document.getElementById('sidebar-content-symposium');

    if (viewName === 'symposium') {
        if (chatControls) chatControls.style.display = 'none';
        if (symposiumControls) symposiumControls.style.display = 'block';
    } else {
        if (chatControls) chatControls.style.display = 'block';
        if (symposiumControls) symposiumControls.style.display = 'none';
    }
}

// =============================================
// Symposium
// =============================================

function populateSymposiumPersonas() {
    // Get personas from the main dropdown
    const options = personaSelect.querySelectorAll('option');

    symposiumPersonaA.innerHTML = '<option value="">Select...</option>';
    symposiumPersonaB.innerHTML = '<option value="">Select...</option>';

    options.forEach(opt => {
        if (opt.value) {
            symposiumPersonaA.innerHTML += `<option value="${opt.value}">${opt.textContent}</option>`;
            symposiumPersonaB.innerHTML += `<option value="${opt.value}">${opt.textContent}</option>`;
        }
    });
}

const symposiumForm = document.getElementById('symposium-form');
const symposiumInput = document.getElementById('symposium-input');

function setupSymposium() {
    symposiumStartBtn.addEventListener('click', startSymposium);
    symposiumNextBtn.addEventListener('click', nextSymposiumTurn);
    symposiumStopBtn.addEventListener('click', stopSymposium);

    // Helper for sending interjections
    const sendInterjection = async (target = null) => {
        const message = symposiumInput.value.trim();
        if (!message) return;

        // Add to UI immediately
        const bubble = createSymposiumBubble('Moderator', 'center');
        bubble.querySelector('.bubble-text').textContent = message;
        symposiumMessages.appendChild(bubble);
        symposiumMessages.scrollTop = symposiumMessages.scrollHeight;

        // Clear input
        symposiumInput.value = '';

        try {
            await fetch(`${API_BASE}/api/symposium/interject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, target })
            });
            // The next turn will handle the response to this interjection
        } catch (error) {
            console.error('Failed to interject:', error);
            bubble.querySelector('.bubble-text').style.color = 'red';
        }
    };

    // Handle targeting buttons
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const target = btn.dataset.target || null; // 'a', 'b', or null (for 'Ask Both')
            sendInterjection(target);
        });
    });

    // Enter to submit (defaults to "Ask Both" / Active form submission)
    symposiumForm.addEventListener('submit', (e) => {
        e.preventDefault();
        sendInterjection(null);
    });

    symposiumInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendInterjection(null);
        }
    });
}

async function startSymposium() {
    const personaA = symposiumPersonaA.value;
    const personaB = symposiumPersonaB.value;
    const topic = symposiumTopic.value.trim();

    if (!personaA || !personaB) {
        alert('Please select both philosophers');
        return;
    }

    if (!topic) {
        alert('Please enter a topic for debate');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/symposium/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                persona_a: personaA,
                persona_b: personaB,
                topic: topic
            })
        });

        const data = await response.json();

        if (data.success) {
            symposiumActive = true;
            statusBackend.textContent = 'Symposium Active'; // Update status
            if (symposiumTopicText) symposiumTopicText.textContent = `Topic: ${topic}`;
            symposiumMessages.innerHTML = '';

            // Show Arena Controls
            const controls = document.getElementById('symposium-active-controls');
            if (controls) controls.style.display = 'flex';
            if (symposiumForm) symposiumForm.style.display = 'flex';

            // Auto-trigger first turn
            nextSymposiumTurn();
        }
    } catch (error) {
        console.error('Failed to start symposium:', error);
        alert('Failed to start symposium');
    }
}

async function nextSymposiumTurn() {
    if (!symposiumActive) return;

    symposiumNextBtn.disabled = true;
    symposiumNextBtn.textContent = 'Thinking...';

    try {
        const response = await fetch(`${API_BASE}/api/symposium/next`);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let buffer = '';
        let currentSpeaker = '';
        let fullText = '';
        let bubble = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            buffer = buffer.replace(/\r\n/g, '\n');

            let doubleNewline;
            while ((doubleNewline = buffer.indexOf('\n\n')) !== -1) {
                const message = buffer.substring(0, doubleNewline);
                buffer = buffer.substring(doubleNewline + 2);

                let eventType = '';
                let eventData = '';

                for (const line of message.split('\n')) {
                    if (line.startsWith('event:')) {
                        eventType = line.substring(6).trim();
                    } else if (line.startsWith('data:')) {
                        const dataContent = line.substring(5);
                        eventData = dataContent.startsWith(' ') ? dataContent.substring(1) : dataContent;
                    } else if (line.startsWith('id:')) {
                        // Extract speaker from turn info if needed
                    }
                }

                if (eventType === 'token' && eventData) {
                    const decodedData = eventData.replace(/\\n/g, '\n');
                    fullText += decodedData;

                    if (!bubble) {
                        // Create bubble - determine side based on turn count
                        const turnCount = symposiumMessages.children.length;
                        const side = turnCount % 2 === 0 ? 'left' : 'right';
                        bubble = createSymposiumBubble('', side);
                        symposiumMessages.appendChild(bubble);
                    }

                    bubble.querySelector('.bubble-text').innerHTML = formatMessage(fullText);
                    symposiumMessages.scrollTop = symposiumMessages.scrollHeight;

                } else if (eventType === 'complete' && eventData) {
                    currentSpeaker = eventData;
                    if (bubble) {
                        bubble.querySelector('.speaker').textContent = currentSpeaker;
                    }
                } else if (eventType === 'done') {
                    // Turn complete
                }
            }
        }

    } catch (error) {
        console.error('Symposium turn error:', error);
    } finally {
        symposiumNextBtn.disabled = false;
        symposiumNextBtn.textContent = 'Next Turn';
    }
}

function createSymposiumBubble(speaker, side) {
    const bubble = document.createElement('div');
    bubble.className = `symposium-bubble ${side}`;
    bubble.innerHTML = `
        <div class="speaker">${speaker}</div>
        <div class="bubble-content">
            <div class="bubble-text"></div>
        </div>
    `;
    return bubble;
}

async function stopSymposium() {
    try {
        await fetch(`${API_BASE}/api/symposium/stop`, { method: 'POST' });
    } catch (error) {
        console.error('Failed to stop symposium:', error);
    }

    symposiumActive = false;
    statusBackend.textContent = 'Symposium Ended';
}

// =============================================
// Persona Grid & Manager
// =============================================

let currentEditingPersona = null;

function populatePersonaGrid() {
    personaGrid.innerHTML = '';

    const options = personaSelect.querySelectorAll('option');
    options.forEach(opt => {
        if (opt.value) {
            const card = document.createElement('div');
            card.className = 'persona-card';
            card.innerHTML = `
                <h3>${opt.textContent}</h3>
                <p>Click to select or configure this persona.</p>
                <div class="persona-card-actions">
                    <button class="select-btn" data-persona="${opt.value}">Select</button>
                    <button class="config-btn" data-persona="${opt.value}">⚙️ Configure</button>
                </div>
            `;
            personaGrid.appendChild(card);
        }
    });

    // Add event listeners to buttons
    personaGrid.querySelectorAll('.select-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            selectPersona(btn.dataset.persona);
            personaSelect.value = btn.dataset.persona;
            switchView('chat');
        });
    });

    personaGrid.querySelectorAll('.config-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            openPersonaModal(btn.dataset.persona);
        });
    });
}

function setupPersonaManager() {
    // Scan for personas
    if (scanPersonasBtn) {
        scanPersonasBtn.addEventListener('click', scanForPersonas);
    }

    // Modal close
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closePersonaModal);
    }

    // Modal select button
    if (modalSelectBtn) {
        modalSelectBtn.addEventListener('click', () => {
            if (currentEditingPersona) {
                selectPersona(currentEditingPersona);
                personaSelect.value = currentEditingPersona;
                closePersonaModal();
                switchView('chat');
            }
        });
    }

    // Modal save button
    if (modalSaveBtn) {
        modalSaveBtn.addEventListener('click', savePersonaPreamble);
    }

    // Close modal on outside click
    if (personaModal) {
        personaModal.addEventListener('click', (e) => {
            if (e.target === personaModal) {
                closePersonaModal();
            }
        });
    }
}

async function scanForPersonas() {
    const mode = scanModeSelect ? scanModeSelect.value : 'shallow';
    const btn = scanPersonasBtn;

    btn.disabled = true;
    btn.textContent = '🔄 Scanning...';

    try {
        const response = await fetch(`${API_BASE}/api/personas/scan?deep=${mode === 'deep'}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            alert(`Scan complete! Found ${data.persona_count} personas (${data.mode} mode).`);
            // Refresh personas
            await loadPersonas();
            populateSymposiumPersonas();
            populatePersonaGrid();
            await loadStatus();
        } else {
            alert('Scan failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Scan failed:', error);
        alert('Scan failed: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '🔄 Scan for Personas';
    }
}

async function openPersonaModal(personaName) {
    currentEditingPersona = personaName;

    try {
        const response = await fetch(`${API_BASE}/api/personas/${encodeURIComponent(personaName)}`);
        const persona = await response.json();

        modalPersonaName.textContent = persona.name;
        personaPrompt.value = persona.prompt || '(No prompt available)';
        personaPreamble.value = persona.custom_preamble || '';

        personaModal.style.display = 'flex';
    } catch (error) {
        console.error('Failed to load persona:', error);
        alert('Failed to load persona details');
    }
}

function closePersonaModal() {
    personaModal.style.display = 'none';
    currentEditingPersona = null;
}

async function savePersonaPreamble() {
    if (!currentEditingPersona || !personaPreamble) return;

    const preamble = personaPreamble.value.trim();
    const btn = modalSaveBtn;

    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
        const response = await fetch(`${API_BASE}/api/personas/${encodeURIComponent(currentEditingPersona)}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ preamble })
        });

        const data = await response.json();
        if (data.success) {
            alert('Preamble saved successfully!');
        } else {
            alert('Failed to save: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Save failed:', error);
        alert('Failed to save preamble: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Save Changes';
    }
}
