import os
import pandas as pd
import io
from fastapi import APIRouter, UploadFile, File
from app.local_config.api_constants import SYOGUN_CSV_ROUTE

router = APIRouter()

# 必須カラムをcsv_typeごとに定義
REQUIRED_COLUMNS = {
    "shipment": ["正味重量", "出荷日付"],
    "receive": ["正味重量", "受入日付"],
    "yard": ["ヤード名", "正味重量"],
}

SAVE_DIR = "/backend/app/data/syogun_csv"
os.makedirs(SAVE_DIR, exist_ok=True)


@router.post(SYOGUN_CSV_ROUTE, summary="将軍CSVファイルをアップロード")
async def upload_csv(
    shipment: UploadFile = File(None),
    receive: UploadFile = File(None),
    yard: UploadFile = File(None),
):
    results = {}
    for csv_type, file in [
        ("shipment", shipment),
        ("receive", receive),
        ("yard", yard),
    ]:
        if file:
            content = await file.read()
            csv_text = content.decode("utf-8")
            df = pd.read_csv(io.StringIO(csv_text))
            # ここでcsv_typeごとに必須カラムを取得
            required_cols = REQUIRED_COLUMNS.get(csv_type, [])
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                results[csv_type] = {
                    "filename": file.filename,
                    "error": f"必須カラムが不足しています: {missing}",
                }
            else:
                save_path = os.path.join(SAVE_DIR, file.filename)
                with open(save_path, "wb") as f:
                    f.write(content)
                # NaN対策
                df = df.where(pd.notnull(df), None)
                results[csv_type] = {
                    "filename": file.filename,
                    "save_path": save_path,
                    "columns": df.columns.tolist(),
                    "preview": df.head().to_dict(orient="records"),
                }
        else:
            results[csv_type] = None

    return {"received": results}
