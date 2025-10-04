"""
CSV to Beancount ledger conversion.
Normalizes bank CSV data and converts to double-entry Beancount postings.
"""

import csv
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import os
import yaml

logger = logging.getLogger(__name__)

class CSVToLedgerConverter:
    """
    Converts bank CSV transactions to Beancount ledger entries.
    Uses configurable rules for account mapping and categorization.
    """
    
    def __init__(self, rules_file: str = None):
        """
        Initialize the CSV converter.
        
        Args:
            rules_file: Path to import rules YAML file
        """
        if rules_file is None:
            rules_file = os.path.join(
                os.path.dirname(__file__), '..', 'ledger', 'import_rules.yaml'
            )
        
        self.rules_file = rules_file
        self.import_rules = {}
        self._load_rules()
    
    def _load_rules(self):
        """Load import rules from YAML configuration."""
        try:
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r') as f:
                    self.import_rules = yaml.safe_load(f)
                logger.info(f"Loaded import rules from {self.rules_file}")
            else:
                logger.warning(f"Import rules file not found: {self.rules_file}")
                self._create_default_rules()
        except Exception as e:
            logger.error(f"Error loading import rules: {e}")
            self._create_default_rules()
    
    def _create_default_rules(self):
        """Create default import rules if configuration file is missing."""
        self.import_rules = {
            'default': {
                'currency': 'USD',
                'timezone': 'America/New_York'
            },
            'fallback_categories': {
                'expense': 'Expenses:Other:Miscellaneous',
                'income': 'Income:Other'
            }
        }
    
    def convert(self, csv_content: str, bank: str = 'generic', account_type: str = 'checking') -> List[Dict[str, Any]]:
        """
        Convert CSV content to Beancount entries.
        
        Args:
            csv_content: CSV file content as string
            bank: Bank identifier for rule selection
            account_type: Account type (checking, savings, credit)
            
        Returns:
            List of Beancount entry dictionaries
        """
        # Parse CSV
        transactions = self._parse_csv(csv_content, bank)
        
        # Convert to Beancount entries
        entries = []
        for transaction in transactions:
            try:
                entry = self._convert_transaction(transaction, bank, account_type)
                if entry:
                    entries.append(entry)
            except Exception as e:
                logger.error(f"Error converting transaction {transaction}: {e}")
                continue
        
        logger.info(f"Converted {len(entries)} transactions from CSV")
        return entries
    
    def _parse_csv(self, csv_content: str, bank: str) -> List[Dict[str, Any]]:
        """Parse CSV content into transaction dictionaries."""
        # Get bank-specific CSV format rules
        bank_rules = self.import_rules.get('banks', {}).get(bank, {})
        csv_format = bank_rules.get('csv_format', {})
        
        # Default column mappings
        date_column = csv_format.get('date_column', 'Date')
        amount_column = csv_format.get('amount_column', 'Amount')
        description_column = csv_format.get('description_column', 'Description')
        type_column = csv_format.get('type_column')
        
        transactions = []
        
        try:
            # Parse CSV
            reader = csv.DictReader(csv_content.splitlines())
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # Extract basic fields
                    transaction = {
                        'date': self._parse_date(row.get(date_column, ''), csv_format),
                        'amount': self._parse_amount(row.get(amount_column, '0')),
                        'description': row.get(description_column, '').strip(),
                        'type': row.get(type_column, '').strip() if type_column else '',
                        'raw_data': row
                    }
                    
                    # Skip invalid transactions
                    if not transaction['date'] or transaction['amount'] == 0:
                        continue
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    logger.warning(f"Error parsing CSV row {row_num}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            raise
        
        return transactions
    
    def _parse_date(self, date_str: str, csv_format: Dict[str, Any]) -> Optional[date]:
        """Parse date string using configured format."""
        if not date_str:
            return None
        
        date_format = csv_format.get('date_format', '%m/%d/%Y')
        
        # Try configured format first
        try:
            return datetime.strptime(date_str.strip(), date_format).date()
        except ValueError:
            pass
        
        # Try common formats
        common_formats = [
            '%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', 
            '%m-%d-%Y', '%Y/%m/%d', '%d-%m-%Y'
        ]
        
        for fmt in common_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _parse_amount(self, amount_str: str) -> Decimal:
        """Parse amount string to Decimal."""
        if not amount_str:
            return Decimal('0')
        
        # Clean amount string
        cleaned = re.sub(r'[^\d.-]', '', str(amount_str))
        
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            logger.warning(f"Could not parse amount: {amount_str}")
            return Decimal('0')
    
    def _convert_transaction(self, transaction: Dict[str, Any], bank: str, account_type: str) -> Optional[Dict[str, Any]]:
        """Convert a single transaction to Beancount entry."""
        # Determine transaction type and accounts
        transaction_type = self._determine_transaction_type(transaction, bank)
        accounts = self._determine_accounts(transaction, bank, account_type, transaction_type)
        
        if not accounts:
            return None
        
        # Create Beancount entry
        entry = {
            'date': transaction['date'],
            'flag': '*',  # Cleared transaction
            'payee': self._extract_payee(transaction),
            'narration': self._generate_narration(transaction),
            'postings': accounts,
            'meta': {
                'source': 'csv_import',
                'bank': bank,
                'raw_description': transaction['description']
            }
        }
        
        return entry
    
    def _determine_transaction_type(self, transaction: Dict[str, Any], bank: str) -> str:
        """Determine if transaction is income, expense, or transfer."""
        bank_rules = self.import_rules.get('banks', {}).get(bank, {})
        
        # Check transaction type rules
        type_rules = bank_rules.get('transaction_type_rules', [])
        transaction_type = transaction.get('type', '')
        
        for rule in type_rules:
            if rule.get('type') == transaction_type:
                return rule.get('action', 'expense')
        
        # Check amount sign rules
        amount_rules = bank_rules.get('amount_sign_rules', {})
        amount = transaction['amount']
        
        if amount < 0 and 'negative' in amount_rules:
            return amount_rules['negative']
        elif amount > 0 and 'positive' in amount_rules:
            return amount_rules['positive']
        
        # Default based on amount sign
        return 'expense' if amount < 0 else 'income'
    
    def _determine_accounts(self, transaction: Dict[str, Any], bank: str, account_type: str, trans_type: str) -> List[Dict[str, Any]]:
        """Determine account postings for double-entry bookkeeping."""
        bank_rules = self.import_rules.get('banks', {}).get(bank, {})
        account_mapping = bank_rules.get('account_mapping', {})
        
        # Get main account
        main_account = account_mapping.get(account_type, f"Assets:{account_type.title()}:{bank.title()}")
        
        # Determine category account
        category_account = self._categorize_transaction(transaction, bank)
        
        amount = abs(transaction['amount'])
        
        postings = []
        
        if trans_type == 'expense':
            # Expense: Category account debited, main account credited
            postings = [
                {
                    'account': category_account,
                    'amount': amount,
                    'currency': 'USD'
                },
                {
                    'account': main_account,
                    'amount': -amount,
                    'currency': 'USD'
                }
            ]
        elif trans_type == 'income':
            # Income: Main account debited, income account credited
            postings = [
                {
                    'account': main_account,
                    'amount': amount,
                    'currency': 'USD'
                },
                {
                    'account': category_account,
                    'amount': -amount,
                    'currency': 'USD'
                }
            ]
        
        return postings
    
    def _categorize_transaction(self, transaction: Dict[str, Any], bank: str) -> str:
        """Categorize transaction using pattern matching rules."""
        description = transaction['description'].lower()
        amount = transaction['amount']
        
        # Get bank-specific rules
        bank_rules = self.import_rules.get('banks', {}).get(bank, {})
        category_rules = bank_rules.get('category_rules', [])
        
        # Try bank-specific rules first
        for rule in category_rules:
            pattern = rule.get('pattern', '')
            if pattern and re.search(pattern, description):
                return rule.get('category', '')
        
        # Try global rules
        global_rules = self.import_rules.get('global_category_rules', [])
        for rule in global_rules:
            pattern = rule.get('pattern', '')
            if pattern and re.search(pattern, description):
                return rule.get('category', '')
        
        # Fallback to default categories
        fallback = self.import_rules.get('fallback_categories', {})
        if amount < 0:
            return fallback.get('expense', 'Expenses:Other:Miscellaneous')
        else:
            return fallback.get('income', 'Income:Other')
    
    def _extract_payee(self, transaction: Dict[str, Any]) -> str:
        """Extract payee name from transaction description."""
        description = transaction['description'].strip()
        
        # Remove common prefixes and suffixes
        description = re.sub(r'^(DEBIT|CREDIT|ACH|CHECK|DEPOSIT)\s+', '', description, flags=re.IGNORECASE)
        description = re.sub(r'\s+(DEBIT|CREDIT|ACH|CHECK|DEPOSIT)$', '', description, flags=re.IGNORECASE)
        
        # Clean up merchant names
        description = re.sub(r'\s+#\d+.*$', '', description)  # Remove location/store numbers
        description = re.sub(r'\s+\d{2}/\d{2}.*$', '', description)  # Remove dates
        description = re.sub(r'\s{2,}', ' ', description)  # Multiple spaces to single
        
        return description.title()
    
    def _generate_narration(self, transaction: Dict[str, Any]) -> str:
        """Generate human-readable narration for the transaction."""
        description = transaction['description']
        amount = abs(transaction['amount'])
        
        # Simple narration based on description
        if 'ATM' in description.upper():
            return f"ATM withdrawal - ${amount:.2f}"
        elif 'DEPOSIT' in description.upper():
            return f"Deposit - ${amount:.2f}"
        elif 'TRANSFER' in description.upper():
            return f"Account transfer - ${amount:.2f}"
        else:
            return description
    
    def to_beancount_text(self, entries: List[Dict[str, Any]]) -> str:
        """Convert entries to Beancount text format."""
        lines = []
        
        for entry in entries:
            date_str = entry['date'].strftime('%Y-%m-%d')
            flag = entry.get('flag', '*')
            payee = entry.get('payee', '')
            narration = entry.get('narration', '')
            
            # Entry header
            lines.append(f'{date_str} {flag} "{payee}" "{narration}"')
            
            # Postings
            for posting in entry.get('postings', []):
                account = posting.get('account', '')
                amount = posting.get('amount', 0)
                currency = posting.get('currency', 'USD')
                
                amount_str = f"{amount:>15.2f} {currency}" if amount != 0 else ""
                lines.append(f"  {account:<40} {amount_str}")
            
            lines.append("")  # Empty line between entries
        
        return "\n".join(lines)
    
    def to_transactions(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert Beancount entries to normalized transaction format for storage."""
        transactions = []
        
        for entry in entries:
            for posting in entry.get('postings', []):
                transaction = {
                    'date': entry['date'],
                    'account': posting.get('account', ''),
                    'amount': posting.get('amount', 0),
                    'currency': posting.get('currency', 'USD'),
                    'merchant': entry.get('payee', ''),
                    'description': entry.get('narration', ''),
                    'category': self._extract_category_from_account(posting.get('account', '')),
                    'source': 'csv_import'
                }
                transactions.append(transaction)
        
        return transactions
    
    def _extract_category_from_account(self, account: str) -> str:
        """Extract category from Beancount account name."""
        parts = account.split(':')
        if len(parts) >= 2:
            return ':'.join(parts[1:])  # Remove Assets/Liabilities/Income/Expenses prefix
        return account