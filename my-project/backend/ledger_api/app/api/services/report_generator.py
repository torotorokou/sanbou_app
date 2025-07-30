# backend/app/api/services/report_generator.py

import os
from datetime import datetime
from typing import Dict, Any


class BaseReportGenerator:
    def __init__(self, output_dir: str, files: Dict[str, Any]):
        self.output_dir = output_dir
        self.files = files

    def preprocess(self, report_key: str):
        # --- YAML読込例
        required_files = config_loader.get_required_files(
            report_key
        )  # 例: ["yard", "shipping"]
        optional_files = config_loader.get_optional_files(
            report_key
        )  # 例: ["receive"] なければ []

        check_csv_files(files, required_files, optional_files)

        return self.files

    def generate_pdf(self, pdf_name: str) -> str:
        pdf_path = os.path.join(self.output_dir, pdf_name)
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%Dummy PDF file\n")
        return pdf_path

    def generate_excel(self, excel_name: str) -> str:
        excel_path = os.path.join(self.output_dir, excel_name)
        with open(excel_path, "wb") as f:
            f.write(b"Dummy,Excel,File\n1,2,3\n")
        return excel_path

    def postprocess(self) -> str:
        """後処理：ダウンロード名用の日付返却"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_download_pdf_name(self, file_name_jp: str, date_str: str) -> str:
        """PDF用のダウンロードファイル名を生成"""
        return f"{file_name_jp}_{date_str}.pdf"

    def get_download_excel_name(self, file_name_jp: str, date_str: str) -> str:
        """Excel用のダウンロードファイル名を生成"""
        return f"{file_name_jp}_{date_str}.xlsx"


class FactoryReportGenerator(BaseReportGenerator):
    pass


class SalesReportGenerator(BaseReportGenerator):
    pass


class InventoryReportGenerator(BaseReportGenerator):
    pass


class YardReportGenerator(BaseReportGenerator):
    pass


class ShippingReportGenerator(BaseReportGenerator):
    pass


def get_report_generator(
    report_key: str, output_dir: str, files: Dict[str, Any]
) -> BaseReportGenerator:
    """帳簿種別に応じて適切なGeneratorを返す"""
    if report_key == "factory":
        return FactoryReportGenerator(output_dir, files)
    elif report_key == "sales":
        return SalesReportGenerator(output_dir, files)
    elif report_key == "inventory":
        return InventoryReportGenerator(output_dir, files)
    elif report_key == "yard":
        return YardReportGenerator(output_dir, files)
    elif report_key == "shipping":
        return ShippingReportGenerator(output_dir, files)
    else:
        return BaseReportGenerator(output_dir, files)
