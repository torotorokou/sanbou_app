import os
import pandas as pd
from sqlalchemy.engine import Engine
import logging

from app.local_config.paths import SAVE_DIR_TEMP


# --- 保存処理 ---
class CSVUploadTempStorage:
    """
    CSVファイルの保存処理をまとめたクラス。
    一時保存ディレクトリへのファイル保存などを行います。
    """

    def save_to_temp(self, dfs: dict, file_inputs: dict, processor):
        """
        DataFrameを一時ディレクトリにCSVファイルとして保存します。
        :param dfs: ファイル名→DataFrameの辞書
        :param file_inputs: ファイル名→UploadFileの辞書
        :param processor: CSV処理結果を生成するプロセッサ
        :return: 保存結果の辞書
        """
        result = {}
        for name, df in dfs.items():
            file = file_inputs[name]
            filename = (
                file.filename or f"{name}.csv"
            )  # ファイル名が無い場合のフォールバック
            save_path = os.path.join(SAVE_DIR_TEMP, filename)
            # DataFrameをCSVファイルとして保存（UTF-8 BOM付き）
            df.to_csv(save_path, index=False, encoding="utf-8-sig")
            # 保存結果の情報を作成
            result[name] = processor.create_result(
                filename=filename,
                columns=df.columns.tolist(),
                status="success",
                code="SUCCESS",
                detail="アップロード成功",
            )
        return result


class CSVUploadSQL:
    def __init__(self, engine: Engine):
        self.engine = engine

    def save_to_sql(self, dfs: dict[str, pd.DataFrame]):
        for name, df in dfs.items():
            try:
                table_name = f"csv_{name.lower()}"
                df.to_sql(
                    table_name,
                    con=self.engine,
                    if_exists="replace",
                    index=False,
                )
            except Exception as e:
                logging.exception(f"[SQL保存失敗] {name}: {e}")
