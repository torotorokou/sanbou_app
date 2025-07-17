from fastapi import APIRouter, UploadFile, File
from app.local_config.api_constants import SYOGUN_CSV_ROUTE

router = APIRouter()


@router.post(SYOGUN_CSV_ROUTE, summary="将軍CSVファイルをアップロード")
async def upload_csv(
    shipment: UploadFile = File(None),
    receive: UploadFile = File(None),
    yard: UploadFile = File(None),
):
    """
    Reactから送信されたCSVをサーバーに保存します。
    - 保存先ディレクトリや命名ルールは config/csv_paths.yaml に従います。
    """
    results = {}
    for csv_type, file in [
        ("shipment", shipment),
        ("receive", receive),
        ("yard", yard),
    ]:
        if file:
            content = await file.read()
            results[csv_type] = {"filename": file.filename, "size": len(content)}
        else:
            results[csv_type] = None
    return {"received": results}
