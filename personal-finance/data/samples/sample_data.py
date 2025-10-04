# Sample Form Data for Testing
# This file contains sample data for testing form filling functionality

sample_433a_data = {
    "taxpayer": {
        "full_name": "John Doe",
        "ssn": "123-45-6789"
    },
    "spouse": {
        "full_name": "Jane Doe",
        "ssn": "987-65-4321"
    },
    "address": {
        "line1": "123 Main Street",
        "line2": "Apt 4B",
        "city": "Anytown",
        "state": "CA",
        "zip": "12345"
    },
    "contact": {
        "phone_home": "(555) 123-4567",
        "phone_work": "(555) 987-6543",
        "email": "john.doe@email.com"
    },
    "employment": {
        "employer_name": "ABC Corporation",
        "employer_address": "456 Business Ave, Anytown, CA 12345",
        "occupation": "Software Engineer",
        "work_phone": "(555) 111-2222",
        "pay_frequency": "Bi-weekly"
    },
    "income": {
        "gross_monthly_wages": 8500.00,
        "net_monthly_wages": 6200.00,
        "other_monthly": 500.00,
        "total_monthly": 9000.00
    },
    "expenses": {
        "housing": {
            "rent_mortgage": 2500.00,
            "utilities": 350.00
        },
        "food": {
            "total": 800.00
        },
        "transportation": {
            "total": 600.00
        },
        "insurance": {
            "total": 450.00
        },
        "medical": {
            "total": 200.00
        },
        "other": {
            "total": 300.00
        },
        "total_monthly": 5200.00
    },
    "assets": {
        "cash": {
            "checking_total": 15000.00,
            "savings_total": 25000.00
        },
        "investments": {
            "total": 75000.00
        },
        "real_estate": {
            "total": 350000.00
        },
        "vehicles": {
            "total": 25000.00
        }
    },
    "liabilities": {
        "credit_cards": {
            "total": 5000.00
        },
        "student_loans": {
            "total": 15000.00
        },
        "auto_loans": {
            "total": 20000.00
        },
        "mortgage": {
            "balance": 280000.00
        },
        "other": {
            "total": 0.00
        }
    }
}

# Sample transaction data for testing
sample_transactions = [
    {
        "date": "2024-01-15",
        "amount": -125.67,
        "merchant": "Grocery Store Inc",
        "description": "Weekly grocery shopping",
        "category": "Expenses:Food:Groceries",
        "account": "Assets:Checking:MainBank"
    },
    {
        "date": "2024-01-16", 
        "amount": 3500.00,
        "merchant": "ABC Corporation",
        "description": "Salary deposit",
        "category": "Income:Salary:Primary",
        "account": "Assets:Checking:MainBank"
    },
    {
        "date": "2024-01-17",
        "amount": -45.23,
        "merchant": "Gas Station",
        "description": "Vehicle fuel",
        "category": "Expenses:Transportation:Gas",
        "account": "Assets:Checking:MainBank"
    },
    {
        "date": "2024-01-18",
        "amount": -89.34,
        "merchant": "Electric Company",
        "description": "Monthly electric bill",
        "category": "Expenses:Housing:Utilities",
        "account": "Assets:Checking:MainBank"
    },
    {
        "date": "2024-01-20",
        "amount": -5.67,
        "merchant": "Starbucks",
        "description": "Coffee",
        "category": "Expenses:Food:Coffee",
        "account": "Assets:Checking:MainBank"
    }
]