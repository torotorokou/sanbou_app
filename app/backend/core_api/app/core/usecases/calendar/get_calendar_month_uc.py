"""
Get Calendar Month UseCase - 月次カレンダーデータ取得ユースケース

指定された年月の営業カレンダーデータを取得し、
営業日判定・祝日情報を提供します。

Design:
  - execute() method with Input/Output DTO pattern
  - Port abstraction for data access
  - Business logic and validation in UseCase layer
"""
import logging

from app.core.ports.calendar_port import ICalendarQuery
from app.core.usecases.calendar.dto import GetCalendarMonthInput, GetCalendarMonthOutput
from backend_shared.application.logging import log_usecase_execution, get_module_logger

logger = get_module_logger(__name__)


class GetCalendarMonthUseCase:
    """
    月次カレンダーデータ取得ユースケース
    
    Responsibilities:
      - Input validation (year/month range check)
      - Calendar data retrieval via Port
      - Structured output via DTO
    """
    
    def __init__(self, query: ICalendarQuery):
        """
        Args:
            query: カレンダーデータ取得の抽象インターフェース
        """
        self.query = query
    
    @log_usecase_execution(usecase_name="GetCalendarMonth", log_result=True)
    def execute(self, input_dto: GetCalendarMonthInput) -> GetCalendarMonthOutput:
        """
        指定された年月のカレンダーデータを取得
        
        Process:
          1. Validate input DTO
          2. Fetch calendar data via Port
          3. Return structured Output DTO
        
        Args:
            input_dto: Input DTO with year and month
            
        Returns:
            GetCalendarMonthOutput: カレンダーデータを含む出力DTO
            
        Raises:
            ValueError: 年月の範囲外
        """
        # Step 1: Validation
        input_dto.validate()
        
        # Step 2: データ取得（Port経由）
        # デコレータが自動でログ出力するため、手動ログは不要
        data = self.query.get_month_calendar(input_dto.year, input_dto.month)
        
        # Step 3: Return structured output
        return GetCalendarMonthOutput(calendar_days=data)
