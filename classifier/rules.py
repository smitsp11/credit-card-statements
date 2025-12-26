"""
Classification rules for transactions.

Contains hard merchant overrides and ignore patterns.
"""
from typing import Optional, List


# Patterns that should be ignored (case-insensitive)
IGNORE_PATTERNS = [
    'PAYMENT',
    'THANK YOU',
    'PAIEMENT',
    'BALANCE',
    'INTEREST',
    'FEE',
]


# Hard merchant overrides (highest priority)
# Format: (prefix_pattern, category)
# First match wins
HARD_OVERRIDES = [
    ('PRESTO', 'presto'),
    ('FLYWIRE', 'personal'),
    ('OCAS', 'personal'),
    ('OPENAI', 'personal'),
    ('CU* RM FINANCE', 'school'),
    ('WAL-MART', 'groceries'),
    ('WALMART', 'groceries'),
    ('FRESHCO', 'groceries'),
    ('FORTINOS', 'groceries'),
    ('DOLLARAMA', 'groceries'),
    ('SHOPPERS', 'groceries'),
    ('SPOTIFY', 'other'),
    ('CITY OF', 'other'),
]


def should_ignore(merchant_description: str) -> bool:
    """
    Check if a transaction should be ignored.
    
    Args:
        merchant_description: The merchant name from the transaction
        
    Returns:
        True if transaction should be ignored
    """
    merchant_upper = merchant_description.upper()
    return any(pattern in merchant_upper for pattern in IGNORE_PATTERNS)


def get_hard_override(merchant_description: str) -> Optional[str]:
    """
    Check for hard merchant override.
    
    Args:
        merchant_description: The merchant name from the transaction
        
    Returns:
        Category name if override found, None otherwise
    """
    merchant_upper = merchant_description.upper()
    
    for pattern, category in HARD_OVERRIDES:
        if merchant_upper.startswith(pattern) or pattern in merchant_upper:
            return category
    
    return None

