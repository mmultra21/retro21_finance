-- DuckDB Schema for Denormalized Transactions
-- Initialize database schema for financial transaction storage

-- Drop existing tables if they exist
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS import_logs;

-- Create accounts table
CREATE TABLE accounts (
    account_id VARCHAR PRIMARY KEY,
    account_name VARCHAR NOT NULL,
    account_type VARCHAR NOT NULL,  -- checking, savings, credit, investment, etc.
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
    category_type VARCHAR NOT NULL,  -- income, expense, transfer
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create main transactions table (denormalized for analytics)
CREATE TABLE transactions (
    transaction_id VARCHAR PRIMARY KEY DEFAULT uuid(),
    date DATE NOT NULL,
    account VARCHAR NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR DEFAULT 'USD',
    merchant VARCHAR,
    description TEXT,
    category VARCHAR,
    transaction_type VARCHAR,  -- income, expense, transfer
    check_number VARCHAR,
    reference_id VARCHAR,
    
    -- Additional fields for analysis
    account_type VARCHAR,
    bank_name VARCHAR,
    is_cleared BOOLEAN DEFAULT TRUE,
    is_reconciled BOOLEAN DEFAULT FALSE,
    
    -- Import metadata
    source VARCHAR,  -- csv_import, manual, api, etc.
    source_file VARCHAR,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data JSON,
    
    -- Calculated fields
    abs_amount DECIMAL(15,2) GENERATED ALWAYS AS (ABS(amount)) STORED,
    year INTEGER GENERATED ALWAYS AS (EXTRACT(YEAR FROM date)) STORED,
    month INTEGER GENERATED ALWAYS AS (EXTRACT(MONTH FROM date)) STORED,
    quarter INTEGER GENERATED ALWAYS AS (EXTRACT(QUARTER FROM date)) STORED,
    day_of_week INTEGER GENERATED ALWAYS AS (EXTRACT(DOW FROM date)) STORED,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create import logs table
CREATE TABLE import_logs (
    log_id VARCHAR PRIMARY KEY DEFAULT uuid(),
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_type VARCHAR NOT NULL,  -- csv, api, manual
    source_file VARCHAR,
    bank_name VARCHAR,
    account_name VARCHAR,
    records_processed INTEGER DEFAULT 0,
    records_imported INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    status VARCHAR DEFAULT 'completed',  -- processing, completed, failed
    error_message TEXT,
    metadata JSON
);

-- Create indexes for performance
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_account ON transactions(account);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_transactions_merchant ON transactions(merchant);
CREATE INDEX idx_transactions_amount ON transactions(amount);
CREATE INDEX idx_transactions_year_month ON transactions(year, month);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);

-- Create composite indexes for common queries
CREATE INDEX idx_transactions_date_account ON transactions(date, account);
CREATE INDEX idx_transactions_date_category ON transactions(date, category);
CREATE INDEX idx_transactions_account_type ON transactions(account, transaction_type);

-- Insert default categories
INSERT INTO categories (category_id, category_name, category_type, description) VALUES
-- Income categories
('income_salary', 'Income:Salary:Primary', 'income', 'Primary employment salary'),
('income_salary_secondary', 'Income:Salary:Secondary', 'income', 'Secondary employment salary'),
('income_freelance', 'Income:Freelance', 'income', 'Freelance and contract work'),
('income_investment', 'Income:Investments:Dividends', 'income', 'Investment dividends and interest'),
('income_interest', 'Income:Investments:Interest', 'income', 'Bank interest and savings'),
('income_other', 'Income:Other', 'income', 'Other income sources'),

-- Housing expenses
('expense_housing_rent', 'Expenses:Housing:Rent', 'expense', 'Rent or mortgage payments'),
('expense_housing_utilities', 'Expenses:Housing:Utilities', 'expense', 'Electric, gas, water, sewer'),
('expense_housing_internet', 'Expenses:Housing:Internet', 'expense', 'Internet and cable services'),
('expense_housing_insurance', 'Expenses:Housing:Insurance', 'expense', 'Home/renters insurance'),
('expense_housing_maintenance', 'Expenses:Housing:Maintenance', 'expense', 'Home repairs and maintenance'),

-- Food expenses
('expense_food_groceries', 'Expenses:Food:Groceries', 'expense', 'Grocery shopping'),
('expense_food_restaurants', 'Expenses:Food:Restaurants', 'expense', 'Dining out and takeout'),
('expense_food_coffee', 'Expenses:Food:Coffee', 'expense', 'Coffee shops and cafes'),

-- Transportation expenses
('expense_transport_gas', 'Expenses:Transportation:Gas', 'expense', 'Vehicle fuel'),
('expense_transport_public', 'Expenses:Transportation:Public', 'expense', 'Public transportation'),
('expense_transport_maintenance', 'Expenses:Transportation:Maintenance', 'expense', 'Vehicle maintenance and repairs'),
('expense_transport_insurance', 'Expenses:Transportation:Insurance', 'expense', 'Auto insurance'),

-- Health expenses
('expense_health_medical', 'Expenses:Health:Medical', 'expense', 'Medical appointments and procedures'),
('expense_health_dental', 'Expenses:Health:Dental', 'expense', 'Dental care'),
('expense_health_pharmacy', 'Expenses:Health:Pharmacy', 'expense', 'Prescriptions and pharmacy'),
('expense_health_insurance', 'Expenses:Health:Insurance', 'expense', 'Health insurance premiums'),

-- Entertainment expenses
('expense_entertainment_movies', 'Expenses:Entertainment:Movies', 'expense', 'Movies and theater'),
('expense_entertainment_streaming', 'Expenses:Entertainment:Streaming', 'expense', 'Streaming services'),
('expense_entertainment_games', 'Expenses:Entertainment:Games', 'expense', 'Games and gaming'),
('expense_entertainment_books', 'Expenses:Entertainment:Books', 'expense', 'Books and reading'),

-- Shopping expenses
('expense_shopping_clothing', 'Expenses:Shopping:Clothing', 'expense', 'Clothing and accessories'),
('expense_shopping_electronics', 'Expenses:Shopping:Electronics', 'expense', 'Electronics and gadgets'),
('expense_shopping_home', 'Expenses:Shopping:Home', 'expense', 'Home goods and furniture'),
('expense_shopping_personal', 'Expenses:Shopping:Personal', 'expense', 'Personal care items'),

-- Financial expenses
('expense_financial_fees', 'Expenses:Financial:Fees', 'expense', 'Bank fees and charges'),
('expense_financial_interest', 'Expenses:Financial:Interest', 'expense', 'Interest payments'),
('expense_financial_taxes', 'Expenses:Financial:Taxes', 'expense', 'Tax payments'),

-- Other expenses
('expense_other_misc', 'Expenses:Other:Miscellaneous', 'expense', 'Miscellaneous expenses');

-- Insert default accounts (examples)
INSERT INTO accounts (account_id, account_name, account_type, bank_name) VALUES
('assets_checking_main', 'Assets:Checking:MainBank', 'checking', 'Main Bank'),
('assets_savings_main', 'Assets:Savings:MainBank', 'savings', 'Main Bank'),
('liabilities_credit_main', 'Liabilities:CreditCard:MainCard', 'credit', 'Main Bank'),
('assets_checking_cu', 'Assets:Checking:CreditUnion', 'checking', 'Credit Union'),
('assets_savings_cu', 'Assets:Savings:CreditUnion', 'savings', 'Credit Union');

-- Create views for common queries

-- Monthly summary view
CREATE VIEW monthly_summary AS
SELECT 
    year,
    month,
    account,
    category,
    transaction_type,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount,
    MIN(amount) as min_amount,
    MAX(amount) as max_amount
FROM transactions
GROUP BY year, month, account, category, transaction_type;

-- Category summary view
CREATE VIEW category_summary AS
SELECT 
    category,
    transaction_type,
    COUNT(*) as transaction_count,
    SUM(abs_amount) as total_spent,
    AVG(abs_amount) as avg_transaction,
    MIN(date) as first_transaction,
    MAX(date) as last_transaction
FROM transactions
WHERE category IS NOT NULL
GROUP BY category, transaction_type
ORDER BY total_spent DESC;

-- Account balance view (running balances)
CREATE VIEW account_balances AS
SELECT 
    account,
    date,
    amount,
    SUM(amount) OVER (
        PARTITION BY account 
        ORDER BY date, created_at 
        ROWS UNBOUNDED PRECEDING
    ) as running_balance
FROM transactions
ORDER BY account, date, created_at;

-- Monthly cash flow view
CREATE VIEW monthly_cash_flow AS
SELECT 
    year,
    month,
    DATE_TRUNC('month', date) as month_start,
    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
    SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses,
    SUM(amount) as net_cash_flow,
    COUNT(*) as total_transactions
FROM transactions
GROUP BY year, month, DATE_TRUNC('month', date)
ORDER BY year, month;

-- Top merchants view
CREATE VIEW top_merchants AS
SELECT 
    merchant,
    COUNT(*) as visit_count,
    SUM(abs_amount) as total_spent,
    AVG(abs_amount) as avg_spent_per_visit,
    MAX(abs_amount) as largest_purchase,
    MIN(date) as first_visit,
    MAX(date) as last_visit
FROM transactions
WHERE merchant IS NOT NULL 
  AND amount < 0  -- Expenses only
GROUP BY merchant
HAVING COUNT(*) > 1
ORDER BY total_spent DESC;

-- Create triggers to update timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: DuckDB doesn't support triggers, so we'll handle timestamp updates in the application