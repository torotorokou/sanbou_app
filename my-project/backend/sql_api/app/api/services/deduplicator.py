import pandas as pd
import sqlalchemy
from sqlalchemy.sql import text
import logging


class Deduplicator:
    def __init__(self, engine, schema: str):
        self.engine = engine
        self.schema = schema

    def extract_new_rows(
        self,
        df_new: pd.DataFrame,
        table_name: str,
        unique_keys: list[str],
        date_col: str,
    ) -> pd.DataFrame:
        if df_new.empty:
            return df_new

        # 日付の候補を抽出
        dates = df_new[date_col].dropna().unique().tolist()

        # DBから既存行を取得（例外対策付き）
        df_existing = self._read_existing_rows(
            table_name=table_name,
            date_col=date_col,
            dates=dates,
        )

        # 重複除去
        if df_existing.empty:
            return df_new

        df_merged = df_new.merge(
            df_existing[unique_keys], on=unique_keys, how="left", indicator=True
        )
        df_only_new = df_merged[df_merged["_merge"] == "left_only"].drop(
            columns=["_merge"]
        )
        return df_only_new

    def _read_existing_rows(
        self, table_name: str, date_col: str, dates: list
    ) -> pd.DataFrame:
        """
        指定されたテーブルから、指定日付に該当する行を取得する。
        テーブルが存在しない場合は空DataFrameを返す。
        """
        if not dates:
            return pd.DataFrame()

        placeholders = ", ".join([f":d{i}" for i in range(len(dates))])
        sql = text(f'''
            SELECT * FROM {self.schema}.{table_name}
            WHERE "{date_col}" IN ({placeholders})
        ''')
        params = {f"d{i}": d for i, d in enumerate(dates)}

        try:
            return pd.read_sql(sql, con=self.engine, params=params)
        except sqlalchemy.exc.ProgrammingError as e:
            if "UndefinedTable" in str(e) or "does not exist" in str(e):
                logging.warning(
                    f"[重複チェックスキップ] テーブル {self.schema}.{table_name} が存在しません。"
                )
                return pd.DataFrame()
            else:
                raise
