# 入出力用の標準ライブラリ
import io

# データフレーム操作用のpandas
import pandas as pd

# FastAPIのファイルアップロード用
from fastapi import UploadFile


class CSVProcessor:
    """
    CSVファイルを処理するためのクラス。
    主にアップロードされたCSVファイルの読み込みや、結果の辞書作成を行う。
    """

    async def read_csv_file(self, file: UploadFile) -> pd.DataFrame:
        """
        アップロードされたCSVファイルを非同期で読み込み、pandasのDataFrameとして返す。

        Args:
            file (UploadFile): アップロードされたCSVファイル

        Returns:
            pd.DataFrame: 読み込んだデータフレーム
        """
        content = await file.read()
        # BOM付きUTF-8対応
        csv_text = content.decode("utf-8-sig")
        df = pd.read_csv(io.StringIO(csv_text), skip_blank_lines=True)
        # 全列がNaNの行を削除（完全な空行）
        df = df.dropna(how="all")
        return df

    def create_result(
        self,
        filename: str,
        columns: list,
        status: str,
        code: str,
        detail: str,
    ) -> dict:
        """
        処理結果を辞書形式で作成する。

        Args:
            filename (str): ファイル名
            columns (list): カラム名リスト
            status (str): ステータス（"success" または "error"）
            code (str): エラーコードやステータスコード
            detail (str): 詳細メッセージ

        Returns:
            dict: 結果をまとめた辞書
        """
        return {
            "filename": filename,
            "columns": columns,
            "status": status,  # "success" または "error"
            "code": code,
            "detail": detail,
        }
