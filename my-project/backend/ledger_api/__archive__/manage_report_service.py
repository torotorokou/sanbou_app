# app/api/services/report_service.py

import pandas as pd
import os
from backend_shared.src.csv_validator_api.csv_upload_validator import (
    CSVValidationResponder,
)


class ManageReportService:
    def __init__(self, report_key: str, files: dict):
        self.report_key = report_key
        self.files = files
        self.dfs = {}  # ファイル名→DataFrame

    def preprocess(self):
        # 必要に応じて事前整形（例：曜日除去など）
        for k, df in self.dfs.items():
            if df["伝票日付"].astype(str).str.contains(r"\(").any():
                df["伝票日付"] = (
                    df["伝票日付"]
                    .astype(str)
                    .str.replace(r"\([^)]+\)", "", regex=True)
                    .str.strip()
                )
                self.dfs[k] = df

    def generate_pdf(self, pdf_name: str) -> str:
        # ダミー生成例
        pdf_path = pdf_name
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%Dummy PDF\n")
        return pdf_path

    def generate_excel(self, excel_name: str) -> str:
        excel_path = excel_name
        with pd.ExcelWriter(excel_path) as writer:
            for k, df in self.dfs.items():
                df.to_excel(writer, sheet_name=k, index=False)
        return excel_path
