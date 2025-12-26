"""
Food-type merchant detection.

Determines if a merchant sells prepared meals or drinks.
"""
from typing import List


# Keywords that indicate food-type merchants (case-insensitive)
FOOD_KEYWORDS = [
    'MCDONALD',
    'KFC',
    'TACO',
    'BURRITO',
    'SUB',
    'PIZZA',
    'SHELBYS',
    'TIM HORTONS',
    'STARBUCKS',
    'COFFEE',
    'CAFE',
    'RESTAURANT',
    'DINER',
    'GRILL',
    'BISTRO',
    'KITCHEN',
    'UBER EATS',
    'UBEREATS',
    'DOORDASH',
    'SKIP',
]


# Explicit exclusions (override food detection)
FOOD_EXCLUSIONS = [
    'FRESHCO',
    'FORTINOS',
    'LOBLAWS',
    'WAL-MART',
    'WALMART',
    'DOLLARAMA',
    'SHOPPERS',
    'SUPERCENTER',
]


def is_food_type_merchant(merchant_description: str, amount: float) -> bool:
    """
    Determine if a merchant is food-type (sells prepared meals/drinks).
    
    Args:
        merchant_description: The merchant name
        amount: Transaction amount
        
    Returns:
        True if merchant is food-type
    """
    merchant_upper = merchant_description.upper()
    
    # Check explicit exclusions first
    if any(exclusion in merchant_upper for exclusion in FOOD_EXCLUSIONS):
        return False
    
    # Check keyword matches
    if any(keyword in merchant_upper for keyword in FOOD_KEYWORDS):
        return True
    
    # Fallback heuristic: amount <= 25 and merchant name length < 40
    if amount <= 25 and len(merchant_description) < 40:
        return True
    
    return False

