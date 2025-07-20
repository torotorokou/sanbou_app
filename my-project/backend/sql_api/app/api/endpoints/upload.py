import os
import io
import yaml
import pandas as pd
from fastapi import APIRouter, UploadFile, File
from app.local_config.api_constants import SYOGUN_CSV_ROUTE
from app.local_config.paths import CSV_DEF_PATH

SAVE_DIR = "/backend/app/data/syogun_csv"
os.makedirs(SAVE_DIR, exist_ok=True)

router = APIRouter()


def load_required_columns_from_yaml(config_path: str = CSV_DEF_PATH) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return {key: value.get("expected_headers", []) for key, value in config.items()}


@router.post(SYOGUN_CSV_ROUTE, summary="将軍CSVファイルをアップロード")
async def upload_csv(
    shipment: UploadFile = File(None),
    receive: UploadFile = File(None),
    yard: UploadFile = File(None),
):
    required_columns = load_required_columns_from_yaml()
    dfs = {}
    results = {}
    any_ng = False

    for csv_type, file in [
        ("shipment", shipment),
        ("receive", receive),
        ("yard", yard),
    ]:
        if file:
            content = await file.read()
            csv_text = content.decode("utf-8")
            df = pd.read_csv(io.StringIO(csv_text))
            required_cols = required_columns.get(csv_type, [])
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                results[csv_type] = {
                    "filename": file.filename,
                    "columns": df.columns.tolist(),
                    "status": "NG",
                    "message": f"必須カラムが不足しています: {missing}",
                }
                any_ng = True
            else:
                dfs[csv_type] = df
                results[csv_type] = {
                    "filename": file.filename,
                    "columns": df.columns.tolist(),
                    "status": "OK",
                    "message": "アップロード成功",
                }
        else:
            results[csv_type] = None
            any_ng = True

    # どれか1つでもカラムNG/ファイル未指定なら即エラー返す
    if any_ng:
        return {
            "status": "error",
            "message": "必須カラムの不足、またはファイル未選択があります。",
            "result": results,
        }

    # 伝票日付の一致確認
    try:
        shipment_dates = set(dfs["shipment"]["伝票日付"].dropna().unique())
        receive_dates = set(dfs["receive"]["伝票日付"].dropna().unique())
        yard_dates = set(dfs["yard"]["伝票日付"].dropna().unique())
    except KeyError:
        return {
            "status": "error",
            "message": "いずれかのファイルに『伝票日付』カラムがありません。",
            "result": results,
        }

    if not (shipment_dates == receive_dates == yard_dates):
        return {
            "status": "error",
            "message": "伝票日付が一致しません。",
            "dates": {
                "shipment": sorted(list(shipment_dates)),
                "receive": sorted(list(receive_dates)),
                "yard": sorted(list(yard_dates)),
            },
            "result": results,
        }

    # ここでファイル保存やSQL登録などの本処理へ進む（必要に応じて）

    return {
        "status": "success",
        "message": "全てのファイルが正常にアップロード・検証されました。",
        "result": results,
    }
