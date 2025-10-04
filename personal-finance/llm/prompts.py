"""
Prompt templates for LLM interactions.
Focuses on narration-only tasks - no mathematical calculations.
"""

from typing import Optional, Dict

def get_categorization_prompt(merchant: str, amount: float, description: str = "") -> str:
    """
    Generate prompt for transaction categorization.
    
    Args:
        merchant: Merchant name
        amount: Transaction amount
        description: Additional description
        
    Returns:
        Formatted prompt string
    """
    
    amount_str = "expense" if amount < 0 else "income"
    abs_amount = abs(amount)
    
    prompt = f"""You are a financial assistant that categorizes transactions. Based on the merchant name and context, suggest the most appropriate expense category.

Transaction Details:
- Merchant: {merchant}
- Type: {amount_str}
- Amount: ${abs_amount:.2f}"""
    
    if description:
        prompt += f"\n- Description: {description}"
    
    prompt += """

Common Categories:
- Food:Groceries, Food:Restaurants, Food:Coffee
- Transportation:Gas, Transportation:Public, Transportation:Maintenance
- Housing:Rent, Housing:Utilities, Housing:Internet, Housing:Insurance
- Health:Medical, Health:Dental, Health:Pharmacy
- Entertainment:Movies, Entertainment:Streaming, Entertainment:Books
- Shopping:Clothing, Shopping:Electronics, Shopping:Personal
- Financial:Fees, Financial:Interest
- Income:Salary, Income:Freelance, Income:Other

Based on the merchant name, suggest the most appropriate category (use format like "Food:Groceries"):
Category:"""

    return prompt

def get_narration_prompt(merchant: str, amount: float, category: str, 
                        date: str = "", description: str = "") -> str:
    """
    Generate prompt for transaction narration.
    
    Args:
        merchant: Merchant name
        amount: Transaction amount
        category: Transaction category
        date: Transaction date
        description: Additional description
        
    Returns:
        Formatted prompt string
    """
    
    amount_str = f"${abs(amount):.2f}"
    action = "spent" if amount < 0 else "received"
    
    prompt = f"""You are a financial assistant that creates natural, concise descriptions for transactions. Write a brief, human-readable narration for this transaction.

Transaction Details:
- Merchant: {merchant}
- Amount: {amount_str} ({action})
- Category: {category}"""
    
    if date:
        prompt += f"\n- Date: {date}"
    if description:
        prompt += f"\n- Description: {description}"
    
    prompt += f"""

Write a brief, natural description of this transaction (max 10 words). Examples:
- "Weekly grocery shopping at Safeway"
- "Coffee with friends at Starbucks"
- "Monthly electric bill payment"
- "Salary deposit from employer"

Narration:"""

    return prompt

def get_merchant_cleanup_prompt(merchant: str) -> str:
    """
    Generate prompt for cleaning up merchant names.
    
    Args:
        merchant: Raw merchant name from bank
        
    Returns:
        Formatted prompt string
    """
    
    prompt = f"""You are a financial assistant that cleans up messy merchant names from bank transactions. Convert the raw bank description into a clean, readable merchant name.

Raw merchant name: {merchant}

Guidelines:
- Remove transaction codes, reference numbers, and timestamps
- Remove excessive punctuation and special characters
- Keep the core business name
- Use proper capitalization
- Remove location codes unless they're part of the name

Examples:
- "WALMART SUPERCENTER #1234 ANYTOWN US" → "Walmart Supercenter"
- "SQ *COFFEE SHOP 123 MAIN" → "Coffee Shop"
- "AMZN MKTP US*123456789" → "Amazon"
- "SHELL OIL 12345678901" → "Shell"

Clean merchant name:"""

    return prompt

def get_spending_pattern_prompt(category: str, amount: float, frequency: int, period: str) -> str:
    """
    Generate prompt for explaining spending patterns.
    
    Args:
        category: Spending category
        amount: Total amount spent
        frequency: Number of transactions
        period: Time period
        
    Returns:
        Formatted prompt string
    """
    
    prompt = f"""You are a financial advisor analyzing spending patterns. Provide a brief, helpful observation about this spending pattern.

Spending Pattern:
- Category: {category}
- Total spent: ${amount:.2f}
- Transactions: {frequency} times
- Period: {period}

Write a brief analysis of this spending pattern. Focus on:
- Whether this seems reasonable for the category
- Any notable observations about frequency or amount
- Simple, actionable insights if relevant

Keep it concise and helpful (2-3 sentences max). Examples:
- "Your grocery spending shows consistent weekly shopping habits, which is great for budgeting."
- "Frequent small coffee purchases add up - consider brewing at home to save money."
- "Restaurant spending is higher than average - cooking more meals at home could help reduce costs."

Analysis:"""

    return prompt

