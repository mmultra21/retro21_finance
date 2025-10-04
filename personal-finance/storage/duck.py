"""
DuckDB database manager for financial data storage.
Handles database initialization, connection management, and data operations.
"""

import duckdb
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pathlib import Path

logger = logging.getLogger(__name__)

class DuckDBManager:
    """
    Manages DuckDB database for financial transaction storage.
    Provides methods for database operations and schema management.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize DuckDB manager.
        
        Args:
            db_path: Path to DuckDB database file
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'duck.db')
        
        self.db_path = db_path
        self.conn = None
        self._ensure_database()
    
    def _ensure_database(self):
        """Ensure database exists and is initialized."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Connect to database
        self.conn = duckdb.connect(self.db_path)
        
        # Initialize schema if needed
        self._initialize_schema()
        
        logger.info(f"Connected to DuckDB at {self.db_path}")
    
    def _initialize_schema(self):
        """Initialize database schema if tables don't exist."""
        try:
            # Check if main table exists
            result = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'"
            ).fetchone()
            
            if not result:
                # Load and execute schema
                schema_file = os.path.join(os.path.dirname(__file__), 'init_duckdb.sql')
                if os.path.exists(schema_file):
                    with open(schema_file, 'r') as f:
                        schema_sql = f.read()
                    
                    # Execute schema (split by semicolon for multiple statements)
                    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
                    for statement in statements:
                        try:
                            self.conn.execute(statement)
                        except Exception as e:
                            logger.warning(f"Schema statement failed: {e}")
                            continue
                    
                    logger.info("Database schema initialized")
                else:
                    logger.warning(f"Schema file not found: {schema_file}")
                    
        except Exception as e:
            logger.error(f"Error initializing schema: {e}")
    
    def insert_transaction(self, transaction: Dict[str, Any]) -> str:
        """
        Insert a single transaction.
        
        Args:
            transaction: Transaction data dictionary
            
        Returns:
            Transaction ID
        """
        try:
            # Generate transaction ID if not provided
            transaction_id = transaction.get('transaction_id', self._generate_id())
            
            # Prepare data
            data = {
                'transaction_id': transaction_id,
                'date': transaction.get('date'),
                'account': transaction.get('account', ''),
                'amount': float(transaction.get('amount', 0)),
                'currency': transaction.get('currency', 'USD'),
                'merchant': transaction.get('merchant', ''),
                'description': transaction.get('description', ''),
                'category': transaction.get('category', ''),
                'transaction_type': transaction.get('transaction_type', ''),
                'check_number': transaction.get('check_number'),
                'reference_id': transaction.get('reference_id'),
                'account_type': transaction.get('account_type', ''),
                'bank_name': transaction.get('bank_name', ''),
                'is_cleared': transaction.get('is_cleared', True),
                'is_reconciled': transaction.get('is_reconciled', False),
                'source': transaction.get('source', 'manual'),
                'source_file': transaction.get('source_file'),
                'raw_data': str(transaction.get('raw_data', {}))
            }
            
            # Insert transaction
            self.conn.execute("""
                INSERT INTO transactions (
                    transaction_id, date, account, amount, currency, merchant,
                    description, category, transaction_type, check_number,
                    reference_id, account_type, bank_name, is_cleared,
                    is_reconciled, source, source_file, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                data['transaction_id'], data['date'], data['account'],
                data['amount'], data['currency'], data['merchant'],
                data['description'], data['category'], data['transaction_type'],
                data['check_number'], data['reference_id'], data['account_type'],
                data['bank_name'], data['is_cleared'], data['is_reconciled'],
                data['source'], data['source_file'], data['raw_data']
            ])
            
            logger.debug(f"Inserted transaction: {transaction_id}")
            return transaction_id
            
        except Exception as e:
            logger.error(f"Error inserting transaction: {e}")
            raise
    
    def insert_transactions(self, transactions: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple transactions in batch.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of transaction IDs
        """
        transaction_ids = []
        
        try:
            for transaction in transactions:
                transaction_id = self.insert_transaction(transaction)
                transaction_ids.append(transaction_id)
            
            logger.info(f"Inserted {len(transaction_ids)} transactions")
            return transaction_ids
            
        except Exception as e:
            logger.error(f"Error inserting transactions: {e}")
            raise
    
    def get_transactions(self, 
                        start_date: Optional[date] = None,
                        end_date: Optional[date] = None,
                        account: Optional[str] = None,
                        category: Optional[str] = None,
                        limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve transactions with optional filters.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            account: Account filter
            category: Category filter
            limit: Maximum number of results
            
        Returns:
            List of transaction dictionaries
        """
        try:
            query = "SELECT * FROM transactions WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            if account:
                query += " AND account LIKE ?"
                params.append(f"%{account}%")
            
            if category:
                query += " AND category LIKE ?"
                params.append(f"%{category}%")
            
            query += " ORDER BY date DESC, created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            result = self.conn.execute(query, params).fetchdf()
            return result.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error retrieving transactions: {e}")
            raise
    
    def get_account_balance(self, account: str, as_of_date: Optional[date] = None) -> float:
        """
        Get account balance as of a specific date.
        
        Args:
            account: Account name
            as_of_date: Date to calculate balance (default: latest)
            
        Returns:
            Account balance
        """
        try:
            query = "SELECT SUM(amount) as balance FROM transactions WHERE account = ?"
            params = [account]
            
            if as_of_date:
                query += " AND date <= ?"
                params.append(as_of_date)
            
            result = self.conn.execute(query, params).fetchone()
            return float(result[0]) if result[0] else 0.0
            
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return 0.0
    
    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """
        Get monthly financial summary.
        
        Args:
            year: Year
            month: Month
            
        Returns:
            Monthly summary data
        """
        try:
            # Get income and expenses
            summary_query = """
                SELECT 
                    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses,
                    SUM(amount) as net_cash_flow,
                    COUNT(*) as transaction_count
                FROM transactions 
                WHERE year = ? AND month = ?
            """
            
            summary = self.conn.execute(summary_query, [year, month]).fetchone()
            
            # Get category breakdown
            category_query = """
                SELECT 
                    category,
                    transaction_type,
                    COUNT(*) as count,
                    SUM(ABS(amount)) as total
                FROM transactions 
                WHERE year = ? AND month = ? AND category IS NOT NULL
                GROUP BY category, transaction_type
                ORDER BY total DESC
            """
            
            categories = self.conn.execute(category_query, [year, month]).fetchdf()
            
            return {
                'year': year,
                'month': month,
                'income': float(summary[0]) if summary[0] else 0.0,
                'expenses': float(summary[1]) if summary[1] else 0.0,
                'net_cash_flow': float(summary[2]) if summary[2] else 0.0,
                'transaction_count': int(summary[3]) if summary[3] else 0,
                'categories': categories.to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error getting monthly summary: {e}")
            return {}
    
    def get_category_totals(self, 
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Get category totals for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of category totals
        """
        try:
            query = """
                SELECT 
                    category,
                    transaction_type,
                    COUNT(*) as transaction_count,
                    SUM(ABS(amount)) as total_amount,
                    AVG(ABS(amount)) as avg_amount
                FROM transactions 
                WHERE category IS NOT NULL
            """
            
            params = []
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            query += " GROUP BY category, transaction_type ORDER BY total_amount DESC"
            
            result = self.conn.execute(query, params).fetchdf()
            return result.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error getting category totals: {e}")
            return []
    
    def log_import(self, log_data: Dict[str, Any]) -> str:
        """
        Log an import operation.
        
        Args:
            log_data: Import log data
            
        Returns:
            Log ID
        """
        try:
            log_id = log_data.get('log_id', self._generate_id())
            
            self.conn.execute("""
                INSERT INTO import_logs (
                    log_id, source_type, source_file, bank_name, account_name,
                    records_processed, records_imported, records_failed,
                    status, error_message, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                log_id,
                log_data.get('source_type', ''),
                log_data.get('source_file', ''),
                log_data.get('bank_name', ''),
                log_data.get('account_name', ''),
                log_data.get('records_processed', 0),
                log_data.get('records_imported', 0),
                log_data.get('records_failed', 0),
                log_data.get('status', 'completed'),
                log_data.get('error_message', ''),
                str(log_data.get('metadata', {}))
            ])
            
            return log_id
            
        except Exception as e:
            logger.error(f"Error logging import: {e}")
            raise
    
    def _generate_id(self) -> str:
        """Generate a unique ID."""
        import uuid
        return str(uuid.uuid4())
    
    def execute_query(self, query: str, params: List[Any] = None) -> Any:
        """
        Execute a custom query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Query result
        """
        try:
            if params:
                return self.conn.execute(query, params)
            else:
                return self.conn.execute(query)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("DuckDB connection closed")