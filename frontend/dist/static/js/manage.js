// Manage Data Tab Functions

let allTransactions = [];
let selectedTransactions = new Set();
// API_BASE is defined in app.js

// Load transactions
async function loadTransactions() {
    const search = document.getElementById('searchInput').value;
    const url = search
        ? API_BASE + '/transactions?limit=100&search=' + encodeURIComponent(search)
        : API_BASE + '/transactions?limit=100';

    try {
        const response = await fetch(url);
        const data = await response.json();

        allTransactions = data.transactions || [];
        selectedTransactions.clear();
        renderTransactionsTable(allTransactions);

        console.log('Loaded ' + allTransactions.length + ' transactions');
    } catch (error) {
        console.error('Error loading transactions:', error);
        document.getElementById('transactionsTable').innerHTML =
            '<div class="error">Error loading transactions. Check console for details.</div>';
    }
}

// Toggle transaction selection
function toggleSelection(transactionId) {
    if (selectedTransactions.has(transactionId)) {
        selectedTransactions.delete(transactionId);
    } else {
        selectedTransactions.add(transactionId);
    }
    updateBulkEditButton();
}

// Select all transactions
function toggleSelectAll() {
    const checkbox = document.getElementById('selectAll');
    if (checkbox.checked) {
        allTransactions.forEach(txn => selectedTransactions.add(txn.transaction_id));
    } else {
        selectedTransactions.clear();
    }
    renderTransactionsTable(allTransactions);
    updateBulkEditButton();
}

// Update bulk edit button visibility
function updateBulkEditButton() {
    const bulkBtn = document.getElementById('bulkEditBtn');
    const bulkDelBtn = document.getElementById('bulkDeleteBtn');
    if (bulkBtn && bulkDelBtn) {
        if (selectedTransactions.size > 0) {
            bulkBtn.style.display = 'inline-block';
            bulkDelBtn.style.display = 'inline-block';
            bulkBtn.textContent = `✏️ Bulk Edit (${selectedTransactions.size})`;
            bulkDelBtn.textContent = `🗑️ Bulk Delete (${selectedTransactions.size})`;
        } else {
            bulkBtn.style.display = 'none';
            bulkDelBtn.style.display = 'none';
        }
    }
}

// Render transactions table
function renderTransactionsTable(transactions) {
    const container = document.getElementById('transactionsTable');

    if (!transactions || transactions.length === 0) {
        container.innerHTML = '<div class="loading">No transactions found.</div>';
        return;
    }

    let html = '<table class="data-table"><thead><tr>';
    html += '<th><input type="checkbox" id="selectAll" onchange="toggleSelectAll()"></th>';
    html += '<th>Post Date</th><th>Check</th><th>Description</th><th>Debit</th><th>Credit</th><th>Category</th><th>Actions</th>';
    html += '</tr></thead><tbody>';

    transactions.forEach(function(txn) {
        const isSelected = selectedTransactions.has(txn.transaction_id);
        const debit = txn.amount < 0 ? Math.abs(txn.amount) : '';
        const credit = txn.amount >= 0 ? txn.amount : '';

        const debitFormatted = debit ? new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(debit) : '';

        const creditFormatted = credit ? new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(credit) : '';

        html += '<tr' + (isSelected ? ' class="selected-row"' : '') + '>';
        html += '<td><input type="checkbox" ' + (isSelected ? 'checked' : '') + ' onchange="toggleSelection(\'' + txn.transaction_id + '\')"></td>';
        html += '<td>' + (txn.date || 'N/A') + '</td>';
        html += '<td>' + (txn.check_number || '') + '</td>';
        html += '<td>' + (txn.description || txn.merchant || 'N/A') + '</td>';
        html += '<td class="amount-negative">' + debitFormatted + '</td>';
        html += '<td class="amount-positive">' + creditFormatted + '</td>';
        html += '<td>' + (txn.category || 'Uncategorized') + '</td>';
        html += '<td><div class="action-btns">';
        html += '<button class="btn btn-small btn-edit" onclick="editTransaction(\'' + txn.transaction_id + '\')">✏️</button>';
        html += '<button class="btn btn-small btn-delete" onclick="deleteTransaction(\'' + txn.transaction_id + '\')">🗑️</button>';
        html += '</div></td>';
        html += '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;

    // Update select all checkbox
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = selectedTransactions.size === transactions.length && transactions.length > 0;
    }
}

// Bulk edit transactions
async function bulkEditTransactions() {
    if (selectedTransactions.size === 0) {
        alert('Please select transactions to edit');
        return;
    }

    const newCategory = prompt('Enter new category for ' + selectedTransactions.size + ' selected transaction(s):', '');
    if (newCategory === null || newCategory === '') return;

    try {
        const updates = [];
        for (const txnId of selectedTransactions) {
            updates.push(
                fetch(API_BASE + '/transactions/' + txnId, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ category: newCategory })
                })
            );
        }

        await Promise.all(updates);
        alert('Successfully updated ' + selectedTransactions.size + ' transaction(s)!');
        selectedTransactions.clear();
        loadTransactions();
    } catch (error) {
        alert('Error updating transactions: ' + error.message);
    }
}

