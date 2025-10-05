// Financial Advisor Chat Functions

const chatMessages = [];

// Send chat message
async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();

    if (!question) {
        alert('Please enter a question');
        return;
    }

    // Add user message to chat
    addChatMessage('user', question);

    // Clear input
    input.value = '';

    // Show loading
    const loadingId = addChatMessage('loading', 'Thinking');

    try {
        const response = await fetch(API_BASE + '/documents/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });

        // Remove loading message
        removeMessage(loadingId);

        if (response.ok) {
            const data = await response.json();

            // Build message with strategy info and sources
            let message = data.answer;

            // Add sources if available
            if (data.sources && data.sources.length > 0) {
                message += '\n\n📚 Sources: ' + data.sources.slice(0, 3).join(', ');
                if (data.sources.length > 3) {
                    message += ` (+${data.sources.length - 3} more)`;
                }
            }

            // Add strategy indicator (for debugging/transparency)
            const strategyIcon = data.strategy === 'web' ? '🌐' :
                                data.strategy === 'vector' ? '📄' : '🤖';

            addChatMessage('ai', message, strategyIcon + ' ' + (data.strategy || 'llm').toUpperCase());
        } else if (response.status === 503) {
            addChatMessage('error', 'AI advisor is not available. Please ensure the LLM server is running.');
        } else {
            const data = await response.json();
            addChatMessage('error', 'Error: ' + (data.detail || 'Failed to get response'));
        }
    } catch (error) {
        removeMessage(loadingId);
        addChatMessage('error', 'Error: ' + error.message);
    }
}

// Add message to chat
function addChatMessage(type, content, strategyLabel) {
    const container = document.getElementById('chatMessages');
    const messageId = 'msg-' + Date.now();

    let html = '';

    if (type === 'user') {
        html = '<div class="chat-message chat-message-user" id="' + messageId + '">';
        html += '<div class="chat-message-header">You</div>';
        html += '<div class="chat-message-content">' + escapeHtml(content) + '</div>';
        html += '</div>';
        chatMessages.push({ type: 'user', content: content });
    } else if (type === 'ai') {
        html = '<div class="chat-message chat-message-ai" id="' + messageId + '">';
        const header = strategyLabel ? '💼 Financial Advisor • ' + strategyLabel : '💼 Financial Advisor';
        html += '<div class="chat-message-header">' + header + '</div>';
        html += '<div class="chat-message-content">' + escapeHtml(content).replace(/\n/g, '<br>') + '</div>';
        html += '</div>';
        chatMessages.push({ type: 'ai', content: content });
    } else if (type === 'error') {
        html = '<div class="chat-message chat-message-error" id="' + messageId + '">';
        html += '<div class="chat-message-header">⚠️ Error</div>';
        html += '<div class="chat-message-content">' + escapeHtml(content) + '</div>';
        html += '</div>';
    } else if (type === 'loading') {
        html = '<div class="chat-message chat-message-ai" id="' + messageId + '">';
        html += '<div class="chat-loading">AI is thinking</div>';
        html += '</div>';
    }

    container.innerHTML += html;

    // Scroll to bottom
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.scrollTop = chatContainer.scrollHeight;

    return messageId;
}

// Remove a message
function removeMessage(messageId) {
    const el = document.getElementById(messageId);
    if (el) {
        el.remove();
    }
}

// Clear chat
function clearChat() {
    if (!confirm('Clear all chat messages?')) {
        return;
    }

    document.getElementById('chatMessages').innerHTML = '';
    chatMessages.length = 0;
}

// Ask a predefined question (from examples)
function askQuestion(question) {
    document.getElementById('chatInput').value = question;
    sendChatMessage();
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Enter key to send
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }
});
