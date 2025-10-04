"""
DuckDB wrapper and safe SQL query runners for financial analytics.
Provides parameterized queries and data analysis functions.
"""

import duckdb
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    """
    DuckDB-based analytics engine for financial data.
    Provides safe parameterized queries and common financial analyses.
    """
    
    def __init__(self, db_path: str = None):
        """Initialize the analytics engine."""
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'storage', 'duck.db')
        
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._load_queries()
    
    def _connect(self):
        """Establish connection to DuckDB."""
        try:
            self.conn = duckdb.connect(self.db_path)
            logger.info(f"Connected to DuckDB at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise
    
    def _load_queries(self):
        """Load SQL queries from queries.sql file."""
        queries_file = os.path.join(os.path.dirname(__file__), 'queries.sql')
        if os.path.exists(queries_file):
            with open(queries_file, 'r') as f:
                self.raw_queries = f.read()
        else:
            logger.warning(f"Queries file not found: {queries_file}")
            self.raw_queries = ""
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Execute a parameterized SQL query safely.
        
        Args:
            query: SQL query string with named parameters
            params: Dictionary of parameter values
            
        Returns:
            pandas DataFrame with results
        """
        if params is None:
            params = {}
            
        try:
            # Sanitize parameters
            sanitized_params = self._sanitize_params(params)
            
            # Execute query
            result = self.conn.execute(query, sanitized_params).fetchdf()
            return result
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize query parameters to prevent injection."""
        sanitized = {}
        
        for key, value in params.items():
            if isinstance(value, (str, int, float, date, datetime)):
                sanitized[key] = value
            elif value is None:
                sanitized[key] = None
            elif isinstance(value, list):
                # For IN clauses
                sanitized[key] = [self._sanitize_single_value(v) for v in value]
            else:
                sanitized[key] = str(value)
                
        return sanitized
    
    def _sanitize_single_value(self, value: Any) -> Any:
        """Sanitize a single parameter value."""
        if isinstance(value, (str, int, float, date, datetime)):
            return value
        elif value is None:
            return None
        else:
            return str(value)
    
    def get_transaction_summary(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get basic transaction summary."""
        if filters is None:
            filters = {}
            
        query = """
        SELECT 
            account,
            COUNT(*) as transaction_count,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount,
            MIN(amount) as min_amount,
            MAX(amount) as max_amount
        FROM transactions 
        WHERE 1=1
        """
        
        params = {}
        if 'start_date' in filters:
            query += " AND date >= $start_date"
            params['start_date'] = filters['start_date']
        if 'end_date' in filters:
            query += " AND date <= $end_date"
            params['end_date'] = filters['end_date']
        if 'account' in filters:
            query += " AND account LIKE '%' || $account || '%'"
            params['account'] = filters['account']
            
        query += " GROUP BY account ORDER BY total_amount DESC"
        
        return self.execute_query(query, params)
    
    def get_monthly_cash_flow(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get monthly cash flow analysis."""
        if filters is None:
            filters = {}
            
        query = """
        SELECT 
            YEAR(date) as year,
            MONTH(date) as month,
            DATE_TRUNC('month', date) as month_start,
            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses,
            SUM(amount) as net_cash_flow
        FROM transactions 
        WHERE 1=1
        """
        
        params = {}
        if 'start_date' in filters:
            query += " AND date >= $start_date"
            params['start_date'] = filters['start_date']
        if 'end_date' in filters:
            query += " AND date <= $end_date"
            params['end_date'] = filters['end_date']
            
        query += " GROUP BY YEAR(date), MONTH(date), DATE_TRUNC('month', date)"
        query += " ORDER BY year, month"
        
        return self.execute_query(query, params)
    
    def get_category_analysis(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get spending analysis by category."""
        if filters is None:
            filters = {}
            
        query = """
        SELECT 
            category,
            COUNT(*) as transaction_count,
            SUM(ABS(amount)) as total_spent,
            AVG(ABS(amount)) as avg_transaction,
            MAX(ABS(amount)) as largest_transaction
        FROM transactions 
        WHERE amount < 0
        """
        
        params = {}
        if 'start_date' in filters:
            query += " AND date >= $start_date"
            params['start_date'] = filters['start_date']
        if 'end_date' in filters:
            query += " AND date <= $end_date"
            params['end_date'] = filters['end_date']
        if 'min_amount' in filters:
            query += " AND ABS(amount) >= $min_amount"
            params['min_amount'] = filters['min_amount']
            
        query += " GROUP BY category ORDER BY total_spent DESC"
        
        return self.execute_query(query, params)
    
    def get_merchant_analysis(self, filters: Dict[str, Any] = None, limit: int = 20) -> pd.DataFrame:
        """Get top merchants by spending."""
        if filters is None:
            filters = {}
            
        query = """
        SELECT 
            merchant,
            COUNT(*) as visit_count,
            SUM(ABS(amount)) as total_spent,
            AVG(ABS(amount)) as avg_spent_per_visit,
            MAX(ABS(amount)) as largest_purchase
        FROM transactions 
        WHERE amount < 0 AND merchant IS NOT NULL
        """
        
        params = {}
        if 'start_date' in filters:
            query += " AND date >= $start_date"
            params['start_date'] = filters['start_date']
        if 'end_date' in filters:
            query += " AND date <= $end_date"
            params['end_date'] = filters['end_date']
            
        query += " GROUP BY merchant ORDER BY total_spent DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query, params)
    
    def get_account_balances(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get account balances over time."""
        if filters is None:
            filters = {}
            
        query = """
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
        WHERE 1=1
        """
        
        params = {}
        if 'start_date' in filters:
            query += " AND date >= $start_date"
            params['start_date'] = filters['start_date']
        if 'end_date' in filters:
            query += " AND date <= $end_date"
            params['end_date'] = filters['end_date']
        if 'accounts' in filters:
            query += " AND account = ANY($accounts)"
            params['accounts'] = filters['accounts']
            
        query += " ORDER BY account, date"
        
        return self.execute_query(query, params)
    
    def detect_unusual_transactions(self, filters: Dict[str, Any] = None, 
                                  std_threshold: float = 2.0) -> pd.DataFrame:
        """Detect unusual transactions using statistical analysis."""
        if filters is None:
            filters = {}
            
        query = """
        WITH transaction_stats AS (
            SELECT 
                category,
                AVG(ABS(amount)) as avg_amount,
                STDDEV(ABS(amount)) as std_amount
            FROM transactions 
            WHERE date >= COALESCE($start_date, '1900-01-01')
                AND date <= COALESCE($end_date, '2100-01-01')
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
        WHERE t.date >= COALESCE($start_date, '1900-01-01')
            AND t.date <= COALESCE($end_date, '2100-01-01')
            AND ts.std_amount > 0
            AND ABS(t.amount - ts.avg_amount) / ts.std_amount > $std_threshold
        ORDER BY z_score DESC
        """
        
        params = {
            'std_threshold': std_threshold,
            'start_date': filters.get('start_date'),
            'end_date': filters.get('end_date')
        }
        
        return self.execute_query(query, params)
    
    def get_summary(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get comprehensive financial summary."""
        summary = {}
        
        # Basic metrics
        transaction_summary = self.get_transaction_summary(filters)
        summary['accounts'] = transaction_summary.to_dict('records')
        
        # Cash flow
        cash_flow = self.get_monthly_cash_flow(filters)
        summary['monthly_cash_flow'] = cash_flow.to_dict('records')
        
        # Categories
        categories = self.get_category_analysis(filters)
        summary['category_spending'] = categories.to_dict('records')
        
        # Calculate totals
        if not cash_flow.empty:
            summary['total_income'] = float(cash_flow['income'].sum())
            summary['total_expenses'] = float(cash_flow['expenses'].sum())
            summary['net_cash_flow'] = float(cash_flow['net_cash_flow'].sum())
        
        return summary
    
    def query_transactions(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Query transactions with filters."""
        if filters is None:
            filters = {}
            
        query = "SELECT * FROM transactions WHERE 1=1"
        params = {}
        
        if 'start_date' in filters:
            query += " AND date >= $start_date"
            params['start_date'] = filters['start_date']
        if 'end_date' in filters:
            query += " AND date <= $end_date"
            params['end_date'] = filters['end_date']
        if 'account' in filters:
            query += " AND account LIKE '%' || $account || '%'"
            params['account'] = filters['account']
        if 'category' in filters:
            query += " AND category LIKE '%' || $category || '%'"
            params['category'] = filters['category']
        if 'min_amount' in filters:
            query += " AND ABS(amount) >= $min_amount"
            params['min_amount'] = filters['min_amount']
        if 'max_amount' in filters:
            query += " AND ABS(amount) <= $max_amount"
            params['max_amount'] = filters['max_amount']
            
        query += " ORDER BY date DESC"
        
        result = self.execute_query(query, params)
        return result.to_dict('records')
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("DuckDB connection closed")