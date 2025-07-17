from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import os, shutil

from app.utils.config_loader import load_csv_path_config
from app.local_config.api_constants import UKEIRE_UPLOAD_ROUTE  # ✅ 定数として読み込み

router = APIRouter()


@router.post(UKEIRE_UPLOAD_ROUTE, summary="受入CSVファイルをアップロード")
async def upload_ukeire_csv(file: UploadFile = File(...)):
    """
    Reactから送信された受入CSVをサーバーに一時保存します。
    - 保存先ディレクトリや命名ルールは config/csv_paths.yaml に従います。
    """
    # ✅ 設定ファイルから 'ukeire' 用設定を読み込む
    try:
        config = load_csv_path_config("ukeire")
        upload_dir = config["upload_dir"]
        filename_pattern = config.get(
            "raw_filename_pattern", "{timestamp}_{original_name}"
        )
    except KeyError as e:
        raise HTTPException(
            status_code=500, detail=f"設定に必要なキーが存在しません: {e}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"設定読み込みエラー: {e}")

    # ✅ 保存ディレクトリ作成（存在しない場合）
    os.makedirs(upload_dir, exist_ok=True)

    # ✅ ファイル名にタイムスタンプを付与（重複防止）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = filename_pattern.format(timestamp=timestamp, original_name=file.filename)
    save_path = os.path.join(upload_dir, filename)

    # ✅ ファイル保存処理
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイル保存エラー: {e}")

    return {"status": "success", "filename": filename}
