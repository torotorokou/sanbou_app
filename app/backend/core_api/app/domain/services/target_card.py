"""
Target card domain logic: Pure computation for target card data.
No side effects, no I/O.
"""
from datetime import date as date_type
from typing import Optional, Dict, Any, Literal

Mode = Literal["daily", "monthly"]


def validate_target_card_date(requested_date: date_type, mode: Mode) -> bool:
    """
    Validate if the requested date is appropriate for the given mode.
    
    Args:
        requested_date: The date requested
        mode: "daily" or "monthly"
        
    Returns:
        True if valid, False otherwise
    """
    if mode == "monthly" and requested_date.day != 1:
        return False
    return True


def transform_target_card_data(raw_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Transform raw repository data into presentation format.
    Pure function: no side effects.
    
    Args:
        raw_data: Raw data from repository
        
    Returns:
        Transformed data suitable for API response, or None
    """
    if not raw_data:
        return None
    
    # Currently pass-through, but could add domain-level transformations here
    # e.g., calculating percentages, formatting, applying business rules
    return raw_data
