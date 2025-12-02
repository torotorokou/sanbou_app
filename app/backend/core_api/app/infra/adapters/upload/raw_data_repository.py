"""
Raw Data Repository

CSV の生データ(変換前)を raw スキーマに保存するリポジトリ。
- log.upload_file: 全 CSV アップロードの共通ログ(シンプル版)
- raw.receive_raw: 受入CSV の生データ(TEXT 型)
- raw.yard_raw: ヤードCSV の生データ(TEXT 型)
- raw.shipment_raw: 出荷CSV の生データ(TEXT 型)

log.upload_file はすべての CSV アップロード(将軍、マニフェスト、予約表など)で
共通のログテーブルとして使用します。
"""

import logging
import os
import hashlib
from typing import Optional, Dict, Any, Iterable
from datetime import datetime, date
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text, Table, MetaData, Column, Integer, BigInteger, Text, String, DateTime, Boolean, ForeignKey
from backend_shared.application.logging import create_log_context

from app.core.domain.csv import CsvKind

logger = logging.getLogger(__name__)


# csv_kind から stg テーブル名へのマッピング（CsvKind Enum を使用）
CSV_KIND_TABLE_MAP: Dict[str, str] = {
    kind.value: kind.table_name
    for kind in CsvKind
}


class RawDataRepository:
    """生データ保存リポジトリ"""
    
    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self.metadata = MetaData()
        
        # upload_file テーブル定義（共通アップロードログ、log スキーマ）
        # シンプル構成：必要最小限のカラムのみ定義
        self.upload_file_table = Table(
            'upload_file',
            self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('csv_type', String(32), nullable=False),  # 'receive', 'yard', 'shipment', etc.
            Column('file_name', Text, nullable=False),
            Column('file_hash', String(64), nullable=False),
            Column('file_type', String(20), nullable=False),  # 'FLASH' / 'FINAL'
            Column('file_size_bytes', BigInteger, nullable=True),
            Column('row_count', Integer, nullable=True),
            Column('uploaded_at', DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
            Column('uploaded_by', String(100), nullable=True),
            Column('is_deleted', Boolean, nullable=False, server_default=text('false')),  # 論理削除フラグ
            Column('deleted_at', DateTime(timezone=True), nullable=True),
            Column('deleted_by', Text, nullable=True),
            Column('processing_status', String(20), server_default='pending', nullable=False),
            Column('error_message', Text, nullable=True),
            Column('env', Text, server_default='local_dev', nullable=False),
            schema='log'
        )
        
        # receive_raw テーブル定義（生データは raw スキーマに保持）
        self.receive_raw_table = Table(
            'receive_raw',
            self.metadata,
            Column('id', BigInteger, primary_key=True, autoincrement=True),
            Column('file_id', Integer, ForeignKey('log.upload_file.id'), nullable=False),
            Column('row_number', Integer, nullable=False),
            # 受入CSV の各カラム（TEXT 型、英語カラム名）
            Column('slip_date_text', Text, nullable=True),
            Column('sales_date_text', Text, nullable=True),
            Column('payment_date_text', Text, nullable=True),
            Column('vendor_cd_text', Text, nullable=True),
            Column('vendor_name_text', Text, nullable=True),
            Column('slip_type_cd_text', Text, nullable=True),
            Column('slip_type_name_text', Text, nullable=True),
            Column('item_cd_text', Text, nullable=True),
            Column('item_name_text', Text, nullable=True),
            Column('net_weight_text', Text, nullable=True),
            Column('quantity_text', Text, nullable=True),
            Column('unit_cd_text', Text, nullable=True),
            Column('unit_name_text', Text, nullable=True),
            Column('unit_price_text', Text, nullable=True),
            Column('amount_text', Text, nullable=True),
            Column('receive_no_text', Text, nullable=True),
            Column('aggregate_item_cd_text', Text, nullable=True),
            Column('aggregate_item_name_text', Text, nullable=True),
            Column('category_cd_text', Text, nullable=True),
            Column('category_name_text', Text, nullable=True),
            Column('weighing_time_gross_text', Text, nullable=True),
            Column('weighing_time_empty_text', Text, nullable=True),
            Column('site_cd_text', Text, nullable=True),
            Column('site_name_text', Text, nullable=True),
            Column('unload_vendor_cd_text', Text, nullable=True),
            Column('unload_vendor_name_text', Text, nullable=True),
            Column('unload_site_cd_text', Text, nullable=True),
            Column('unload_site_name_text', Text, nullable=True),
            Column('transport_vendor_cd_text', Text, nullable=True),
            Column('transport_vendor_name_text', Text, nullable=True),
            Column('client_cd_text', Text, nullable=True),
            Column('client_name_text', Text, nullable=True),
            Column('manifest_type_cd_text', Text, nullable=True),
            Column('manifest_type_name_text', Text, nullable=True),
            Column('manifest_no_text', Text, nullable=True),
            Column('sales_staff_cd_text', Text, nullable=True),
            Column('sales_staff_name_text', Text, nullable=True),
            Column('column38', Text, nullable=True),
            Column('column39', Text, nullable=True),
            Column('loaded_at', DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP')),
            schema='raw'
        )
        
        # yard_raw テーブル定義（生データは raw スキーマに保持）
        self.yard_raw_table = Table(
            'yard_raw',
            self.metadata,
            Column('id', BigInteger, primary_key=True, autoincrement=True),
            Column('file_id', Integer, ForeignKey('log.upload_file.id'), nullable=False),
            Column('row_number', Integer, nullable=False),
            # ヤードCSV の各カラム（TEXT 型、英語カラム名）
            Column('slip_date_text', Text, nullable=True),
            Column('client_name_text', Text, nullable=True),
            Column('item_name_text', Text, nullable=True),
            Column('net_weight_text', Text, nullable=True),
            Column('quantity_text', Text, nullable=True),
            Column('unit_name_text', Text, nullable=True),
            Column('unit_price_text', Text, nullable=True),
            Column('amount_text', Text, nullable=True),
            Column('sales_staff_name_text', Text, nullable=True),
            Column('vendor_cd_text', Text, nullable=True),
            Column('vendor_name_text', Text, nullable=True),
            Column('category_cd_text', Text, nullable=True),
            Column('category_name_text', Text, nullable=True),
            Column('item_cd_text', Text, nullable=True),
            Column('slip_no_text', Text, nullable=True),
            Column('loaded_at', DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP')),
            schema='raw'
        )
        
        # shipment_raw テーブル定義（生データは raw スキーマに保持）
        self.shipment_raw_table = Table(
            'shipment_raw',
            self.metadata,
            Column('id', BigInteger, primary_key=True, autoincrement=True),
            Column('file_id', Integer, ForeignKey('log.upload_file.id'), nullable=False),
            Column('row_number', Integer, nullable=False),
            # 出荷CSV の各カラム（TEXT 型、英語カラム名）
            Column('slip_date_text', Text, nullable=True),
            Column('shipment_no_text', Text, nullable=True),
            Column('client_name_text', Text, nullable=True),
            Column('vendor_cd_text', Text, nullable=True),
            Column('vendor_name_text', Text, nullable=True),
            Column('site_cd_text', Text, nullable=True),
            Column('site_name_text', Text, nullable=True),
            Column('item_name_text', Text, nullable=True),
            Column('net_weight_text', Text, nullable=True),
            Column('quantity_text', Text, nullable=True),
            Column('unit_name_text', Text, nullable=True),
            Column('unit_price_text', Text, nullable=True),
            Column('amount_text', Text, nullable=True),
            Column('transport_vendor_name_text', Text, nullable=True),
            Column('slip_type_name_text', Text, nullable=True),
            Column('detail_note_text', Text, nullable=True),
            Column('category_cd_text', Text, nullable=True),
            Column('category_name_text', Text, nullable=True),
            Column('loaded_at', DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP')),
            schema='raw'
        )
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """
        ファイルの SHA-256 ハッシュを計算
        
        Args:
            file_content: ファイルの内容（バイト列）
            
        Returns:
            str: SHA-256 ハッシュ（16進数文字列）
        """
        return hashlib.sha256(file_content).hexdigest()
    
    def create_upload_file(
        self,
        csv_type: str,
        file_name: str,
        file_hash: str,
        file_type: str,
        file_size_bytes: Optional[int] = None,
        row_count: Optional[int] = None,
        uploaded_by: Optional[str] = None,
        env: Optional[str] = None,
    ) -> int:
        """
        アップロードファイルのメタ情報を log.upload_file に登録
        
        Args:
            csv_type: CSV種別 ('receive', 'yard', 'shipment', 'payable', 'sales_summary' など)
            file_name: ファイル名
            file_hash: SHA-256 ハッシュ
            file_type: FLASH / FINAL
            file_size_bytes: ファイルサイズ
            row_count: データ行数
            uploaded_by: アップロードユーザー
            env: 環境名 (デフォルト: 'local_dev')
            
        Returns:
            int: 登録された upload_file.id
        """
        try:
            # env が指定されていない場合は環境変数または 'local_dev' をデフォルト
            if env is None:
                env = os.getenv("APP_ENV", "local_dev")
            
            result = self.db.execute(
                self.upload_file_table.insert().values(
                    csv_type=csv_type,
                    file_name=file_name,
                    file_hash=file_hash,
                    file_type=file_type,
                    file_size_bytes=file_size_bytes,
                    row_count=row_count,
                    uploaded_by=uploaded_by,
                    processing_status='pending',
                    env=env,
                ).returning(self.upload_file_table.c.id)
            )
            file_id = result.scalar_one()
            self.db.commit()
            logger.info(
                "upload_fileレコード作成",
                extra=create_log_context(
                    file_id=file_id,
                    csv_type=csv_type,
                    hash_prefix=file_hash[:8]
                )
            )
            return file_id
        except Exception as e:
            self.db.rollback()
            logger.error(
                "upload_file作成失敗",
                extra=create_log_context(error=str(e)),
                exc_info=True
            )
            raise
    
    def check_duplicate_upload(
        self,
        csv_type: str,
        file_hash: str,
        file_type: str,
        file_name: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        row_count: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        重複アップロードチェック（成功済み＆有効なファイルのみ）
        
        優先順位:
        1. file_hash + csv_type + file_type でマッチ（最も信頼性が高い）
        2. フォールバック: file_name + file_size + row_count でマッチ
        
        Args:
            csv_type: CSV種別 ('receive', 'yard', 'shipment')
            file_hash: SHA-256ハッシュ
            file_type: 'FLASH' or 'FINAL'
            file_name: ファイル名（フォールバック用）
            file_size_bytes: ファイルサイズ（フォールバック用）
            row_count: 行数（フォールバック用）
            
        Returns:
            重複ファイルの情報（id, uploaded_at等）、存在しない場合はNone
        """
        # 第1優先: file_hash + csv_type + file_type で検索（論理削除されていない有効なレコードのみ）
        result = self.db.execute(
            self.upload_file_table.select().where(
                self.upload_file_table.c.csv_type == csv_type,
                self.upload_file_table.c.file_hash == file_hash,
                self.upload_file_table.c.file_type == file_type,
                self.upload_file_table.c.processing_status == 'success',
                self.upload_file_table.c.is_deleted == False,  # 論理削除されていないレコードのみ
            ).order_by(self.upload_file_table.c.uploaded_at.desc())
        ).fetchone()
        
        if result:
            logger.info(
                "重複検出(hash一致)",
                extra=create_log_context(
                    csv_type=csv_type,
                    hash_prefix=file_hash[:8],
                    existing_id=result.id
                )
            )
            return {
                "id": result.id,
                "file_name": result.file_name,
                "uploaded_at": result.uploaded_at,
                "uploaded_by": result.uploaded_by,
                "match_type": "hash",
            }
        
        # 第2優先: フォールバック（ファイル名、サイズ、行数）
        if file_name and file_size_bytes is not None and row_count is not None:
            result = self.db.execute(
                self.upload_file_table.select().where(
                    self.upload_file_table.c.csv_type == csv_type,
                    self.upload_file_table.c.file_name == file_name,
                    self.upload_file_table.c.file_size_bytes == file_size_bytes,
                    self.upload_file_table.c.row_count == row_count,
                    self.upload_file_table.c.processing_status == 'success',
                    self.upload_file_table.c.is_deleted == False,  # 論理削除されていないレコードのみ
                ).order_by(self.upload_file_table.c.uploaded_at.desc())
            ).fetchone()
            
            if result:
                logger.info(
                    "重複検出(fallback一致)",
                    extra=create_log_context(
                        csv_type=csv_type,
                        file_name=file_name,
                        existing_id=result.id
                    )
                )
                return {
                    "id": result.id,
                    "file_name": result.file_name,
                    "uploaded_at": result.uploaded_at,
                    "uploaded_by": result.uploaded_by,
                    "match_type": "fallback",
                }
        
        return None
    
    def check_file_exists(self, file_hash: str, csv_type: str) -> Optional[int]:
        """
        同一ファイルがすでに登録されているかチェック（後方互換性のため残す）
        
        Args:
            file_hash: SHA-256 ハッシュ
            csv_type: CSV種別 ('receive', 'yard', 'shipment', etc.)
            
        Returns:
            Optional[int]: 既存の upload_file.id、存在しない場合は None
        """
        result = self.db.execute(
            self.upload_file_table.select().where(
                self.upload_file_table.c.file_hash == file_hash,
                self.upload_file_table.c.csv_type == csv_type,
            )
        ).fetchone()
        
        return result.id if result else None
    
    def update_upload_status(
        self,
        file_id: int,
        status: str,
        error_message: Optional[str] = None,
        row_count: Optional[int] = None,
    ) -> None:
        """
        アップロードファイルの処理ステータスを更新
        
        Args:
            file_id: upload_file.id
            status: 'pending' / 'success' / 'failed'
            error_message: エラーメッセージ
            row_count: 実際に処理された行数（成功時に更新）
        """
        try:
            values: Dict[str, Any] = {
                "processing_status": status,
                "error_message": error_message,
            }
            if row_count is not None:
                values["row_count"] = row_count

            self.db.execute(
                self.upload_file_table.update()
                .where(self.upload_file_table.c.id == file_id)
                .values(**values)
            )
            self.db.commit()
            logger.info(
                "upload_fileステータス更新",
                extra=create_log_context(file_id=file_id, status=status)
            )
        except Exception as e:
            self.db.rollback()
            logger.error(
                "upload_fileステータス更新失敗",
                extra=create_log_context(error=str(e)),
                exc_info=True
            )
            raise
    
    def soft_delete_upload_file(
        self,
        file_id: int,
        deleted_by: Optional[str] = None,
    ) -> None:
        """
        アップロードファイルを論理削除
        
        Args:
            file_id: upload_file.id
            deleted_by: 削除実行者（ユーザー名など）
        """
        try:
            self.db.execute(
                self.upload_file_table.update()
                .where(self.upload_file_table.c.id == file_id)
                .values(
                    is_deleted=True,
                    deleted_at=datetime.utcnow(),
                    deleted_by=deleted_by,
                )
            )
            self.db.commit()
            logger.info(
                "upload_file論理削除",
                extra=create_log_context(file_id=file_id, deleted_by=deleted_by)
            )
        except Exception as e:
            self.db.rollback()
            logger.error(
                "upload_file論理削除失敗",
                extra=create_log_context(error=str(e)),
                exc_info=True
            )
            raise
    
    def soft_delete_scope_by_dates(
        self,
        *,
        csv_kind: str,
        dates: Iterable[date],
        deleted_by: Optional[str] = None,
    ) -> int:
        """
        指定された csv_kind について、指定日付の有効データをすべて論理削除する。
        upload_file_id は問わず、「その日付の is_deleted = false 行すべて」が対象。
        パターンA（同一日付＋種別は最後のアップロードだけ有効）用。
        
        Args:
            csv_kind: CSV種別 ('shogun_flash_receive', 'shogun_final_yard', etc.)
            dates: 削除対象の日付のイテラブル
            deleted_by: 削除実行者（ユーザー名など）
            
        Returns:
            int: 更新された行数
            
        Raises:
            ValueError: 不正な csv_kind が指定された場合
        """
        from sqlalchemy import bindparam
        
        # csv_kind からテーブル名を取得
        table_name = CSV_KIND_TABLE_MAP.get(csv_kind)
        if not table_name:
            raise ValueError(
                f"Invalid csv_kind: {csv_kind}. "
                f"Valid values are: {list(CSV_KIND_TABLE_MAP.keys())}"
            )
        
        # dates が空の場合は何もしない
        dates_list = list(dates)
        if not dates_list:
            logger.debug(
                "削除対象日付なし",
                extra=create_log_context(csv_kind=csv_kind)
            )
            return 0
        
        # dates を date 型のリストに変換(datetime.date または pd.Timestamp.date())
        # PostgreSQL の date 型と互換性を持たせる
        normalized_dates = []
        for d in dates_list:
            if hasattr(d, 'date') and callable(getattr(d, 'date', None)):
                # pd.Timestamp の場合
                normalized_dates.append(d.date())  # type: ignore
            elif isinstance(d, date):
                # datetime.date の場合
                normalized_dates.append(d)
            else:
                logger.warning(f"Unexpected date type: {type(d)}, value={d}")
                normalized_dates.append(d)
        
        logger.info(
            f"[SOFT_DELETE] soft_delete_scope_by_dates called: table={table_name}, "
            f"csv_kind={csv_kind}, dates_count={len(normalized_dates)}, "
            f"dates_sample={normalized_dates[:3]}, deleted_by={deleted_by}"
        )
        
        try:
            # IN句 + expanding bindparam を使用（型の不整合を回避）
            sql = text(f"""
                UPDATE {table_name}
                SET is_deleted = true,
                    deleted_at = now(),
                    deleted_by = :deleted_by
                WHERE slip_date IN :dates
                  AND is_deleted = false
            """).bindparams(bindparam("dates", expanding=True))
            
            result = self.db.execute(sql, {
                "dates": normalized_dates,
                "deleted_by": deleted_by,
            })
            affected_rows = result.rowcount
            self.db.commit()
            
            logger.info(
                f"[SOFT_DELETE] ✅ soft_delete_scope_by_dates: table={table_name}, csv_kind={csv_kind}, "
                f"dates={normalized_dates[:5]}{'...' if len(normalized_dates) > 5 else ''}, "
                f"deleted_by={deleted_by}, ⚠️ affected_rows={affected_rows}"
            )
            return affected_rows
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to soft delete scope by dates: csv_kind={csv_kind}, "
                f"table={table_name}, dates={normalized_dates[:5]}, error={e}",
                exc_info=True
            )
            raise
    
    def soft_delete_by_date_and_kind(
        self,
        *,
        upload_file_id: int,
        target_date: date,
        csv_kind: str,
        deleted_by: Optional[str] = None,
    ) -> int:
        """
        カレンダーの1マス（upload_file_id + date + csv_kind）に対応する行だけを論理削除。
        特定ファイルの特定日付分だけ無効化したい場合に使用。
        
        Args:
            upload_file_id: log.upload_file.id
            target_date: 削除対象の日付
            csv_kind: CSV種別 ('shogun_flash_receive', 'shogun_final_yard', etc.)
            deleted_by: 削除実行者（ユーザー名など）
            
        Returns:
            int: 更新された行数
            
        Raises:
            ValueError: 不正な csv_kind が指定された場合
        """
        # csv_kind からテーブル名を取得
        table_name = CSV_KIND_TABLE_MAP.get(csv_kind)
        if not table_name:
            raise ValueError(
                f"Invalid csv_kind: {csv_kind}. "
                f"Valid values are: {list(CSV_KIND_TABLE_MAP.keys())}"
            )
        
        try:
            sql = text(f"""
                UPDATE {table_name}
                SET is_deleted = true,
                    deleted_at = now(),
                    deleted_by = :deleted_by
                WHERE upload_file_id = :upload_file_id
                  AND slip_date = :target_date
                  AND is_deleted = false
            """)
            
            result = self.db.execute(sql, {
                "upload_file_id": upload_file_id,
                "target_date": target_date,
                "deleted_by": deleted_by,
            })
            affected_rows = result.rowcount
            self.db.commit()
            
            logger.info(
                f"Soft deleted {affected_rows} rows from {table_name} "
                f"for upload_file_id={upload_file_id}, date={target_date}, "
                f"deleted_by={deleted_by}"
            )
            return affected_rows
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to soft delete by date and kind: "
                f"upload_file_id={upload_file_id}, date={target_date}, "
                f"csv_kind={csv_kind}, error={e}",
                exc_info=True
            )
            raise
    
    def is_recent_duplicate_upload(
        self,
        *,
        file_hash: str,
        csv_type: str,
        uploaded_by: str,
        minutes: int = 3,
    ) -> bool:
        """
        直近 minutes 分以内に、同一 file_hash + csv_type + uploaded_by の
        upload_file レコードが存在するかを判定する。
        UX 用の「連続アップロード防止」チェック。
        
        Args:
            file_hash: SHA-256ハッシュ
            csv_type: CSV種別 ('receive', 'yard', 'shipment')
            uploaded_by: アップロードユーザー名
            minutes: 判定する時間範囲（分）
            
        Returns:
            bool: 直近に同一ファイルが存在すれば True
        """
        try:
            sql = text("""
                SELECT 1
                FROM log.upload_file
                WHERE file_hash = :file_hash
                  AND csv_type = :csv_type
                  AND uploaded_by = :uploaded_by
                  AND uploaded_at >= now() - (:minutes || ' minutes')::interval
                LIMIT 1
            """)
            
            result = self.db.execute(sql, {
                "file_hash": file_hash,
                "csv_type": csv_type,
                "uploaded_by": uploaded_by,
                "minutes": minutes,
            }).fetchone()
            
            is_duplicate = result is not None
            if is_duplicate:
                logger.warning(
                    "直近重複検出",
                    extra=create_log_context(
                        csv_type=csv_type,
                        hash_prefix=file_hash[:8],
                        uploaded_by=uploaded_by
                    )
                )
            return is_duplicate
            
        except Exception as e:
            logger.error(
                "直近重複チェック失敗",
                extra=create_log_context(error=str(e)),
                exc_info=True
            )
            # エラー時は安全側に倒して False を返す（処理は継続させる）
            return False

    
    def save_receive_raw(
        self,
        file_id: int,
        df: pd.DataFrame,
    ) -> int:
        """
        受入CSV の生データを raw.receive_raw に保存
        
        Args:
            file_id: upload_file.id
            df: 日本語カラム名のままの DataFrame（変換前）
            
        Returns:
            int: 保存した行数
        """
        if df.empty:
            logger.warning("Empty DataFrame, skipping raw save")
            return 0
        
        try:
            # 行番号を付与
            records = []
            for row_idx, (idx, row) in enumerate(df.iterrows(), start=1):
                record: Dict[str, Any] = {
                    'file_id': file_id,
                    'row_number': row_idx,  # 1-indexed
                }
                # DataFrame の各カラムを TEXT として保存
                for col in df.columns:
                    value = row[col]
                    # pd.NaT, np.nan, None はすべて None に正規化
                    if pd.isna(value):
                        record[col] = None
                    else:
                        # すべて文字列として保存
                        record[col] = str(value)
                
                records.append(record)
            
            # バルクインサート
            self.db.execute(self.receive_raw_table.insert(), records)
            self.db.commit()
            
            logger.info(f"Saved {len(records)} rows to raw.receive_raw (file_id={file_id})")
            return len(records)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save raw data: {e}")
            raise
    
    def save_yard_raw(
        self,
        file_id: int,
        df: pd.DataFrame,
    ) -> int:
        """
        ヤードCSV の生データを raw.yard_raw に保存
        
        Args:
            file_id: upload_file.id
            df: 日本語カラム名のままの DataFrame（変換前）
            
        Returns:
            int: 保存した行数
        """
        if df.empty:
            logger.warning("Empty DataFrame, skipping raw save")
            return 0
        
        try:
            # カラム名マッピング（日本語 → 英語）
            column_map = {
                '伝票日付': 'slip_date_text',
                '取引先名': 'client_name_text',
                '品名': 'item_name_text',
                '正味重量': 'net_weight_text',
                '数量': 'quantity_text',
                '単位名': 'unit_name_text',
                '単価': 'unit_price_text',
                '金額': 'amount_text',
                '営業担当者名': 'sales_staff_name_text',
                '業者CD': 'vendor_cd_text',
                '業者名': 'vendor_name_text',
                '種類CD': 'category_cd_text',
                '種類名': 'category_name_text',
                '品名CD': 'item_cd_text',
                '伝票番号': 'slip_no_text',
            }
            
            # 行番号を付与してレコード作成
            records = []
            for row_idx, (idx, row) in enumerate(df.iterrows(), start=1):
                record: Dict[str, Any] = {
                    'file_id': file_id,
                    'row_number': row_idx,
                }
                # DataFrame の各カラムを TEXT として保存（英語カラム名に変換）
                for jp_col, en_col in column_map.items():
                    if jp_col in df.columns:
                        value = row[jp_col]
                        record[en_col] = None if pd.isna(value) else str(value)
                
                records.append(record)
            
            # バルクインサート
            self.db.execute(self.yard_raw_table.insert(), records)
            self.db.commit()
            
            logger.info(f"Saved {len(records)} rows to raw.yard_raw (file_id={file_id})")
            return len(records)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save yard raw data: {e}")
            raise
    
    def save_shipment_raw(
        self,
        file_id: int,
        df: pd.DataFrame,
    ) -> int:
        """
        出荷CSV の生データを raw.shipment_raw に保存
        
        Args:
            file_id: upload_file.id
            df: 日本語カラム名のままの DataFrame（変換前）
            
        Returns:
            int: 保存した行数
        """
        if df.empty:
            logger.warning("Empty DataFrame, skipping raw save")
            return 0
        
        try:
            # カラム名マッピング（日本語 → 英語）
            column_map = {
                '伝票日付': 'slip_date_text',
                '出荷番号': 'shipment_no_text',
                '取引先名': 'client_name_text',
                '業者CD': 'vendor_cd_text',
                '業者名': 'vendor_name_text',
                '現場CD': 'site_cd_text',
                '現場名': 'site_name_text',
                '品名': 'item_name_text',
                '正味重量': 'net_weight_text',
                '数量': 'quantity_text',
                '単位名': 'unit_name_text',
                '単価': 'unit_price_text',
                '金額': 'amount_text',
                '運搬業者名': 'transport_vendor_name_text',
                '伝票区分名': 'slip_type_name_text',
                '明細備考': 'detail_note_text',
                '種類CD': 'category_cd_text',
                '種類名': 'category_name_text',
            }
            
            # 行番号を付与してレコード作成
            records = []
            for row_idx, (idx, row) in enumerate(df.iterrows(), start=1):
                record: Dict[str, Any] = {
                    'file_id': file_id,
                    'row_number': row_idx,
                }
                # DataFrame の各カラムを TEXT として保存（英語カラム名に変換）
                for jp_col, en_col in column_map.items():
                    if jp_col in df.columns:
                        value = row[jp_col]
                        record[en_col] = None if pd.isna(value) else str(value)
                
                records.append(record)
            
            # バルクインサート
            self.db.execute(self.shipment_raw_table.insert(), records)
            self.db.commit()
            
            logger.info(f"Saved {len(records)} rows to raw.shipment_raw (file_id={file_id})")
            return len(records)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save shipment raw data: {e}")
            raise
    
    # ========================================================================
    # Upload Status Query Methods (IUploadStatusQuery Port implementation)
    # ========================================================================
    
    def get_upload_status(self, upload_file_id: int) -> Optional[Dict[str, Any]]:
        """
        アップロードファイルのステータスを取得
        
        Args:
            upload_file_id: log.upload_file.id
            
        Returns:
            アップロード情報の辞書、または None（見つからない場合）
        """
        from sqlalchemy import select
        
        try:
            result = self.db.execute(
                select(self.upload_file_table).where(
                    self.upload_file_table.c.id == upload_file_id
                )
            ).first()
            
            if not result:
                return None
            
            # レコードを辞書に変換
            upload_info = {
                "id": result.id,
                "csv_type": result.csv_type,
                "file_name": result.file_name,
                "file_type": result.file_type,
                "processing_status": result.processing_status,
                "uploaded_at": result.uploaded_at.isoformat() if result.uploaded_at else None,
                "uploaded_by": result.uploaded_by,
                "row_count": result.row_count,
                "error_message": result.error_message,
            }
            
            return upload_info
            
        except Exception as e:
            logger.error(
                "upload_status取得失敗",
                extra=create_log_context(upload_file_id=upload_file_id, error=str(e)),
                exc_info=True
            )
            raise
    
    def get_upload_calendar(self, year: int, month: int) -> list[Dict[str, Any]]:
        """
        指定月のアップロードカレンダーデータを取得
        
        Args:
            year: 年
            month: 月 (1-12)
            
        Returns:
            カレンダーアイテムのリスト
        """
        from datetime import date
        from calendar import monthrange
        
        try:
            # 指定月の開始日・終了日を計算
            _, last_day = monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)
            
            # 各 stg テーブルから upload_file_id, slip_date, csv_kind, row_count を取得
            # 論理削除されていないデータのみ
            sql = text("""
            WITH upload_data AS (
                SELECT 
                    uf.id as upload_file_id,
                    r.slip_date as data_date,
                    'shogun_flash_receive' as csv_kind,
                    COUNT(*) as row_count
                FROM log.upload_file uf
                JOIN stg.shogun_flash_receive r ON r.upload_file_id = uf.id
                WHERE r.is_deleted = false
                  AND r.slip_date IS NOT NULL
                  AND r.slip_date >= :start_date
                  AND r.slip_date <= :end_date
                GROUP BY uf.id, r.slip_date
                
                UNION ALL
                
                SELECT 
                    uf.id,
                    y.slip_date,
                    'shogun_flash_yard' as csv_kind,
                    COUNT(*) as row_count
                FROM log.upload_file uf
                JOIN stg.shogun_flash_yard y ON y.upload_file_id = uf.id
                WHERE y.is_deleted = false
                  AND y.slip_date IS NOT NULL
                  AND y.slip_date >= :start_date
                  AND y.slip_date <= :end_date
                GROUP BY uf.id, y.slip_date
                
                UNION ALL
                
                SELECT 
                    uf.id,
                    s.slip_date,
                    'shogun_flash_shipment' as csv_kind,
                    COUNT(*) as row_count
                FROM log.upload_file uf
                JOIN stg.shogun_flash_shipment s ON s.upload_file_id = uf.id
                WHERE s.is_deleted = false
                  AND s.slip_date IS NOT NULL
                  AND s.slip_date >= :start_date
                  AND s.slip_date <= :end_date
                GROUP BY uf.id, s.slip_date
            )
            SELECT 
                upload_file_id,
                data_date,
                csv_kind,
                row_count
            FROM upload_data
            ORDER BY data_date, csv_kind, upload_file_id
            """)
            
            result = self.db.execute(sql, {
                "start_date": start_date,
                "end_date": end_date
            })
            rows = result.fetchall()
            
            items = [
                {
                    "uploadFileId": row[0],
                    "date": row[1].strftime("%Y-%m-%d"),  # 'YYYY-MM-DD' 形式
                    "csvKind": row[2],
                    "rowCount": row[3]
                }
                for row in rows
            ]
            
            logger.debug(f"Fetched upload calendar for {year}-{month:02d}: {len(items)} items")
            return items
            
        except Exception as e:
            logger.error(f"Failed to fetch upload calendar: year={year}, month={month}, error={e}", exc_info=True)
            raise

