"""
Form validation and data formatting utilities.
Handles field validation, data masking, currency formatting, and business rules.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

class FormValidator:
    """
    Validates form data against rules and constraints.
    Handles field formats, required fields, and business logic validation.
    """
    
    def __init__(self):
        """Initialize the form validator."""
        self.validation_errors = []
    
    def validate(self, data: Dict[str, Any], rules: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate form data against provided rules.
        
        Args:
            data: Form data to validate
            rules: Validation rules configuration
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        self.validation_errors = []
        
        # Validate required fields
        self._validate_required_fields(data, rules.get('required_fields', []))
        
        # Validate field formats
        self._validate_field_formats(data, rules.get('field_formats', {}))
        
        # Validate business rules
        self._validate_business_rules(data, rules.get('business_rules', []))
        
        return len(self.validation_errors) == 0, self.validation_errors
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]):
        """Validate that all required fields are present and not empty."""
        for field_path in required_fields:
            value = self._get_nested_value(data, field_path)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                self.validation_errors.append(f"Required field missing: {field_path}")
    
    def _validate_field_formats(self, data: Dict[str, Any], format_rules: Dict[str, Any]):
        """Validate field formats against regex patterns."""
        for field_path, rules in format_rules.items():
            value = self._get_nested_value(data, field_path)
            if value is None:
                continue
                
            pattern = rules.get('pattern')
            if pattern and not re.match(pattern, str(value)):
                message = rules.get('message', f"Invalid format for {field_path}")
                self.validation_errors.append(message)
    
    def _validate_business_rules(self, data: Dict[str, Any], business_rules: List[Dict[str, str]]):
        """Validate business logic rules."""
        for rule in business_rules:
            rule_expression = rule.get('rule', '')
            if not self._evaluate_rule(data, rule_expression):
                message = rule.get('message', f"Business rule violation: {rule_expression}")
                self.validation_errors.append(message)
    
    def _evaluate_rule(self, data: Dict[str, Any], rule: str) -> bool:
        """Evaluate a business rule expression."""
        # Handle common comparison operators
        operators = ['<=', '>=', '<', '>', '==', '!=']
        
        for op in operators:
            if op in rule:
                left, right = rule.split(op, 1)
                left_val = self._get_rule_value(data, left.strip())
                right_val = self._get_rule_value(data, right.strip())
                
                try:
                    if op == '<=':
                        return float(left_val or 0) <= float(right_val or 0)
                    elif op == '>=':
                        return float(left_val or 0) >= float(right_val or 0)
                    elif op == '<':
                        return float(left_val or 0) < float(right_val or 0)
                    elif op == '>':
                        return float(left_val or 0) > float(right_val or 0)
                    elif op == '==':
                        return str(left_val or '') == str(right_val or '')
                    elif op == '!=':
                        return str(left_val or '') != str(right_val or '')
                except (ValueError, TypeError):
                    return False
        
        return True
    
    def _get_rule_value(self, data: Dict[str, Any], expression: str) -> Any:
        """Get value for rule evaluation (supports nested paths and literals)."""
        expression = expression.strip()
        
        # Check if it's a number literal
        try:
            return float(expression)
        except ValueError:
            pass
        
        # Check if it's a string literal
        if expression.startswith('"') and expression.endswith('"'):
            return expression[1:-1]
        
        # Otherwise, treat as data path
        return self._get_nested_value(data, expression)
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        if not path:
            return None
            
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value

class DataFormatter:
    """
    Formats and masks data for form display and privacy.
    Handles currency, phone numbers, SSN masking, etc.
    """
    
    @staticmethod
    def format_currency(amount: Union[str, int, float, Decimal], 
                       show_cents: bool = True,
                       currency_symbol: str = "$") -> str:
        """
        Format amount as currency.
        
        Args:
            amount: Amount to format
            show_cents: Whether to show decimal places
            currency_symbol: Currency symbol to use
            
        Returns:
            Formatted currency string
        """
        try:
            decimal_amount = Decimal(str(amount))
            if show_cents:
                formatted = f"{decimal_amount:,.2f}"
            else:
                formatted = f"{decimal_amount:,.0f}"
            return f"{currency_symbol}{formatted}"
        except (InvalidOperation, ValueError):
            return f"{currency_symbol}0.00" if show_cents else f"{currency_symbol}0"
    
    @staticmethod
    def format_phone(phone: str, format_style: str = "(xxx) xxx-xxxx") -> str:
        """
        Format phone number.
        
        Args:
            phone: Phone number to format
            format_style: Format pattern
            
        Returns:
            Formatted phone number
        """
        # Extract digits only
        digits = re.sub(r'\D', '', str(phone))
        
        if len(digits) == 10:
            if format_style == "(xxx) xxx-xxxx":
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif format_style == "xxx-xxx-xxxx":
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            elif format_style == "xxx.xxx.xxxx":
                return f"{digits[:3]}.{digits[3:6]}.{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            # Handle +1 country code
            return DataFormatter.format_phone(digits[1:], format_style)
        
        return phone  # Return original if can't format
    
    @staticmethod
    def mask_ssn(ssn: str, mask_pattern: str = "xxx-xx-xxxx") -> str:
        """
        Mask Social Security Number for privacy.
        
        Args:
            ssn: SSN to mask
            mask_pattern: Masking pattern
            
        Returns:
            Masked SSN
        """
        digits = re.sub(r'\D', '', str(ssn))
        
        if len(digits) == 9:
            if mask_pattern == "xxx-xx-xxxx":
                return f"xxx-xx-{digits[-4:]}"
            elif mask_pattern == "***-**-xxxx":
                return f"***-**-{digits[-4:]}"
            elif mask_pattern == "xxx-xx-****":
                return f"{digits[:3]}-{digits[3:5]}-****"
        
        return ssn  # Return original if can't mask
    
    @staticmethod
    def format_date(date_value: Union[str, datetime, date], 
                   format_style: str = "%m/%d/%Y") -> str:
        """
        Format date value.
        
        Args:
            date_value: Date to format
            format_style: Date format string
            
        Returns:
            Formatted date string
        """
        if isinstance(date_value, str):
            # Try to parse string date
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                try:
                    date_value = datetime.strptime(date_value, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                return str(date_value)  # Return original if can't parse
        
        if isinstance(date_value, datetime):
            date_value = date_value.date()
        
        if isinstance(date_value, date):
            return date_value.strftime(format_style)
        
        return str(date_value)
    
    @staticmethod
    def format_percentage(value: Union[str, int, float], decimal_places: int = 1) -> str:
        """
        Format value as percentage.
        
        Args:
            value: Value to format (0.15 = 15%)
            decimal_places: Number of decimal places
            
        Returns:
            Formatted percentage string
        """
        try:
            percentage = float(value) * 100
            return f"{percentage:.{decimal_places}f}%"
        except (ValueError, TypeError):
            return "0.0%"
    
    @staticmethod
    def clean_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Clean and normalize text input.
        
        Args:
            text: Text to clean
            max_length: Maximum length to truncate to
            
        Returns:
            Cleaned text
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length].strip()
        
        return text

class FieldCalculator:
    """
    Performs calculations for computed form fields.
    Handles totals, percentages, and derived values.
    """
    
    @staticmethod
    def calculate_total_income(data: Dict[str, Any]) -> float:
        """Calculate total monthly income."""
        income_fields = [
            'income.gross_monthly_wages',
            'income.other_monthly',
            'income.spouse_wages',
            'income.investment_income',
            'income.rental_income'
        ]
        
        total = 0.0
        for field_path in income_fields:
            value = FieldCalculator._get_nested_value(data, field_path)
            if value:
                try:
                    total += float(value)
                except (ValueError, TypeError):
                    continue
        
        return total
    
    @staticmethod
    def calculate_total_expenses(data: Dict[str, Any]) -> float:
        """Calculate total monthly expenses."""
        expense_fields = [
            'expenses.housing.rent_mortgage',
            'expenses.housing.utilities',
            'expenses.food.total',
            'expenses.transportation.total',
            'expenses.insurance.total',
            'expenses.medical.total',
            'expenses.other.total'
        ]
        
        total = 0.0
        for field_path in expense_fields:
            value = FieldCalculator._get_nested_value(data, field_path)
            if value:
                try:
                    total += float(value)
                except (ValueError, TypeError):
                    continue
        
        return total
    
    @staticmethod
    def calculate_net_cash_flow(data: Dict[str, Any]) -> float:
        """Calculate net monthly cash flow."""
        income = FieldCalculator.calculate_total_income(data)
        expenses = FieldCalculator.calculate_total_expenses(data)
        return income - expenses
    
    @staticmethod
    def calculate_total_assets(data: Dict[str, Any]) -> float:
        """Calculate total asset value."""
        asset_fields = [
            'assets.cash.checking_total',
            'assets.cash.savings_total',
            'assets.investments.total',
            'assets.real_estate.total',
            'assets.vehicles.total'
        ]
        
        total = 0.0
        for field_path in asset_fields:
            value = FieldCalculator._get_nested_value(data, field_path)
            if value:
                try:
                    total += float(value)
                except (ValueError, TypeError):
                    continue
        
        return total
    
    @staticmethod
    def calculate_total_liabilities(data: Dict[str, Any]) -> float:
        """Calculate total liability value."""
        liability_fields = [
            'liabilities.credit_cards.total',
            'liabilities.student_loans.total',
            'liabilities.auto_loans.total',
            'liabilities.mortgage.balance',
            'liabilities.other.total'
        ]
        
        total = 0.0
        for field_path in liability_fields:
            value = FieldCalculator._get_nested_value(data, field_path)
            if value:
                try:
                    total += float(value)
                except (ValueError, TypeError):
                    continue
        
        return total
    
    @staticmethod
    def calculate_net_worth(data: Dict[str, Any]) -> float:
        """Calculate net worth (assets - liabilities)."""
        assets = FieldCalculator.calculate_total_assets(data)
        liabilities = FieldCalculator.calculate_total_liabilities(data)
        return assets - liabilities
    
    @staticmethod
    def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value