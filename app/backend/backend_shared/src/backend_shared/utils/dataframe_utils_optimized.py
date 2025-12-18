"""
dataframe_utils_optimized.py (Backward Compatibility)

⚠️ DEPRECATED: This module has been merged into dataframe_utils.py
Please update your imports:
    from backend_shared.utils.dataframe_utils_optimized import clean_na_strings_vectorized
    → from backend_shared.utils import clean_na_strings_vectorized
    or
    → from backend_shared.utils.dataframe_utils import clean_na_strings_vectorized

This compatibility layer will be removed in a future version.

dataframe_utils.pyの最適化版関数を提供。
apply()を使った行単位処理をベクトル化して高速化する。
"""
import warnings

# Re-export from new location for backward compatibility
from backend_shared.utils.dataframe_utils import (
    clean_na_strings_vectorized,
    to_numeric_vectorized,
)

# Issue deprecation warning on module import
warnings.warn(
    "backend_shared.utils.dataframe_utils_optimized is deprecated. "
    "Use backend_shared.utils.dataframe_utils instead.",
    DeprecationWarning,
    stacklevel=2
)


def apply_clean_na_strings_optimized(df, columns):
    """
    複数列に対してclean_na_strings_vectorizedを適用する。
    
    ⚠️ DEPRECATED: Use clean_na_strings_vectorized directly instead.
    
    Example:
        # Old (deprecated)
        df = apply_clean_na_strings_optimized(df, ['col1', 'col2'])
        
        # New (recommended)
        for col in ['col1', 'col2']:
            if col in df.columns:
                df[col] = clean_na_strings_vectorized(df[col])
    """
    warnings.warn(
        "apply_clean_na_strings_optimized is deprecated. "
        "Use clean_na_strings_vectorized directly.",
        DeprecationWarning,
        stacklevel=2
    )
    import pandas as pd
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = clean_na_strings_vectorized(df[col])
    return df


__all__ = [
    "clean_na_strings_vectorized",
    "to_numeric_vectorized",
    "apply_clean_na_strings_optimized",
]
