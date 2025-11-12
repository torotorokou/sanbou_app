"""
Shogun Flash Debug Service

将軍速報版CSVのアップロード処理を制御するサービス層。
CSV読み込み → Pydantic検証 → デバッグテーブル保存の流れを管理。
"""

import logging
from typing import Dict, Any, Optional
import io
import pandas as pd
from fastapi import UploadFile

from app.repositories.shogun_flash_debug_repo import ShogunFlashDebugRepository

logger = logging.getLogger(__name__)


class ShogunFlashDebugService:
    """将軍速報版デバッグ用サービス"""
    
    def __init__(self, repo: ShogunFlashDebugRepository):
        self.repo = repo
    
    async def process_upload(
        self,
        csv_type: str,
        file: UploadFile,
    ) -> Dict[str, Any]:
        """
        CSVファイルをアップロード、検証、保存
        
        Args:
            csv_type: CSV種別 ('receive', 'shipment', 'yard')
            file: アップロードされたCSVファイル
            
        Returns:
            dict: 処理結果
            {
                'csv_type': str,
                'filename': str,
                'status': 'success' | 'error',
                'validation': {...},  # 検証結果
                'message': str,
            }
        """
        filename = file.filename or 'unknown.csv'
        
        try:
            # 1. CSVファイルを読み込み
            content = await file.read()
            df = await self._read_csv(content, filename)
            
            if df is None or df.empty:
                return {
                    'csv_type': csv_type,
                    'filename': filename,
                    'status': 'error',
                    'message': 'CSVファイルが空、または読み込めませんでした',
                }
            
            logger.info(f"Loaded {csv_type} CSV: {len(df)} rows, {len(df.columns)} columns")
            
            # 2. カラム名を英語に変換（日本語 → 英語）
            df_en = self._convert_columns_to_english(df, csv_type)
            
            # 3. Pydantic検証 + デバッグテーブルに保存
            validation_result = self.repo.validate_and_save(csv_type, df_en)
            
            # 4. 結果を返す
            if validation_result['invalid_rows'] == 0:
                status = 'success'
                message = f"全 {validation_result['valid_rows']} 行を検証・保存しました"
            else:
                status = 'partial'
                message = (
                    f"{validation_result['valid_rows']} 行は有効です。"
                    f"{validation_result['invalid_rows']} 行に検証エラーがあります。"
                )
            
            return {
                'csv_type': csv_type,
                'filename': filename,
                'status': status,
                'validation': validation_result,
                'message': message,
            }
        
        except Exception as e:
            logger.exception(f"Error processing {csv_type} CSV: {e}")
            return {
                'csv_type': csv_type,
                'filename': filename,
                'status': 'error',
                'message': f"処理中にエラーが発生しました: {str(e)}",
            }
    
    async def _read_csv(self, content: bytes, filename: str) -> Optional[pd.DataFrame]:
        """
        CSVファイルを読み込む（UTF-8エンコーディング）
        
        Args:
            content: CSVファイルのバイナリ内容
            filename: ファイル名（ログ用）
            
        Returns:
            DataFrame or None
        """
        try:
            # UTF-8で読み込み
            df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            
            # 空白のみの行を除外
            df = df.dropna(how='all')
            
            return df
        
        except UnicodeDecodeError:
            logger.error(f"UTF-8 decode error for {filename}, trying Shift-JIS")
            try:
                # Shift-JISでリトライ
                df = pd.read_csv(io.BytesIO(content), encoding='shift-jis')
                df = df.dropna(how='all')
                return df
            except Exception as e:
                logger.error(f"Failed to read CSV with Shift-JIS: {e}")
                return None
        
        except Exception as e:
            logger.error(f"Failed to read CSV {filename}: {e}")
            return None
    
    def _convert_columns_to_english(self, df: pd.DataFrame, csv_type: str) -> pd.DataFrame:
        """
        日本語カラム名を英語に変換
        
        YAML定義（syogun_csv_masters.yaml）に基づいて変換。
        未定義のカラムはそのまま残す。
        
        Args:
            df: 元のDataFrame（日本語カラム）
            csv_type: CSV種別
            
        Returns:
            DataFrame（英語カラム）
        """
        # カラム名マッピング（日本語 → 英語）
        column_mappings = self._get_column_mapping(csv_type)
        
        # 存在するカラムのみマッピング
        rename_map = {
            jp_name: en_name
            for jp_name, en_name in column_mappings.items()
            if jp_name in df.columns
        }
        
        df_en = df.rename(columns=rename_map)
        
        logger.info(f"Converted columns for {csv_type}: {len(rename_map)} mappings")
        
        return df_en
    
    def _get_column_mapping(self, csv_type: str) -> Dict[str, str]:
        """
        CSV種別ごとの日本語→英語カラムマッピング
        
        syogun_csv_masters.yaml に基づく定義
        """
        if csv_type == 'receive':
            return {
                '伝票日付': 'slip_date',
                '売上日付': 'sales_date',
                '支払日付': 'payment_date',
                '業者CD': 'vendor_cd',
                '業者名': 'vendor_name',
                '伝票区分CD': 'slip_type_cd',
                '伝票区分名': 'slip_type_name',
                '品名CD': 'item_cd',
                '品名': 'item_name',
                '正味重量': 'net_weight',
                '数量': 'quantity',
                '単位CD': 'unit_cd',
                '単位名': 'unit_name',
                '単価': 'unit_price',
                '金額': 'amount',
                '受入番号': 'receive_no',
                '集計項目CD': 'aggregate_item_cd',
                '集計項目': 'aggregate_item_name',
                '種類CD': 'category_cd',
                '種類名': 'category_name',
                '計量時間(総重量)': 'weighing_time_gross',
                '計量時間(空車重量)': 'weighing_time_empty',
                '現場CD': 'site_cd',
                '現場名': 'site_name',
                '荷降業者CD': 'unload_vendor_cd',
                '荷降業者名': 'unload_vendor_name',
                '荷降現場CD': 'unload_site_cd',
                '荷降現場名': 'unload_site_name',
                '運搬業者CD': 'transport_vendor_cd',
                '運搬業者名': 'transport_vendor_name',
                '取引先CD': 'client_cd',
                '取引先名': 'client_name',
                'マニ種類CD': 'manifest_type_cd',
                'マニ種類名': 'manifest_type_name',
                'マニフェスト番号': 'manifest_no',
                '営業担当者CD': 'sales_staff_cd',
                '営業担当者名': 'sales_staff_name',
            }
        elif csv_type == 'shipment':
            return {
                '伝票日付': 'slip_date',
                '出荷番号': 'shipment_no',
                '取引先名': 'client_en_name',
                '業者CD': 'vendor_cd',
                '業者名': 'vendor_en_name',
                '現場CD': 'site_cd',
                '現場名': 'site_en_name',
                '品名': 'item_en_name',
                '正味重量': 'net_weight',
                '数量': 'quantity',
                '単位名': 'unit_en_name',
                '単価': 'unit_price',
                '金額': 'amount',
                '運搬業者名': 'transport_vendor_en_name',
                '伝票区分名': 'slip_type_en_name',
                '明細備考': 'detail_note',
            }
        elif csv_type == 'yard':
            return {
                '伝票日付': 'slip_date',
                '取引先名': 'client_en_name',
                '品名': 'item_en_name',
                '正味重量': 'net_weight',
                '数量': 'quantity',
                '単位名': 'unit_en_name',
                '単価': 'unit_price',
                '金額': 'amount',
                '営業担当者名': 'sales_staff_en_name',
                '業者CD': 'vendor_cd',
                '業者名': 'vendor_en_name',
                '種類CD': 'category_cd',
                '種類名': 'category_en_name',
                '品名CD': 'item_cd',
                '伝票番号': 'slip_no',
            }
        else:
            return {}
