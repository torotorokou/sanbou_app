"""
Forecasting domain logic: Pure computation for forecast data.
Feature engineering, post-processing, threshold logic, etc.
No I/O.
"""
from datetime import date as date_type
from typing import List, Dict, Any


# ビジネス定数
MAX_FORECAST_DAYS = 90  # 予測可能な最大日数
MIN_FORECAST_DAYS = 1   # 予測可能な最小日数
PREDICTION_PRECISION = 2  # 予測値の小数点以下桁数


def validate_forecast_date_range(from_date: date_type, to_date: date_type) -> tuple[bool, str]:
    """
    Validate forecast date range with business rules.
    
    ビジネスルール:
      - 開始日は終了日より前でなければならない
      - 予測期間は1日以上、90日以内でなければならない
      - 過去日付は許可（履歴データ分析用）
    
    Args:
        from_date: Start date
        to_date: End date
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if valid, False otherwise
            - error_message: 空文字列（valid時）または具体的なエラーメッセージ
    """
    if from_date > to_date:
        return False, f"開始日（{from_date}）は終了日（{to_date}）より前でなければなりません"
    
    delta_days = (to_date - from_date).days
    
    if delta_days < MIN_FORECAST_DAYS:
        return False, f"予測期間は最低{MIN_FORECAST_DAYS}日必要です（指定: {delta_days}日）"
    
    if delta_days > MAX_FORECAST_DAYS:
        return False, f"予測期間は最大{MAX_FORECAST_DAYS}日です（指定: {delta_days}日）"
    
    return True, ""


def apply_business_rules_to_predictions(predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply domain-specific business rules to prediction results.
    Pure function: no side effects.
    
    適用されるルール:
      1. 予測値を指定精度（小数点以下2桁）に丸める
      2. 負の予測値は0に補正（数量は負にならない）
      3. 信頼区間の下限が負の場合は0に補正
      4. 信頼区間の上限が予測値より小さい場合は警告フラグを追加
    
    Args:
        predictions: Raw prediction data
            Expected keys: date, y_hat, y_lo (optional), y_hi (optional)
        
    Returns:
        Predictions with business rules applied
    """
    if not predictions:
        return predictions
    
    result = []
    for pred in predictions:
        # Copy to avoid mutating original
        adjusted = pred.copy()
        
        # 1. 予測値の精度調整と負値補正
        if "y_hat" in adjusted:
            y_hat = float(adjusted["y_hat"])
            adjusted["y_hat"] = max(0.0, round(y_hat, PREDICTION_PRECISION))
        
        # 2. 信頼区間の下限補正
        if "y_lo" in adjusted and adjusted["y_lo"] is not None:
            y_lo = float(adjusted["y_lo"])
            adjusted["y_lo"] = max(0.0, round(y_lo, PREDICTION_PRECISION))
        
        # 3. 信頼区間の上限補正
        if "y_hi" in adjusted and adjusted["y_hi"] is not None:
            y_hi = float(adjusted["y_hi"])
            adjusted["y_hi"] = max(0.0, round(y_hi, PREDICTION_PRECISION))
        
        # 4. 信頼区間の整合性チェック
        if all(k in adjusted for k in ["y_hat", "y_lo", "y_hi"]):
            if adjusted["y_hi"] < adjusted["y_hat"]:
                adjusted["_warning"] = "upper_bound_below_prediction"
            if adjusted["y_lo"] > adjusted["y_hat"]:
                adjusted["_warning"] = "lower_bound_above_prediction"
        
        result.append(adjusted)
    
    return result


def calculate_forecast_confidence(predictions: List[Dict[str, Any]]) -> float:
    """
    予測の信頼度を計算（将来の拡張用）
    
    信頼区間の幅が狭いほど信頼度が高い
    
    Args:
        predictions: Prediction data with y_lo and y_hi
    
    Returns:
        float: Confidence score (0.0 - 1.0)
    """
    if not predictions:
        return 0.0
    
    valid_intervals = [
        p for p in predictions
        if all(k in p and p[k] is not None for k in ["y_hat", "y_lo", "y_hi"])
    ]
    
    if not valid_intervals:
        return 0.5  # デフォルト値
    
    # 相対的な信頼区間幅の平均を計算
    widths = []
    for p in valid_intervals:
        y_hat = float(p["y_hat"])
        if y_hat > 0:
            interval_width = (float(p["y_hi"]) - float(p["y_lo"])) / y_hat
            widths.append(interval_width)
    
    if not widths:
        return 0.5
    
    avg_width = sum(widths) / len(widths)
    # 幅が小さいほど高信頼度（逆数的な関係）
    confidence = max(0.0, min(1.0, 1.0 - (avg_width / 2.0)))
    
    return round(confidence, 3)

