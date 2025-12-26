"""
CSV Gateway Port (CSV 読み込みの抽象インターフェース).

👶 初心者向け解説:
- Port: 「どういう操作ができるか」を定義する抽象的な窓口
- Gateway: 外部データソース（CSV ファイル）へのアクセスを抽象化
- 依存性逆転: UseCase はこの Port に依存し、具体的な読み込み方法（pandas, polars 等）を知らない
"""

from abc import ABC, abstractmethod
from typing import Any

from fastapi import UploadFile


class CsvGateway(ABC):
    """CSV ファイル読み込みの抽象インターフェース."""

    @abstractmethod
    def read_csv_files(
        self, files: dict[str, UploadFile]
    ) -> tuple[dict[str, Any] | None, Any | None]:
        """
        CSV ファイルを読み込み、データフレームまたはエラーを返す.

        Args:
            files: ファイル識別子 → UploadFile のマッピング
                  例: {"shipment": <UploadFile>, "yard": <UploadFile>}

        Returns:
            成功時: (DataFrames の辞書, None)
            失敗時: (None, ErrorResponse)

        Notes:
            👶 戻り値の型 `Any` は、pandas DataFrame や polars DataFrame など、
            実装によって異なる可能性があるため抽象化しています。
        """
        pass

    @abstractmethod
    def validate_csv_structure(
        self, dfs: dict[str, Any], file_inputs: dict[str, Any]
    ) -> Any | None:
        """
        CSV の構造検証（必須カラム存在確認など）.

        Args:
            dfs: 読み込み済みデータフレームの辞書
            file_inputs: 元のファイル入力（検証メッセージ用）

        Returns:
            None（成功）または ErrorResponse（失敗）
        """
        pass

    @abstractmethod
    def format_csv_data(self, dfs: dict[str, Any]) -> dict[str, Any]:
        """
        CSV データの整形（型変換、正規化など）.

        Args:
            dfs: 生の読み込みデータ

        Returns:
            整形後のデータフレーム辞書
        """
        pass
