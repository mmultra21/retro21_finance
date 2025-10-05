// Personal Finance Dashboard - JavaScript

const API_BASE = 'http://127.0.0.1:8000';

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    setupTabs();
    checkAPIStatus();
    checkLLMStatus();
    loadTemplates();
    loadForms();

    // Refresh status every 30 seconds
    setInterval(checkAPIStatus, 30000);
    setInterval(checkLLMStatus, 30000);
});

// Tab switching
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');

            // Remove active class from all
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked
            button.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        });
    });
}

// Check API status
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        const statusElement = document.getElementById('apiStatus');
        if (response.ok) {
            statusElement.textContent = '🟢 API Online';
            statusElement.classList.add('online');
        } else {
            statusElement.textContent = '🔴 API Offline';
            statusElement.classList.remove('online');
        }
    } catch (error) {
        const statusElement = document.getElementById('apiStatus');
        statusElement.textContent = '🔴 API Offline';
        statusElement.classList.remove('online');
    }
}

// Check LLM status
async function checkLLMStatus() {
    try {
        const response = await fetch(`${API_BASE}/llm/health`);
        const data = await response.json();
        const statusElement = document.getElementById('llmStatus');

        if (response.ok && data.status === 'online') {
            statusElement.textContent = `🟢 LLM Online (${data.model || 'unknown'})`;
            statusElement.classList.add('online');
        } else {
            statusElement.textContent = '🔴 LLM Offline';
            statusElement.classList.remove('online');
        }
    } catch (error) {
        const statusElement = document.getElementById('llmStatus');
        statusElement.textContent = '🔴 LLM Offline';
        statusElement.classList.remove('online');
    }
}

// Load overview data
async function loadOverview() {
    // Sample data for demonstration
    // In production, this would fetch from /analytics/summary

    document.getElementById('totalIncome').textContent = '$5,250.00';
    document.getElementById('totalExpenses').textContent = '$3,847.62';
    document.getElementById('netSavings').textContent = '$1,402.38';
    document.getElementById('savingsRate').textContent = '26.7%';

    showNotification('Overview data loaded (sample data)', 'success');
}

// Load narrative templates
async function loadTemplates() {
    try {
        const response = await fetch(`${API_BASE}/narrate/templates`);
        const data = await response.json();

        const select = document.getElementById('narrativeTemplate');
        select.innerHTML = '<option value="">-- Select a template --</option>';

        for (const [key, template] of Object.entries(data.templates)) {
            const option = document.createElement('option');
            option.value = template.template;
            option.textContent = template.name.replace(/_/g, ' ').toUpperCase();
            select.appendChild(option);
        }
    } catch (error) {
        console.error('Error loading templates:', error);
        document.getElementById('narrativeTemplate').innerHTML =
            '<option value="">Error loading templates</option>';
    }
}

