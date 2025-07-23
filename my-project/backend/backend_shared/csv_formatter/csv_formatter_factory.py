import pandas as pd
from typing import Protocol

# =========================
# フォーマッターの共通プロトコル
# =========================


class BaseCSVFormatter(Protocol):
    def format(self, df: pd.DataFrame) -> pd.DataFrame: ...


# 親クラスで共通処理を定義
class CommonCSVFormatter:
    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        # 例：全カラム名をstrip＆大文字化
        df.columns = [col.strip() for col in df.columns]
        # 例：全データの前後空白トリム
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        return df


# configファイル
class ConfigurableFormatter(BaseCSVFormatter):
    def __init__(self, rules: dict):
        self.rules = rules

    def format(self, df: pd.DataFrame, csv_type: str) -> pd.DataFrame:
        rule = self.rules.get(csv_type, {})
        for col in rule.get("numeric_columns", []):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        for col in rule.get("date_columns", []):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
        if "required_columns" in rule:
            df = df.dropna(subset=rule["required_columns"])
        return df


# =========================
# 各CSV種別のフォーマッター
# =========================


class ShipmentFormatter(BaseCSVFormatter):  # ← 明示的に継承
    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        if "正味重量" in df.columns:
            df["正味重量"] = pd.to_numeric(df["正味重量"], errors="coerce")
        if "伝票日付" in df.columns:
            df["伝票日付"] = pd.to_datetime(df["伝票日付"], errors="coerce").dt.date
        df = df.dropna(subset=["伝票日付", "正味重量"])
        return df


class ReceiveFormatter(BaseCSVFormatter):  # ← 明示的に継承
    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        if "正味重量" in df.columns:
            df["正味重量"] = pd.to_numeric(df["正味重量"], errors="coerce")
        if "伝票日付" in df.columns:
            df["伝票日付"] = pd.to_datetime(df["伝票日付"], errors="coerce").dt.date
        df = df.dropna(subset=["伝票日付", "正味重量"])
        return df


class YardFormatter(BaseCSVFormatter):  # ← 明示的に継承
    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        if "伝票日付" in df.columns:
            df["伝票日付"] = pd.to_datetime(df["伝票日付"], errors="coerce").dt.date
        df = df.dropna(subset=["伝票日付"])
        return df


class DefaultFormatter(BaseCSVFormatter):  # ← 明示的に継承
    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        return df


# =========================
# ファクトリ
# =========================


class CSVFormatterFactory:
    @staticmethod
    def get_formatter(csv_type: str) -> BaseCSVFormatter:
        if csv_type == "shipment":
            return ShipmentFormatter()
        elif csv_type == "receive":
            return ReceiveFormatter()
        elif csv_type == "yard":
            return YardFormatter()
        else:
            return DefaultFormatter()


# =========================
# 利用例
# =========================

if __name__ == "__main__":
    # 例: 使い方
    # df = pd.read_csv("shipment.csv")
    # formatter = CSVFormatterFactory.get_formatter("shipment")
    # df_formatted = formatter.format(df)
    pass