// Bulk delete transactions
async function bulkDeleteTransactions() {
    if (selectedTransactions.size === 0) {
        alert('Please select transactions to delete');
        return;
    }

    if (!confirm('Are you sure you want to delete ' + selectedTransactions.size + ' selected transaction(s)?')) {
        return;
    }

    try {
        const deletes = [];
        for (const txnId of selectedTransactions) {
            deletes.push(
                fetch(API_BASE + '/transactions/' + txnId, {
                    method: 'DELETE'
                })
            );
        }

        await Promise.all(deletes);
        alert('Successfully deleted ' + selectedTransactions.size + ' transaction(s)!');
        selectedTransactions.clear();
        loadTransactions();
    } catch (error) {
        alert('Error deleting transactions: ' + error.message);
    }
}

// Edit transaction
async function editTransaction(transactionId) {
    const txn = allTransactions.find(function(t) { return t.transaction_id === transactionId; });
    if (!txn) {
        alert('Transaction not found');
        return;
    }

    const newDescription = prompt('Edit Description:', txn.description || txn.merchant || '');
    if (newDescription === null) return;

    const newCategory = prompt('Edit Category:', txn.category || '');
    if (newCategory === null) return;

    const newAmount = prompt('Edit Amount (use negative for debit):', txn.amount || '');
    if (newAmount === null) return;

    try {
        const response = await fetch(API_BASE + '/transactions/' + transactionId, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                description: newDescription,
                category: newCategory,
                amount: parseFloat(newAmount)
            })
        });

        if (response.ok) {
            alert('Transaction updated successfully!');
            loadTransactions();
        } else {
            const data = await response.json();
            alert('Error: ' + (data.detail || 'Update failed'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Delete transaction
async function deleteTransaction(transactionId) {
    if (!confirm('Are you sure you want to delete this transaction?')) {
        return;
    }

    try {
        const response = await fetch(API_BASE + '/transactions/' + transactionId, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('Transaction deleted successfully!');
            loadTransactions();
        } else {
            const data = await response.json();
            alert('Error: ' + (data.detail || 'Delete failed'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Export transactions to CSV
async function exportTransactions() {
    if (allTransactions.length === 0) {
        alert('No transactions to export. Load transactions first.');
        return;
    }

    const headers = ['Post Date', 'Check', 'Description', 'Debit', 'Credit', 'Category', 'Balance'];
    const csvRows = [headers.join(',')];

    allTransactions.forEach(function(txn) {
        const debit = txn.amount < 0 ? Math.abs(txn.amount) : '';
        const credit = txn.amount >= 0 ? txn.amount : '';

        const row = [
            txn.date || '',
            txn.check_number || '',
            '"' + (txn.description || txn.merchant || '').replace(/"/g, '""') + '"',
            debit,
            credit,
            '"' + (txn.category || '').replace(/"/g, '""') + '"',
            '' // Balance - to be calculated if needed
        ];
        csvRows.push(row.join(','));
    });

    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', 'transactions_' + new Date().toISOString().split('T')[0] + '.csv');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    alert('CSV exported successfully!');
}

// Clear all transactions from database
async function clearAllTransactions() {
    // First warning
    const firstConfirm = confirm(
        '⚠️ WARNING: This will DELETE ALL TRANSACTIONS from the database!\n\n' +
        'This action CANNOT be undone.\n\n' +
        'Are you sure you want to continue?'
    );

    if (!firstConfirm) {
        return;
    }

    // Second confirmation - require typing
    const confirmation = prompt(
        '⚠️ FINAL WARNING ⚠️\n\n' +
        'You are about to permanently delete ALL transactions.\n\n' +
        'Type "DELETE ALL" to confirm (case sensitive):'
    );

    if (confirmation !== 'DELETE ALL') {
        alert('Cancelled. No transactions were deleted.');
        return;
    }

    try {
        const response = await fetch(API_BASE + '/transactions/clear-all', {
            method: 'DELETE'
        });

        if (response.ok) {
            const data = await response.json();
            alert('✅ Successfully deleted all transactions!\n\nDeleted: ' + (data.deleted_count || 'all') + ' transactions');
            selectedTransactions.clear();
            loadTransactions();
        } else {
            const data = await response.json();
            alert('Error: ' + (data.detail || 'Failed to clear transactions'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Expose functions to global scope
window.loadTransactions = loadTransactions;
window.toggleSelection = toggleSelection;
window.toggleSelectAll = toggleSelectAll;
window.bulkEditTransactions = bulkEditTransactions;
window.bulkDeleteTransactions = bulkDeleteTransactions;
window.editTransaction = editTransaction;
window.deleteTransaction = deleteTransaction;
window.exportTransactions = exportTransactions;
window.clearAllTransactions = clearAllTransactions;

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
});
