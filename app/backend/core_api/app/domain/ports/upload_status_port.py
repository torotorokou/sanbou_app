"""
Upload Status Port - アップロード状態管理の抽象インターフェース

CSV アップロードファイルの状態取得・カレンダー表示・削除を行うための Port。
"""
from typing import Protocol, List, Dict, Any, Optional
from datetime import date


class IUploadStatusQuery(Protocol):
    """
    アップロードステータス取得の抽象インターフェース
    
    log.upload_file テーブルからアップロードファイルの情報を取得します。
    """
    
    def get_upload_status(self, upload_file_id: int) -> Optional[Dict[str, Any]]:
        """
        アップロードファイルのステータスを取得
        
        Args:
            upload_file_id: log.upload_file.id
            
        Returns:
            アップロード情報の辞書、または None（見つからない場合）
            - id: アップロードファイルID
            - csv_type: CSV種別
            - file_name: ファイル名
            - file_type: ファイルタイプ
            - processing_status: 処理ステータス
            - uploaded_at: アップロード日時（ISO形式）
            - uploaded_by: アップロード実行者
            - row_count: 行数
            - error_message: エラーメッセージ
        """
        ...
    
    def get_upload_calendar(self, year: int, month: int) -> List[Dict[str, Any]]:
        """
        指定月のアップロードカレンダーデータを取得
        
        Args:
            year: 年
            month: 月 (1-12)
            
        Returns:
            カレンダーアイテムのリスト。各要素は以下のキーを含む:
            - uploadFileId: アップロードファイルID
            - date: データ日付 (YYYY-MM-DD)
            - csvKind: CSV種別
            - rowCount: 行数
        """
        ...


class IUploadCalendarQuery(Protocol):
    """
    アップロードカレンダー詳細取得の抽象インターフェース
    
    stg テーブルからデータ日付と行数を集計してカレンダー表示用データを提供します。
    """
    
    def fetch_upload_calendar(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        指定期間のアップロードカレンダーデータを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            カレンダーアイテムのリスト。各要素は以下のキーを含む:
            - uploadFileId: アップロードファイルID
            - date: データ日付 (YYYY-MM-DD文字列)
            - csvKind: CSV種別
            - rowCount: 行数
        """
        ...
    
    def soft_delete_by_date_and_kind(
        self,
        *,
        upload_file_id: int,
        target_date: date,
        csv_kind: str,
        deleted_by: Optional[str] = None
    ) -> int:
        """
        指定されたアップロードスコープを論理削除
        
        Args:
            upload_file_id: 削除対象の log.upload_file.id
            target_date: 削除対象の日付
            csv_kind: CSV種別
            deleted_by: 削除実行者（オプション）
            
        Returns:
            影響を受けた行数
        """
        ...
