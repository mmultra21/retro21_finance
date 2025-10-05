-- DuckDB Schema for Financial Transactions
-- Fixed version compatible with DuckDB

-- Drop existing tables if they exist
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS import_logs;

-- Create accounts table
CREATE TABLE accounts (
    account_id VARCHAR PRIMARY KEY,
    account_name VARCHAR NOT NULL,
    account_type VARCHAR NOT NULL,
    bank_name VARCHAR,
    currency VARCHAR DEFAULT 'USD',
    opening_balance DECIMAL(15,2) DEFAULT 0.00,
    current_balance DECIMAL(15,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create categories table
CREATE TABLE categories (
    category_id VARCHAR PRIMARY KEY,
    category_name VARCHAR NOT NULL,
    parent_category VARCHAR,
    category_type VARCHAR NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create main transactions table
CREATE TABLE transactions (
    transaction_id VARCHAR PRIMARY KEY,
    date DATE NOT NULL,
    account VARCHAR NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR DEFAULT 'USD',
    merchant VARCHAR,
    description TEXT,
    category VARCHAR,
    transaction_type VARCHAR,
    check_number VARCHAR,
    reference_id VARCHAR,
    account_type VARCHAR,
    bank_name VARCHAR,
    is_cleared BOOLEAN DEFAULT TRUE,
    is_reconciled BOOLEAN DEFAULT FALSE,
    source VARCHAR,
    source_file VARCHAR,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create import logs table
CREATE TABLE import_logs (
    log_id VARCHAR PRIMARY KEY,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_type VARCHAR NOT NULL,
    source_file VARCHAR,
    bank_name VARCHAR,
    account_name VARCHAR,
    records_processed INTEGER DEFAULT 0,
    records_imported INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    status VARCHAR DEFAULT 'completed',
    error_message TEXT,
    metadata VARCHAR
);

-- Create indexes for performance
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_account ON transactions(account);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_transactions_merchant ON transactions(merchant);
CREATE INDEX idx_transactions_amount ON transactions(amount);

-- Insert default categories
INSERT INTO categories (category_id, category_name, category_type, description) VALUES
('income_salary', 'Income:Salary:Primary', 'income', 'Primary employment salary'),
('income_salary_secondary', 'Income:Salary:Secondary', 'income', 'Secondary employment salary'),
('income_freelance', 'Income:Freelance', 'income', 'Freelance and contract work'),
('income_investment', 'Income:Investments:Dividends', 'income', 'Investment dividends and interest'),
('income_interest', 'Income:Investments:Interest', 'income', 'Bank interest and savings'),
('income_other', 'Income:Other', 'income', 'Other income sources'),
('expense_housing_rent', 'Expenses:Housing:Rent', 'expense', 'Rent or mortgage payments'),
('expense_housing_utilities', 'Expenses:Housing:Utilities', 'expense', 'Electric, gas, water, sewer'),
('expense_housing_internet', 'Expenses:Housing:Internet', 'expense', 'Internet and cable services'),
('expense_housing_insurance', 'Expenses:Housing:Insurance', 'expense', 'Home/renters insurance'),
('expense_housing_maintenance', 'Expenses:Housing:Maintenance', 'expense', 'Home repairs and maintenance'),
('expense_food_groceries', 'Expenses:Food:Groceries', 'expense', 'Grocery shopping'),
('expense_food_restaurants', 'Expenses:Food:Restaurants', 'expense', 'Dining out and takeout'),
('expense_food_coffee', 'Expenses:Food:Coffee', 'expense', 'Coffee shops and cafes'),
('expense_transport_gas', 'Expenses:Transportation:Gas', 'expense', 'Vehicle fuel'),
('expense_transport_public', 'Expenses:Transportation:Public', 'expense', 'Public transportation'),
('expense_transport_maintenance', 'Expenses:Transportation:Maintenance', 'expense', 'Vehicle maintenance and repairs'),
('expense_transport_insurance', 'Expenses:Transportation:Insurance', 'expense', 'Auto insurance'),
('expense_health_medical', 'Expenses:Health:Medical', 'expense', 'Medical appointments and procedures'),
('expense_health_dental', 'Expenses:Health:Dental', 'expense', 'Dental care'),
('expense_health_pharmacy', 'Expenses:Health:Pharmacy', 'expense', 'Prescriptions and pharmacy'),
('expense_health_insurance', 'Expenses:Health:Insurance', 'expense', 'Health insurance premiums'),
('expense_entertainment_movies', 'Expenses:Entertainment:Movies', 'expense', 'Movies and theater'),
('expense_entertainment_streaming', 'Expenses:Entertainment:Streaming', 'expense', 'Streaming services'),
('expense_entertainment_games', 'Expenses:Entertainment:Games', 'expense', 'Games and gaming'),
('expense_entertainment_books', 'Expenses:Entertainment:Books', 'expense', 'Books and reading'),
('expense_shopping_clothing', 'Expenses:Shopping:Clothing', 'expense', 'Clothing and accessories'),
('expense_shopping_electronics', 'Expenses:Shopping:Electronics', 'expense', 'Electronics and gadgets'),
('expense_shopping_home', 'Expenses:Shopping:Home', 'expense', 'Home goods and furniture'),
('expense_shopping_personal', 'Expenses:Shopping:Personal', 'expense', 'Personal care items'),
('expense_financial_fees', 'Expenses:Financial:Fees', 'expense', 'Bank fees and charges'),
('expense_financial_interest', 'Expenses:Financial:Interest', 'expense', 'Interest payments'),
('expense_financial_taxes', 'Expenses:Financial:Taxes', 'expense', 'Tax payments'),
('expense_other_misc', 'Expenses:Other:Miscellaneous', 'expense', 'Miscellaneous expenses');

-- Insert default accounts
INSERT INTO accounts (account_id, account_name, account_type, bank_name) VALUES
('assets_checking_main', 'Assets:Checking:MainBank', 'checking', 'Main Bank'),
('assets_savings_main', 'Assets:Savings:MainBank', 'savings', 'Main Bank'),
('liabilities_credit_main', 'Liabilities:CreditCard:MainCard', 'credit', 'Main Bank'),
('assets_checking_cu', 'Assets:Checking:CreditUnion', 'checking', 'Credit Union'),
('assets_savings_cu', 'Assets:Savings:CreditUnion', 'savings', 'Credit Union');

-- Insert sample transactions for testing
INSERT INTO transactions (transaction_id, date, merchant, amount, category, account, transaction_type, description) VALUES
('sample-1', '2024-10-01', 'Grocery Store', -125.50, 'Expenses:Food:Groceries', 'Assets:Checking:MainBank', 'expense', 'Weekly groceries'),
('sample-2', '2024-10-02', 'Gas Station', -45.00, 'Expenses:Transportation:Gas', 'Assets:Checking:MainBank', 'expense', 'Fill up'),
('sample-3', '2024-10-03', 'Employer Inc', 2500.00, 'Income:Salary:Primary', 'Assets:Checking:MainBank', 'income', 'Bi-weekly paycheck'),
('sample-4', '2024-10-03', 'Coffee Shop', -5.75, 'Expenses:Food:Coffee', 'Assets:Checking:MainBank', 'expense', 'Morning coffee'),
('sample-5', '2024-10-04', 'Electric Company', -120.00, 'Expenses:Housing:Utilities', 'Assets:Checking:MainBank', 'expense', 'Electric bill');
