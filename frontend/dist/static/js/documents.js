// documents.js - Enhanced Document RAG System with intelligent routing

// API_BASE is defined in app.js

// State tracking
let queryCount = 0;
let lastStrategy = 'None';

// Confirm script loaded
console.log('📄 Enhanced documents.js loaded successfully');

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 Initializing Document RAG System');

    // Load initial stats
    updateVectorStoreStats();
    loadDocuments();

    // Set up Enter key to send
    const input = document.getElementById('docChatInput');
    if (input) {
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendDocQuestion();
            }
        });
    }

    // Auto-refresh stats when tab is activated
    const documentsTab = document.querySelector('[data-tab="documents"]');
    if (documentsTab) {
        documentsTab.addEventListener('click', function() {
            updateVectorStoreStats();
            loadDocuments();
        });
    }
});

// Update vector store statistics
async function updateVectorStoreStats() {
    try {
        const response = await fetch(API_BASE + '/documents');
        const data = await response.json();

        document.getElementById('vectorDocCount').textContent = data.count || 0;
        document.getElementById('lastStrategy').textContent = lastStrategy;
        document.getElementById('queryCount').textContent = queryCount;
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Upload document
async function uploadDocument() {
    const fileInput = document.getElementById('docFile');
    const category = document.getElementById('docCategory').value;
    const statusDiv = document.getElementById('uploadStatus');

    if (!fileInput.files || !fileInput.files[0]) {
        alert('Please select a file to upload');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);

    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '⏳ Uploading and vectorizing document...';
    statusDiv.className = 'status-message info';

    try {
        const response = await fetch(API_BASE + '/documents/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            statusDiv.innerHTML = `✅ Document uploaded and vectorized!<br>
                📄 <strong>${data.filename}</strong><br>
                📊 Pages: ${data.page_count} | Chunks: ${data.chunks || 'N/A'}<br>
                🔍 Status: Ready for semantic search`;
            statusDiv.className = 'status-message success';

            // Clear file input
            fileInput.value = '';

            // Update stats and document list
            setTimeout(() => {
                updateVectorStoreStats();
                loadDocuments();
            }, 1000);
        } else {
            throw new Error(data.message || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        statusDiv.innerHTML = '❌ Error: ' + error.message;
        statusDiv.className = 'status-message error';
    }
}

// Send document question with intelligent routing
async function sendDocQuestion() {
    const input = document.getElementById('docChatInput');
    const question = input ? input.value.trim() : '';

    if (!question) {
        alert('Please enter a question');
        return;
    }

    addDocChatMessage('user', question);
    input.value = '';

    // Add thinking message
    const thinkingId = 'thinking-' + Date.now();
    addDocChatMessage('ai', '🤔 Analyzing question and routing to best strategy...', thinkingId);

    try {
        const response = await fetch(API_BASE + '/documents/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });

        // Remove thinking message
        const thinkingMsg = document.getElementById(thinkingId);
        if (thinkingMsg) {
            thinkingMsg.remove();
        }

        if (response.ok) {
            const data = await response.json();

            // Update state
            queryCount++;
            lastStrategy = (data.strategy || 'unknown').toUpperCase();
            updateVectorStoreStats();

            // Display answer with routing info
            displayAnswer(data);
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Question failed');
        }
    } catch (error) {
        console.error('Document Q&A error:', error);

        // Remove thinking message
        const thinkingMsg = document.getElementById(thinkingId);
        if (thinkingMsg) {
            thinkingMsg.remove();
        }

        addDocChatMessage('ai', '❌ Error: ' + error.message);
    }
}

// Display answer with enhanced formatting
function displayAnswer(data) {
    const container = document.getElementById('docChatMessages');
    const welcome = container.previousElementSibling;

    // Hide welcome message
    if (welcome && welcome.classList.contains('chat-welcome')) {
        welcome.style.display = 'none';
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message ai';

    // Strategy icon and badge
    const strategyIcons = {
        'vector': '📄',
        'web': '🌐',
        'llm': '🤖',
        'hybrid': '🔄'
    };

    const strategyColors = {
        'vector': 'vector',
        'web': 'web',
        'llm': 'llm',
        'hybrid': 'hybrid'
    };

    const strategy = (data.strategy || 'llm').toLowerCase();
    const icon = strategyIcons[strategy] || '🤖';
    const badgeClass = strategyColors[strategy] || 'llm';

    // Build message HTML
    let html = `
        <div class="message-header">
            <span class="message-icon">${icon}</span>
            <span class="message-role">AI Assistant</span>
            <span class="source-badge ${badgeClass}">${strategy}</span>
        </div>
        <div class="message-content">${escapeHtml(data.answer).replace(/\n/g, '<br>')}</div>
    `;

    // Add sources if available
    if (data.sources && data.sources.length > 0) {
        html += `
            <div class="sources-list">
                <strong>📚 Sources (${data.sources.length}):</strong>
                ${data.sources.map(source =>
                    `<span class="source-item">📄 ${escapeHtml(source)}</span>`
                ).join('')}
            </div>
        `;
    }

    // Add routing info
    const confidence = data.routing_confidence ? (data.routing_confidence * 100).toFixed(0) : 'N/A';
    html += `
        <div class="message-routing-info">
            🎯 <strong>Routing:</strong> ${strategy.toUpperCase()} strategy
            (Confidence: ${confidence}%)
        </div>
    `;

    messageDiv.innerHTML = html;
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

// Add message to document chat (simplified version for user messages)
function addDocChatMessage(role, text, messageId = null) {
    const container = document.getElementById('docChatMessages');
    const welcome = container.previousElementSibling;

    // Hide welcome message after first interaction
    if (welcome && welcome.classList.contains('chat-welcome')) {
        welcome.style.display = 'none';
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message ' + role;
    if (messageId) {
        messageDiv.id = messageId;
    }

    const roleLabel = role === 'user' ? 'You' : 'AI';
    const icon = role === 'user' ? '👤' : '🤖';

    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-icon">${icon}</span>
            <span class="message-role">${roleLabel}</span>
        </div>
        <div class="message-content">${escapeHtml(text).replace(/\n/g, '<br>')}</div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

// Clear document chat
function clearDocChat() {
    const container = document.getElementById('docChatMessages');
    if (!container) {
        console.error('docChatMessages element not found');
        return;
    }

    container.innerHTML = '';

    const welcome = document.querySelector('#docChatContainer .chat-welcome');
    if (welcome) {
        welcome.style.display = 'block';
    }

    // Reset stats
    queryCount = 0;
    lastStrategy = 'None';
    updateVectorStoreStats();
}

// Load documents list
async function loadDocuments() {
    const container = document.getElementById('documentsTable');
    if (!container) return;

    container.innerHTML = '<div class="loading">Loading documents from vector store...</div>';

    try {
        const response = await fetch(API_BASE + '/documents');
        const data = await response.json();

        if (data.documents && data.documents.length > 0) {
            renderDocumentsTable(data.documents);
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <p>📭 No documents in vector store yet.</p>
                    <p>Upload your first document above to get started!</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading documents:', error);
        container.innerHTML = '<div class="error">Error loading documents: ' + error.message + '</div>';
    }
}

// Render documents table with enhanced info
function renderDocumentsTable(documents) {
    const container = document.getElementById('documentsTable');

    let html = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Filename</th>
                    <th>Category</th>
                    <th>Pages</th>
                    <th>Upload Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

    documents.forEach(doc => {
        const uploadDate = doc.upload_date ? new Date(doc.upload_date).toLocaleDateString() : 'N/A';
        const category = doc.category || 'general';

        html += `
            <tr>
                <td><strong>📄 ${escapeHtml(doc.filename)}</strong></td>
                <td><span class="badge">${escapeHtml(category)}</span></td>
                <td>${doc.page_count || 1}</td>
                <td>${uploadDate}</td>
                <td><span style="color: #10b981;">● Indexed</span></td>
                <td>
                    <button class="btn-small btn-danger" onclick="deleteDocument('${doc.document_id}', '${escapeHtml(doc.filename)}')">
                        🗑️ Delete
                    </button>
                </td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
        <div style="margin-top: 15px; padding: 10px; background: rgba(59, 130, 246, 0.1); border-radius: 6px; font-size: 0.9em; color: #1e40af;">
            <strong>💡 Tip:</strong> All ${documents.length} documents are vectorized and searchable. Ask questions about them using the Q&A section above!
        </div>
    `;

    container.innerHTML = html;
}

// Delete document
async function deleteDocument(documentId, filename) {
    if (!confirm(`Are you sure you want to delete "${filename}" from the vector store?`)) {
        return;
    }

    try {
        const response = await fetch(API_BASE + '/documents/' + documentId, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Document removed from vector store');
            updateVectorStoreStats();
            loadDocuments();
        } else {
            throw new Error(data.message || 'Delete failed');
        }
    } catch (error) {
        console.error('Delete error:', error);
        alert('❌ Error deleting document: ' + error.message);
    }
}

// Export document list
async function exportDocumentList() {
    try {
        const response = await fetch(API_BASE + '/documents');
        const data = await response.json();

        if (!data.documents || data.documents.length === 0) {
            alert('No documents to export');
            return;
        }

        // Create CSV
        const headers = ['Filename', 'Category', 'Pages', 'Upload Date', 'Document ID'];
        const rows = data.documents.map(doc => [
            doc.filename,
            doc.category || 'general',
            doc.page_count || 1,
            doc.upload_date || 'N/A',
            doc.document_id
        ]);

        const csv = [headers, ...rows].map(row => row.join(',')).join('\n');

        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vector-store-documents-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);

        alert(`✅ Exported ${data.documents.length} documents to CSV`);
    } catch (error) {
        console.error('Export error:', error);
        alert('❌ Error exporting documents: ' + error.message);
    }
}

// Ask predefined question
function askDocQuestion(question) {
    const input = document.getElementById('docChatInput');
    if (input) {
        input.value = question;
        input.focus();
    }
}

// HTML escape helper
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Expose functions to global window scope for inline onclick handlers
window.uploadDocument = uploadDocument;
window.sendDocQuestion = sendDocQuestion;
window.clearDocChat = clearDocChat;
window.askDocQuestion = askDocQuestion;
window.loadDocuments = loadDocuments;
window.deleteDocument = deleteDocument;
window.exportDocumentList = exportDocumentList;
window.updateVectorStoreStats = updateVectorStoreStats;

console.log('✅ All document RAG functions loaded and ready');
