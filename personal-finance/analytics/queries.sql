-- Parameterized SQL templates for financial analytics
-- Use with DuckDB for fast analytical queries

-- Basic transaction summary
-- Parameters: start_date, end_date, account_filter
SELECT 
    account,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount,
    MIN(amount) as min_amount,
    MAX(amount) as max_amount
FROM transactions 
WHERE date >= $start_date 
    AND date <= $end_date
    AND ($account_filter IS NULL OR account LIKE '%' || $account_filter || '%')
GROUP BY account
ORDER BY total_amount DESC;

-- Monthly cash flow analysis
-- Parameters: start_date, end_date
SELECT 
    YEAR(date) as year,
    MONTH(date) as month,
    DATE_TRUNC('month', date) as month_start,
    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
    SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses,
    SUM(amount) as net_cash_flow
FROM transactions 
WHERE date >= $start_date 
    AND date <= $end_date
GROUP BY YEAR(date), MONTH(date), DATE_TRUNC('month', date)
ORDER BY year, month;

-- Category spending analysis
-- Parameters: start_date, end_date, min_amount
SELECT 
    category,
    COUNT(*) as transaction_count,
    SUM(ABS(amount)) as total_spent,
    AVG(ABS(amount)) as avg_transaction,
    MAX(ABS(amount)) as largest_transaction
FROM transactions 
WHERE date >= $start_date 
    AND date <= $end_date
    AND amount < 0  -- Expenses only
    AND ABS(amount) >= COALESCE($min_amount, 0)
GROUP BY category
ORDER BY total_spent DESC;

-- Account balances over time
-- Parameters: start_date, end_date, account_list
SELECT 
    account,
    date,
    amount,
    SUM(amount) OVER (
        PARTITION BY account 
        ORDER BY date 
        ROWS UNBOUNDED PRECEDING
    ) as running_balance
FROM transactions 
WHERE date >= $start_date 
    AND date <= $end_date
    AND ($account_list IS NULL OR account = ANY($account_list))
ORDER BY account, date;

-- Top merchants by spending
-- Parameters: start_date, end_date, limit_count
SELECT 
    merchant,
    COUNT(*) as visit_count,
    SUM(ABS(amount)) as total_spent,
    AVG(ABS(amount)) as avg_spent_per_visit,
    MAX(ABS(amount)) as largest_purchase
FROM transactions 
WHERE date >= $start_date 
    AND date <= $end_date
    AND amount < 0  -- Expenses only
    AND merchant IS NOT NULL
GROUP BY merchant
ORDER BY total_spent DESC
LIMIT COALESCE($limit_count, 20);

-- Income vs expenses by category
-- Parameters: start_date, end_date
SELECT 
    category,
    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expenses,
    SUM(amount) as net
FROM transactions 
WHERE date >= $start_date 
    AND date <= $end_date
GROUP BY category
HAVING SUM(ABS(amount)) > 0
ORDER BY net DESC;

-- Weekly spending patterns
-- Parameters: start_date, end_date
SELECT 
    DAYNAME(date) as day_of_week,
    DAYOFWEEK(date) as day_number,
    COUNT(*) as transaction_count,
    SUM(ABS(amount)) as total_spent,
    AVG(ABS(amount)) as avg_transaction
FROM transactions 
WHERE date >= $start_date 
    AND date <= $end_date
    AND amount < 0  -- Expenses only
GROUP BY DAYNAME(date), DAYOFWEEK(date)
ORDER BY day_number;

-- Unusual transactions detection
-- Parameters: start_date, end_date, std_dev_threshold
WITH transaction_stats AS (
    SELECT 
        category,
        AVG(ABS(amount)) as avg_amount,
        STDDEV(ABS(amount)) as std_amount
    FROM transactions 
    WHERE date >= $start_date AND date <= $end_date
    GROUP BY category
)
SELECT 
    t.date,
    t.merchant,
    t.category,
    t.amount,
    ts.avg_amount,
    ABS(t.amount - ts.avg_amount) / ts.std_amount as z_score
FROM transactions t
JOIN transaction_stats ts ON t.category = ts.category
WHERE t.date >= $start_date 
    AND t.date <= $end_date
    AND ts.std_amount > 0
    AND ABS(t.amount - ts.avg_amount) / ts.std_amount > COALESCE($std_dev_threshold, 2.0)
ORDER BY z_score DESC;

-- Budget vs actual analysis
-- Parameters: start_date, end_date, budget_amounts (JSON)
SELECT 
    category,
    SUM(ABS(amount)) as actual_spent,
    COALESCE($budget_amounts ->> category, 0)::DECIMAL as budgeted,
    SUM(ABS(amount)) - COALESCE($budget_amounts ->> category, 0)::DECIMAL as variance,
    CASE 
        WHEN COALESCE($budget_amounts ->> category, 0)::DECIMAL > 0 
        THEN (SUM(ABS(amount)) / COALESCE($budget_amounts ->> category, 0)::DECIMAL) * 100 
        ELSE NULL 
    END as percent_of_budget
FROM transactions 
WHERE date >= $start_date 
    AND date <= $end_date
    AND amount < 0  -- Expenses only
GROUP BY category
ORDER BY variance DESC;