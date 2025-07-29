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


# class CSVUploadSQL:
#     def __init__(self, engine: Engine):
#         self.engine = engine

#     def save_to_sql(self, dfs: dict[str, pd.DataFrame]):
#         for name, df in dfs.items():
#             try:
#                 table_name = f"csv_{name.lower()}"
#                 df.to_sql(
#                     table_name,
#                     con=self.engine,
#                     if_exists="replace",
#                     index=False,
#                 )
#             except Exception as e:
#                 logging.exception(f"[SQL保存失敗] {name}: {e}")


import logging
import pandas as pd
from sqlalchemy.engine import Engine
from typing import Optional


class CSVUploadSQL:
    """
    DataFrameをSQLデータベースに保存するクラス。
    主に1ファイル単位の保存を担当し、必要に応じて一括保存も可能。
    """

    def __init__(self, engine: Engine):
        self.engine = engine

    def save_dataframe(
        self,
        df: pd.DataFrame,
        schema: Optional[str],
        table_name: str,
        if_exists: str = "append",  # 明示的に指定可能に
    ) -> None:
        """
        単一のDataFrameをSQLに保存する。
        :param df: 保存するデータ
        :param schema: 保存先スキーマ（None可）
        :param table_name: 保存先テーブル名
        :param if_exists: 'append'（追記） or 'replace'（上書き）など
        """
        if df.empty:
            logging.info(
                f"[スキップ] 空のデータフレーム（{schema}.{table_name}）は保存されません。"
            )
            return

        try:
            df.to_sql(
                name=table_name,
                con=self.engine,
                schema=schema,
                if_exists=if_exists,
                index=False,
            )
            logging.info(f"[SQL保存成功] {schema}.{table_name} （{len(df)} rows）")
        except Exception as e:
            logging.exception(f"[SQL保存失敗] {schema}.{table_name}: {e}")

    def save_multiple(
        self,
        dfs: dict[str, pd.DataFrame],
        schema: Optional[str],
        table_map: dict[str, str],
        if_exists: str = "append",
    ) -> None:
        """
        複数のDataFrameを一括で保存する（補助用途）。
        :param dfs: {csv_type: df} の辞書
        :param schema: スキーマ名
        :param table_map: {csv_type: table_name} のマッピング
        :param if_exists: append / replace 指定（全体に共通）
        """
        for name, df in dfs.items():
            table_name = table_map.get(name, name)
            self.save_dataframe(df, schema, table_name, if_exists=if_exists)
