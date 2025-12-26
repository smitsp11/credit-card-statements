"""
Main classification logic.

Applies all rules in priority order to classify transactions.
"""
from datetime import datetime
from typing import Dict, List
from .rules import should_ignore, get_hard_override
from .food_detector import is_food_type_merchant


# Valid categories
CATEGORIES = [
    'school meals',
    'food',
    'groceries',
    'presto',
    'school',
    'personal',
    'mom stuff',
    'other',
]


def classify_transaction(merchant_description: str, transaction_date: datetime, amount: float) -> str:
    """
    Classify a single transaction into a category.
    
    Priority order:
    1. Ignore rules (return None if should ignore)
    2. Hard merchant overrides
    3. Food-type detection + weekday/weekend rule
    4. Amount-based fallback
    
    Args:
        merchant_description: Merchant name
        transaction_date: Transaction date
        amount: Transaction amount (positive CAD)
        
    Returns:
        Category name
    """
    # Step 1: Check ignore rules
    if should_ignore(merchant_description):
        return None
    
    # Step 2: Check hard merchant overrides
    override = get_hard_override(merchant_description)
    if override:
        return override
    
    # Step 3: Food-type detection with weekday/weekend rule
    if is_food_type_merchant(merchant_description, amount):
        weekday = transaction_date.weekday()  # 0=Monday, 6=Sunday
        if weekday < 5:  # Monday-Friday
            return 'school meals'
        else:  # Saturday-Sunday
            return 'food'
    
    # Step 4: Amount-based fallback
    if amount >= 100:
        return 'school'
    elif amount <= 10:
        return 'groceries'
    else:
        return 'other'


def aggregate_by_category(transactions: List) -> Dict[str, float]:
    """
    Classify and aggregate transactions by category.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        Dictionary mapping category names to total amounts
    """
    category_totals = {cat: 0.0 for cat in CATEGORIES}
    skipped_count = 0
    
    for transaction in transactions:
        category = classify_transaction(
            transaction.merchant_description,
            transaction.transaction_date,
            transaction.amount
        )
        
        if category is None:
            skipped_count += 1
            continue
        
        if category not in category_totals:
            raise ValueError(f"Invalid category: {category}")
        
        category_totals[category] += transaction.amount
    
    # Remove categories with zero totals
    category_totals = {k: v for k, v in category_totals.items() if v > 0}
    
    return category_totals, skipped_count

