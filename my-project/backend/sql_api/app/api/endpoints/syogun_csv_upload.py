# --- import ---
import os
from fastapi import APIRouter, UploadFile, File, status
from typing import Annotated

from app.local_config.api_constants import SYOGUN_CSV_ROUTE
from app.local_config.paths import SAVE_DIR_TEMP
from app.api.utils.response_utils import api_response
from app.api.utils.csv_processor import CSVProcessor
from backend_shared.config.config_loader import SyogunCsvConfigLoader

from app.api.services.csv_upload.csv_upload_validator import CSVValidationResponder
from app.api.services.csv_upload.storage import CSVUploadTempStorage
from backend_shared.src.csv_formatter.formatter_factory import CSVFormatterFactory

from backend_shared.src.csv_formatter.formatter_config import build_formatter_config
from app.api.services.csv_upload.formatter_utils import format_and_rename_for_sql

# --- ルーター定義 ---
router = APIRouter()
os.makedirs(SAVE_DIR_TEMP, exist_ok=True)


# --- 統括サービス ---
class CSVImportService:
    def __init__(self, file_inputs: dict[str, UploadFile]):
        self.processor = CSVProcessor()
        self.config_loader = SyogunCsvConfigLoader()

        # file_inputsのキー（"shipment"や"receive"等）から必要なexpected_headersのみ取得
        self.required_columns = {
            name: self.config_loader.get_expected_headers(name)
            for name in file_inputs.keys()
        }

        self.validator = CSVValidationResponder(self.required_columns)
        self.storage = CSVUploadTempStorage()

    async def process_upload(self, file_inputs: dict[str, UploadFile]):
        # ステップ1：空ファイルチェック
        if missing := self.validator.check_missing_file(file_inputs):
            return api_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                status_str="error",
                code="MISSING_FILE",
                detail=f"{missing}ファイルが選択されていません。",
            )

        # ステップ2：CSV読み込み
        dfs = {}
        for name, file in file_inputs.items():
            df = await self.processor.read_csv_file(file)
            dfs[name] = df

        # ステップ3：必須カラムチェック
        if res := self.validator.validate_columns(dfs, file_inputs):
            return res

        # ステップ4：伝票日付の存在チェック
        if res := self.validator.validate_denpyou_date_exists(dfs, file_inputs):
            return res

        # ステップ5：伝票日付の一致チェック
        if res := self.validator.validate_denpyou_date_consistency(dfs):
            return res

        # ステップ6：CSVの整形処理（columns_defを渡す設計に修正）
        formatted_dfs = {}
        for name, df in dfs.items():
            config = build_formatter_config(self.config_loader, name)
            formatter = CSVFormatterFactory.get_formatter(name, config)

            df_formatted = formatter.format(df)
            formatted_dfs[name] = df_formatted

        # ステップ7：SQL保存用のヘッダ名の変更
        rename_dfs = {}
        for name, df in dfs.items():
            rename_dfs[name] = format_and_rename_for_sql(name, df, self.config_loader)

        # ステップ7：SQLに転送
        self.storage.save_to_temp(
            dfs=rename_dfs, file_inputs=file_inputs, processor=self.processor
        )
        return api_response(
            status_code=status.HTTP_200_OK,
            status_str="success",
            code="SUCCESS",
            detail="全てのファイルが正常にアップロード・検証されました。",
        )


# --- FastAPIルート定義 ---
@router.post(SYOGUN_CSV_ROUTE, summary="将軍CSVファイルをアップロード")
async def upload_csv(
    shipment: Annotated[UploadFile | None, File(description="出荷CSV")] = None,
    receive: Annotated[UploadFile | None, File(description="受入CSV")] = None,
    yard: Annotated[UploadFile | None, File(description="ヤードCSV")] = None,
):
    file_inputs = {
        "shipment": shipment,
        "receive": receive,
        "yard": yard,
    }
    # Noneのものは除外
    file_inputs = {k: v for k, v in file_inputs.items() if v is not None}
    service = CSVImportService(file_inputs)
    return await service.process_upload(file_inputs)