def get_budget_analysis_prompt(category: str, spent: float, budgeted: float, period: str) -> str:
    """
    Generate prompt for budget vs actual analysis.
    
    Args:
        category: Spending category
        spent: Amount actually spent
        budgeted: Budgeted amount
        period: Time period
        
    Returns:
        Formatted prompt string
    """
    
    over_under = "over" if spent > budgeted else "under"
    variance = abs(spent - budgeted)
    percentage = (variance / budgeted * 100) if budgeted > 0 else 0
    
    prompt = f"""You are a financial advisor analyzing budget performance. Provide helpful feedback on this budget category.

Budget Analysis:
- Category: {category}
- Budgeted: ${budgeted:.2f}
- Actual spent: ${spent:.2f}
- Variance: ${variance:.2f} {over_under} budget ({percentage:.1f}%)
- Period: {period}

Provide brief, actionable feedback about this budget performance. Consider:
- Whether the variance is significant
- Possible reasons for over/under spending
- Practical suggestions for improvement

Keep it helpful and concise (2-3 sentences). Examples:
- "Great job staying under budget! Consider reallocating some savings to other categories."
- "Slightly over budget due to one large purchase - normal variation for this category."
- "Significantly over budget - review recent transactions and consider ways to reduce spending."

Feedback:"""

    return prompt

def get_financial_summary_prompt(income: float, expenses: float, period: str) -> str:
    """
    Generate prompt for financial summary narration.
    
    Args:
        income: Total income
        expenses: Total expenses
        period: Time period
        
    Returns:
        Formatted prompt string
    """
    
    net = income - expenses
    savings_rate = (net / income * 100) if income > 0 else 0
    
    prompt = f"""You are a financial advisor creating a summary of financial performance. Write a brief, encouraging summary.

Financial Summary for {period}:
- Total income: ${income:.2f}
- Total expenses: ${expenses:.2f}
- Net savings: ${net:.2f}
- Savings rate: {savings_rate:.1f}%

Write a brief, positive summary of this financial performance. Include:
- Overall assessment of the savings rate
- Any notable achievements or concerns
- Encouraging tone with actionable insights

Keep it motivating and helpful (3-4 sentences). Examples:
- "Excellent financial discipline this month with a 20% savings rate! Your consistent budgeting is paying off."
- "Solid progress with positive cash flow despite some unexpected expenses. Consider building an emergency fund."
- "Income exceeded expenses, showing good financial control. Small improvements in spending could boost savings further."

Summary:"""

    return prompt

def get_narrative_templates() -> Dict[str, str]:
    """
    Get predefined narrative templates for different financial scenarios.
    Templates use {facts} placeholder that gets replaced with structured data.
    
    Returns:
        Dictionary of template names and their prompts
    """
    
    templates = {
        "monthly_summary": """You are a financial advisor providing a friendly monthly summary. Based on the financial data below, write a conversational 2-3 paragraph summary that highlights key insights and provides encouragement.

Financial Data:
{facts}

Write a personalized monthly financial summary that:
- Acknowledges achievements and positive trends
- Identifies areas for improvement without being judgmental
- Provides 1-2 specific, actionable recommendations
- Uses an encouraging, supportive tone
- Keeps it conversational and easy to understand

Summary:""",

        "spending_insights": """You are a financial coach analyzing spending patterns. Based on the spending data below, provide helpful insights in a friendly, non-judgmental tone.

Spending Data:
{facts}

Write a spending analysis that:
- Highlights interesting patterns or trends
- Compares spending across categories
- Identifies potential areas for optimization
- Suggests practical tips for improvement
- Maintains an encouraging, helpful tone

Analysis:""",

        "budget_performance": """You are a personal finance assistant reviewing budget performance. Based on the budget vs actual data below, provide constructive feedback.

Budget Performance:
{facts}

Write a budget review that:
- Celebrates categories where you stayed on track
- Addresses overspending with understanding and practical advice
- Suggests realistic adjustments for next month
- Focuses on progress rather than perfection
- Provides specific, actionable next steps

Review:""",

        "cash_flow_story": """You are a financial storyteller. Based on the cash flow data below, tell the story of this financial period in an engaging, narrative style.

Cash Flow Data:
{facts}

Write a financial story that:
- Describes the financial journey of this period
- Highlights major inflows and outflows
- Explains what drove the key financial movements
- Uses engaging, story-like language
- Ends with insights about the overall financial trajectory

Story:""",

        "goal_progress": """You are a motivational financial coach tracking progress toward financial goals. Based on the goal data below, provide an encouraging progress update.

Goal Progress:
{facts}

Write a progress update that:
- Celebrates milestones achieved
- Shows how current progress relates to the ultimate goal
- Identifies what's working well in the strategy
- Suggests adjustments if needed to stay on track
- Maintains high motivation and positive momentum

Progress Update:""",

        "tax_preparation": """You are a tax preparation assistant helping to organize financial information. Based on the tax-relevant data below, provide a clear summary for tax preparation.

Tax-Relevant Data:
{facts}

Write a tax preparation summary that:
- Organizes income and deduction information clearly
- Highlights important tax implications
- Identifies potential deductions or credits
- Notes any items that need additional documentation
- Provides next steps for tax filing

Tax Summary:"""
    }
    
    return templates

def get_narrative_template(template_name: str) -> Optional[str]:
    """
    Get a specific narrative template by name.
    
    Args:
        template_name: Name of the template to retrieve
        
    Returns:
        Template string or None if not found
    """
    templates = get_narrative_templates()
    return templates.get(template_name)