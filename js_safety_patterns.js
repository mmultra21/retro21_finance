// JavaScript Function Safety Template
// Use this pattern to avoid common gotchas

// ===== PATTERN 1: Safe Global Function Declaration =====
// ✅ Works with inline onclick handlers
// ✅ Available immediately after script loads
// ✅ Survives module bundlers

(function() {
    'use strict';
    
    // Define your function locally
    function clearDocChat() {
        const container = document.getElementById('docChatMessages');
        if (!container) {
            console.warn('clearDocChat: docChatMessages element not found');
            return;
        }
        
        container.innerHTML = '';
        
        const welcome = document.querySelector('#docChatContainer .chat-welcome');
        if (welcome) {
            welcome.style.display = 'block';
        }
        
        console.log('Document chat cleared successfully');
    }
    
    // Expose to global scope for onclick handlers
    window.clearDocChat = clearDocChat;
    
    // Also expose on the window for debugging
    if (typeof window.DEBUG !== 'undefined') {
        window.DEBUG.clearDocChat = clearDocChat;
    }
})();

// ===== PATTERN 2: DOM-Ready Safe Function =====
// ✅ Ensures DOM elements exist before function runs
// ✅ Works with any loading order

document.addEventListener('DOMContentLoaded', function() {
    
    function safeFunction() {
        // This runs only after DOM is ready
        const element = document.getElementById('someElement');
        if (element) {
            // Safe to manipulate DOM here
        }
    }
    
    // Expose globally
    window.safeFunction = safeFunction;
});

// ===== PATTERN 3: Defensive Function with Error Handling =====
// ✅ Won't break if DOM elements are missing
// ✅ Provides helpful debugging info

function defensiveFunction(elementId) {
    try {
        const element = document.getElementById(elementId);
        
        if (!element) {
            console.error(`Element with ID '${elementId}' not found`);
            return false;
        }
        
        // Your function logic here
        element.innerHTML = '';
        
        console.log(`Successfully processed element: ${elementId}`);
        return true;
        
    } catch (error) {
        console.error('Function failed:', error);
        return false;
    }
}

// ===== PATTERN 4: Modern Event Listener (No Inline HTML) =====
// ✅ Separates JS from HTML
// ✅ Works with module bundlers
// ✅ Better maintenance

document.addEventListener('DOMContentLoaded', function() {
    
    // Find button by ID or class
    const clearButton = document.getElementById('clearDocChatBtn');
    
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            clearDocChat();
        });
    } else {
        console.warn('Clear button not found - check element ID');
    }
});

// ===== PATTERN 5: Module Pattern for Bundlers =====
// ✅ Works with Vite, Webpack, etc.
// ✅ Proper module separation

const DocumentChat = {
    clear: function() {
        const container = document.getElementById('docChatMessages');
        if (container) {
            container.innerHTML = '';
        }
    },
    
    init: function() {
        // Setup event listeners
        const clearBtn = document.getElementById('clearDocChatBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', this.clear.bind(this));
        }
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    DocumentChat.init();
});

// Expose for inline handlers if needed
window.clearDocChat = DocumentChat.clear.bind(DocumentChat);

// ===== DEBUGGING HELPERS =====
// Add these to help debug function availability

window.DEBUG = window.DEBUG || {};
window.DEBUG.checkFunction = function(functionName) {
    if (typeof window[functionName] === 'function') {
        console.log(`✅ Function '${functionName}' is available`);
        return true;
    } else {
        console.error(`❌ Function '${functionName}' is NOT available`);
        console.log('Available functions:', Object.keys(window).filter(key => typeof window[key] === 'function'));
        return false;
    }
};

// Usage in browser console:
// DEBUG.checkFunction('clearDocChat')