// Generate narrative
async function generateNarrative() {
    const template = document.getElementById('narrativeTemplate').value;
    const income = document.getElementById('narIncome').value || '$0';
    const expenses = document.getElementById('narExpenses').value || '$0';
    const savings = document.getElementById('narSavings').value || '$0';
    const category = document.getElementById('narCategory').value || 'Unknown';

    if (!template) {
        showNotification('Please select a template first', 'error');
        return;
    }

    const facts = {
        total_income: income,
        total_expenses: expenses,
        net_savings: savings,
        top_category: category,
        month: new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    };

    try {
        showNotification('Generating narrative...', 'info');

        const response = await fetch(`${API_BASE}/narrate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ template, facts })
        });

        const data = await response.json();

        if (response.ok) {
            const resultBox = document.getElementById('narrativeResult');
            const textEl = document.getElementById('narrativeText');
            const metaEl = document.getElementById('narrativeMeta');

            textEl.textContent = data.text;
            metaEl.innerHTML = `
                <strong>Tokens:</strong> ${data.usage?.total_tokens || 'N/A'} |
                <strong>Generated:</strong> ${new Date().toLocaleString()}
            `;

            resultBox.style.display = 'block';
            showNotification('Narrative generated successfully!', 'success');
        } else {
            showNotification(`Error: ${data.detail || 'Failed to generate narrative'}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

// Load available forms
async function loadForms() {
    try {
        const response = await fetch(`${API_BASE}/forms/available`);
        const data = await response.json();

        const formsList = document.getElementById('formsList');
        formsList.innerHTML = '';

        if (data.forms && data.forms.length > 0) {
            data.forms.forEach(form => {
                const formItem = document.createElement('div');
                formItem.className = 'form-item';
                formItem.innerHTML = `
                    <h4>${form}</h4>
                    <p>Tax form available for automated filling</p>
                `;
                formsList.appendChild(formItem);
            });
        } else {
            formsList.innerHTML = '<div class="loading">No forms available</div>';
        }
    } catch (error) {
        console.error('Error loading forms:', error);
        document.getElementById('formsList').innerHTML =
            '<div class="error">Error loading forms</div>';
    }
}

// Import CSV
async function importCSV() {
    const fileInput = document.getElementById('csvFile');
    const bank = document.getElementById('bankSelect').value;

    if (!fileInput.files || fileInput.files.length === 0) {
        showNotification('Please select a CSV file first', 'error');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('bank', bank);

    try {
        showNotification('Uploading and importing transactions...', 'info');

        const response = await fetch(`${API_BASE}/ingest/csv`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            const resultBox = document.getElementById('importResult');
            const textEl = document.getElementById('importText');

            textEl.innerHTML = `
                <div class="success">
                    <strong>Success!</strong> ${data.message}<br>
                    Transactions imported: ${data.transactions_count || 0}<br>
                    Bank: ${data.bank}
                </div>
            `;

            resultBox.style.display = 'block';
            showNotification('Import successful!', 'success');

            // Clear file input
            fileInput.value = '';
        } else {
            showNotification(`Error: ${data.detail || 'Import failed'}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

// Show notification (simple alert for now)
function showNotification(message, type) {
    // In production, use a toast library
    // For now, just log and optionally alert
    console.log(`[${type.toUpperCase()}] ${message}`);

    if (type === 'error') {
        alert(message);
    }
}

// Initialize on load
window.addEventListener('load', () => {
    loadOverview();
});

// ============================================
// Manage Data Tab Functions
// ============================================

// allTransactions is defined in manage.js

// Load transactions
async function loadTransactions() {
    const search = document.getElementById('searchInput').value;
    const url = search
        ? `${API_BASE}/transactions?limit=100&search=${encodeURIComponent(search)}`
        : `${API_BASE}/transactions?limit=100`;

    try {
        const response = await fetch(url);
        const data = await response.json();

        allTransactions = data.transactions || [];
        renderTransactionsTable(allTransactions);

        showNotification(`Loaded ${allTransactions.length} transactions`, 'success');
    } catch (error) {
        console.error('Error loading transactions:', error);
        document.getElementById('transactionsTable').innerHTML =
            '<div class="error">Error loading transactions. Check console for details.</div>';
    }
}

// Render transactions table
function renderTransactionsTable(transactions) {
    const container = document.getElementById('transactionsTable');

    if (!transactions || transactions.length === 0) {
        container.innerHTML = '<div class="loading">No transactions found.</div>';
        return;
    }

    let html = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Merchant</th>
                    <th>Amount</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

    transactions.forEach(txn => {
        const amountClass = txn.amount >= 0 ? 'amount-positive' : 'amount-negative';
        const amountFormatted = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(Math.abs(txn.amount));

        html += `
            <tr>
                <td>${txn.date || 'N/A'}</td>
                <td>${txn.merchant || 'N/A'}</td>
                <td class="${amountClass}">${txn.amount >= 0 ? '+' : '-'}${amountFormatted}</td>
                <td>${txn.category || 'Uncategorized'}</td>
                <td>${txn.description || ''}</td>
                <td>
                    <div class="action-btns">
                        <button class="btn btn-small btn-edit" onclick="editTransaction('${txn.transaction_id}')">✏️ Edit</button>
                        <button class="btn btn-small btn-delete" onclick="deleteTransaction('${txn.transaction_id}')">🗑️ Delete</button>
                    </div>
                </td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// Edit transaction
async function editTransaction(transactionId) {
    const txn = allTransactions.find(t => t.transaction_id === transactionId);
    if (!txn) {
        alert('Transaction not found');
        return;
    }

    const newMerchant = prompt('Edit Merchant:', txn.merchant || '');
    if (newMerchant === null) return; // Cancelled

    const newCategory = prompt('Edit Category:', txn.category || '');
    if (newCategory === null) return;

    const newAmount = prompt('Edit Amount:', txn.amount || '');
    if (newAmount === null) return;

    const newDescription = prompt('Edit Description:', txn.description || '');
    if (newDescription === null) return;

    try {
        const response = await fetch(`${API_BASE}/transactions/${transactionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                merchant: newMerchant,
                category: newCategory,
                amount: parseFloat(newAmount),
                description: newDescription
            })
        });

        if (response.ok) {
            showNotification('Transaction updated successfully!', 'success');
            loadTransactions(); // Reload
        } else {
            const data = await response.json();
            alert(`Error: ${data.detail || 'Update failed'}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Delete transaction
async function deleteTransaction(transactionId) {
    if (!confirm('Are you sure you want to delete this transaction?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/transactions/${transactionId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Transaction deleted successfully!', 'success');
            loadTransactions(); // Reload
        } else {
            const data = await response.json();
            alert(`Error: ${data.detail || 'Delete failed'}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Export transactions to CSV
async function exportTransactions() {
    if (allTransactions.length === 0) {
        alert('No transactions to export. Load transactions first.');
        return;
    }

    // Create CSV
    const headers = ['Date', 'Merchant', 'Amount', 'Category', 'Description', 'Type'];
    const csvRows = [headers.join(',')];

    allTransactions.forEach(txn => {
        const row = [
            txn.date || '',
            `"${(txn.merchant || '').replace(/"/g, '""')}"`,
            txn.amount || 0,
            `"${(txn.category || '').replace(/"/g, '""')}"`,
            `"${(txn.description || '').replace(/"/g, '""')}"`,
            txn.transaction_type || ''
        ];
        csvRows.push(row.join(','));
    });

    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', `transactions_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    showNotification('CSV exported successfully!', 'success');
}

// Search on Enter key
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                loadTransactions();
            }
        });
    }

    // Load transactions when Manage tab is clicked
    const manageTab = document.querySelector('[data-tab="manage"]');
    if (manageTab) {
        manageTab.addEventListener('click', function() {
            setTimeout(loadTransactions, 100);
        });
    }
});

