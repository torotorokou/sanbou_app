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
        # ファイル内容をバイト列で読み込む
        content = await file.read()
        # バイト列をUTF-8で文字列にデコード
        csv_text = content.decode("utf-8")
        # 文字列をpandasでDataFrameに変換
        return pd.read_csv(io.StringIO(csv_text))

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
