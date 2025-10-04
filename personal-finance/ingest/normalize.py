"""
Data normalization utilities for financial transactions.
Cleans dates, amounts, merchant names, and other transaction data.
"""

import re
import logging
from typing import Union, Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

class DataNormalizer:
    """
    Normalizes and cleans financial transaction data.
    Handles dates, amounts, merchant names, and descriptions.
    """
    
    @staticmethod
    def normalize_date(date_input: Union[str, datetime, date], 
                      input_format: Optional[str] = None) -> Optional[date]:
        """
        Normalize various date formats to a standard date object.
        
        Args:
            date_input: Date in various formats
            input_format: Expected input format (optional)
            
        Returns:
            Normalized date object or None if invalid
        """
        if date_input is None:
            return None
        
        if isinstance(date_input, date):
            return date_input
        
        if isinstance(date_input, datetime):
            return date_input.date()
        
        if not isinstance(date_input, str):
            date_input = str(date_input)
        
        date_str = date_input.strip()
        if not date_str:
            return None
        
        # Try specific format first if provided
        if input_format:
            try:
                return datetime.strptime(date_str, input_format).date()
            except ValueError:
                pass
        
        # Common date formats to try
        formats = [
            '%Y-%m-%d',           # 2024-01-15
            '%m/%d/%Y',           # 01/15/2024
            '%d/%m/%Y',           # 15/01/2024
            '%m-%d-%Y',           # 01-15-2024
            '%d-%m-%Y',           # 15-01-2024
            '%Y/%m/%d',           # 2024/01/15
            '%m/%d/%y',           # 01/15/24
            '%d/%m/%y',           # 15/01/24
            '%b %d, %Y',          # Jan 15, 2024
            '%B %d, %Y',          # January 15, 2024
            '%d %b %Y',           # 15 Jan 2024
            '%d %B %Y',           # 15 January 2024
            '%Y-%m-%d %H:%M:%S',  # 2024-01-15 10:30:00
            '%m/%d/%Y %H:%M:%S',  # 01/15/2024 10:30:00
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_input}")
        return None
    
    @staticmethod
    def normalize_amount(amount_input: Union[str, int, float, Decimal]) -> Decimal:
        """
        Normalize various amount formats to a standard Decimal.
        
        Args:
            amount_input: Amount in various formats
            
        Returns:
            Normalized Decimal amount
        """
        if amount_input is None:
            return Decimal('0')
        
        if isinstance(amount_input, Decimal):
            return amount_input
        
        if isinstance(amount_input, (int, float)):
            return Decimal(str(amount_input))
        
        if not isinstance(amount_input, str):
            amount_input = str(amount_input)
        
        # Clean the amount string
        amount_str = amount_input.strip()
        
        # Remove currency symbols and formatting
        amount_str = re.sub(r'[$€£¥₹]', '', amount_str)  # Currency symbols
        amount_str = re.sub(r'[,\s]', '', amount_str)    # Commas and spaces
        amount_str = re.sub(r'[()]+', '', amount_str)    # Parentheses
        
        # Handle negative amounts in parentheses (accounting format)
        is_negative = False
        if amount_input.strip().startswith('(') and amount_input.strip().endswith(')'):
            is_negative = True
        
        # Extract numeric part
        amount_str = re.sub(r'[^\d.-]', '', amount_str)
        
        if not amount_str:
            return Decimal('0')
        
        try:
            amount = Decimal(amount_str)
            return -amount if is_negative else amount
        except InvalidOperation:
            logger.warning(f"Could not parse amount: {amount_input}")
            return Decimal('0')
    
    @staticmethod
    def normalize_merchant(merchant_input: str) -> str:
        """
        Clean and normalize merchant/payee names.
        
        Args:
            merchant_input: Raw merchant name from bank
            
        Returns:
            Cleaned merchant name
        """
        if not merchant_input:
            return ""
        
        merchant = str(merchant_input).strip()
        
        # Remove common prefixes
        prefixes = [
            r'^(DEBIT|CREDIT|ACH|CHECK|DEPOSIT|TRANSFER|PAYMENT)\s+',
            r'^(SQ\s*\*|SQUARE\s*\*)',  # Square payment processor
            r'^(PAYPAL\s*\*|PP\s*\*)',  # PayPal
            r'^(AMZN\s+MKTP\s+)',       # Amazon Marketplace
            r'^(TST\s*\*|TOAST\s*\*)', # Toast POS
        ]
        
        for prefix in prefixes:
            merchant = re.sub(prefix, '', merchant, flags=re.IGNORECASE)
        
        # Remove common suffixes
        suffixes = [
            r'\s+(DEBIT|CREDIT|ACH|CHECK|DEPOSIT|TRANSFER|PAYMENT)$',
            r'\s+\d{2}/\d{2}(/\d{2,4})?$',  # Dates
            r'\s+#\d+.*$',                   # Store/location numbers
            r'\s+\d{10,}.*$',               # Transaction IDs
            r'\s+[A-Z]{2,3}\s*$',           # State/country codes
        ]
        
        for suffix in suffixes:
            merchant = re.sub(suffix, '', merchant, flags=re.IGNORECASE)
        
        # Clean up specific patterns
        merchant = re.sub(r'\*+', '', merchant)  # Remove asterisks
        merchant = re.sub(r'\s{2,}', ' ', merchant)  # Multiple spaces to single
        merchant = re.sub(r'^[-\s]+|[-\s]+$', '', merchant)  # Leading/trailing dashes/spaces
        
        # Normalize common merchants
        normalizations = {
            r'WALMART.*SUPER.*CENTER': 'Walmart Supercenter',
            r'WALMART.*': 'Walmart',
            r'TARGET\s+T-?\d+': 'Target',
            r'STARBUCKS.*': 'Starbucks',
            r'MCDONALD.*': 'McDonald\'s',
            r'SHELL\s+OIL.*': 'Shell',
            r'EXXONMOBIL.*': 'ExxonMobil',
            r'CHEVRON.*': 'Chevron',
            r'BP\s+#?\d+': 'BP',
            r'COSTCO.*': 'Costco',
            r'HOME\s+DEPOT.*': 'Home Depot',
            r'LOWES.*': 'Lowe\'s',
            r'AMAZON.*': 'Amazon',
            r'NETFLIX.*': 'Netflix',
            r'SPOTIFY.*': 'Spotify',
        }
        
        for pattern, replacement in normalizations.items():
            if re.search(pattern, merchant, re.IGNORECASE):
                merchant = replacement
                break
        
        # Final cleanup
        merchant = ' '.join(word.capitalize() for word in merchant.split())
        
        return merchant
    
    @staticmethod
    def normalize_description(description_input: str, max_length: int = 200) -> str:
        """
        Clean and normalize transaction descriptions.
        
        Args:
            description_input: Raw transaction description
            max_length: Maximum length for description
            
        Returns:
            Cleaned description
        """
        if not description_input:
            return ""
        
        description = str(description_input).strip()
        
        # Remove excessive whitespace
        description = re.sub(r'\s+', ' ', description)
        
        # Remove special characters that don't add value
        description = re.sub(r'[*#]{2,}', '', description)
        description = re.sub(r'^[-=]+|[-=]+$', '', description)
        
        # Truncate if too long
        if len(description) > max_length:
            description = description[:max_length].strip()
        
        return description
    
    @staticmethod
    def normalize_account_number(account_input: str) -> str:
        """
        Normalize account numbers (mask for privacy).
        
        Args:
            account_input: Raw account number
            
        Returns:
            Masked account number
        """
        if not account_input:
            return ""
        
        account = re.sub(r'\D', '', str(account_input))  # Keep only digits
        
        if len(account) >= 4:
            return f"****{account[-4:]}"
        else:
            return "****"
    
    @staticmethod
    def normalize_category(category_input: str) -> str:
        """
        Normalize expense/income categories.
        
        Args:
            category_input: Raw category
            
        Returns:
            Normalized category
        """
        if not category_input:
            return "Other:Miscellaneous"
        
        category = str(category_input).strip()
        
        # Convert to title case
        parts = category.split(':')
        normalized_parts = []
        
        for part in parts:
            # Clean and capitalize each part
            clean_part = re.sub(r'[^\w\s]', '', part).strip()
            if clean_part:
                normalized_parts.append(clean_part.title())
        
        if not normalized_parts:
            return "Other:Miscellaneous"
        
        return ':'.join(normalized_parts)
    
    @staticmethod
    def detect_transaction_type(description: str, amount: Decimal) -> str:
        """
        Detect transaction type from description and amount.
        
        Args:
            description: Transaction description
            amount: Transaction amount
            
        Returns:
            Transaction type: 'income', 'expense', 'transfer'
        """
        desc_lower = description.lower()
        
        # Transfer indicators
        transfer_keywords = [
            'transfer', 'xfer', 'online banking transfer',
            'account to account', 'internal transfer'
        ]
        
        if any(keyword in desc_lower for keyword in transfer_keywords):
            return 'transfer'
        
        # Income indicators
        income_keywords = [
            'deposit', 'payroll', 'salary', 'wages', 'bonus',
            'dividend', 'interest', 'refund', 'credit', 'direct dep'
        ]
        
        if any(keyword in desc_lower for keyword in income_keywords):
            return 'income'
        
        # Fee indicators (always expense regardless of amount)
        fee_keywords = [
            'fee', 'charge', 'penalty', 'overdraft', 'nsf',
            'service charge', 'maintenance fee'
        ]
        
        if any(keyword in desc_lower for keyword in fee_keywords):
            return 'expense'
        
        # Default based on amount sign
        return 'expense' if amount < 0 else 'income'
    
    @staticmethod
    def standardize_phone(phone_input: str) -> str:
        """
        Standardize phone number format.
        
        Args:
            phone_input: Raw phone number
            
        Returns:
            Standardized phone number
        """
        if not phone_input:
            return ""
        
        # Extract digits only
        digits = re.sub(r'\D', '', str(phone_input))
        
        # Handle different lengths
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone_input  # Return original if can't standardize
    
    @staticmethod
    def validate_and_normalize_transaction(raw_transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize a complete transaction record.
        
        Args:
            raw_transaction: Raw transaction data
            
        Returns:
            Normalized transaction data
        """
        normalized = {}
        
        # Normalize each field
        normalized['date'] = DataNormalizer.normalize_date(
            raw_transaction.get('date')
        )
        
        normalized['amount'] = DataNormalizer.normalize_amount(
            raw_transaction.get('amount')
        )
        
        normalized['merchant'] = DataNormalizer.normalize_merchant(
            raw_transaction.get('merchant', raw_transaction.get('description', ''))
        )
        
        normalized['description'] = DataNormalizer.normalize_description(
            raw_transaction.get('description', '')
        )
        
        normalized['category'] = DataNormalizer.normalize_category(
            raw_transaction.get('category', '')
        )
        
        # Detect transaction type if not provided
        if 'type' not in raw_transaction or not raw_transaction['type']:
            normalized['type'] = DataNormalizer.detect_transaction_type(
                normalized['description'], normalized['amount']
            )
        else:
            normalized['type'] = raw_transaction['type']
        
        # Copy other fields as-is
        for key, value in raw_transaction.items():
            if key not in normalized:
                normalized[key] = value
        
        return normalized