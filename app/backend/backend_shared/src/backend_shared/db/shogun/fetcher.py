"""
将軍データセット取得クラス

将軍システムの6種類のデータセット（flash/final × receive/shipment/yard）を
DBから取得する機能を提供します。

設計原則:
- Clean Architecture: DB I/Oは外部から注入されたSessionを使用
- SOLID: 単一責任、依存性注入、インターフェース分離
- 既存構造を壊さない: backend_sharedの既存パターンに従う
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional, Union

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend_shared.application.logging import get_module_logger
from ..names import (
    V_ACTIVE_SHOGUN_FINAL_RECEIVE,
    V_ACTIVE_SHOGUN_FINAL_SHIPMENT,
    V_ACTIVE_SHOGUN_FINAL_YARD,
    V_ACTIVE_SHOGUN_FLASH_RECEIVE,
    V_ACTIVE_SHOGUN_FLASH_SHIPMENT,
    V_ACTIVE_SHOGUN_FLASH_YARD,
)

from .dataset_keys import ShogunDatasetKey, ShogunDatasetKeyType
from .master_name_mapper import ShogunMasterNameMapper

logger = get_module_logger(__name__)


class ShogunDatasetFetcherError(Exception):
    """将軍データセット取得エラー"""
    pass


class ShogunDatasetFetcher:
    """
    将軍データセット取得クラス
    
    6種類のデータセットをDBから取得する機能を提供します。
    
    責務:
    - dataset_key → DB view名の解決
    - DB viewからのデータ取得
    - フィルタリング（日付範囲等）
    - 結果の返却（list[dict] または DataFrame）
    
    依存性注入:
    - SQLAlchemy Session: 外部から注入（I/O境界を越えない）
    - MasterNameMapper: カラム名変換用（オプショナル）
    
    使用例:
        # 基本的な使い方
        fetcher = ShogunDatasetFetcher(db_session)
        
        # 受入データ取得（final）
        data = fetcher.fetch(ShogunDatasetKey.SHOGUN_FINAL_RECEIVE)
        # => list[dict]
        
        # 日付範囲指定
        data = fetcher.fetch(
            ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 10, 31)
        )
        
        # DataFrame形式で取得
        df = fetcher.fetch_df(ShogunDatasetKey.SHOGUN_FLASH_SHIPMENT)
        
        # 便利メソッド
        data = fetcher.get_final_receive(start_date=...)
        data = fetcher.get_flash_shipment(limit=1000)
    """
    
    # dataset_key → view name のマッピング
    _VIEW_MAP = {
        ShogunDatasetKey.SHOGUN_FINAL_RECEIVE: V_ACTIVE_SHOGUN_FINAL_RECEIVE,
        ShogunDatasetKey.SHOGUN_FINAL_SHIPMENT: V_ACTIVE_SHOGUN_FINAL_SHIPMENT,
        ShogunDatasetKey.SHOGUN_FINAL_YARD: V_ACTIVE_SHOGUN_FINAL_YARD,
        ShogunDatasetKey.SHOGUN_FLASH_RECEIVE: V_ACTIVE_SHOGUN_FLASH_RECEIVE,
        ShogunDatasetKey.SHOGUN_FLASH_SHIPMENT: V_ACTIVE_SHOGUN_FLASH_SHIPMENT,
        ShogunDatasetKey.SHOGUN_FLASH_YARD: V_ACTIVE_SHOGUN_FLASH_YARD,
    }
    
    def __init__(
        self,
        session: Session,
        name_mapper: Optional[ShogunMasterNameMapper] = None
    ):
        """
        コンストラクタ
        
        Args:
            session: SQLAlchemy Session（外部から注入）
            name_mapper: カラム名変換用マッパー（省略時は自動生成）
        """
        self.session = session
        self.name_mapper = name_mapper or ShogunMasterNameMapper()
    
    def fetch(
        self,
        dataset_key: Union[ShogunDatasetKey, ShogunDatasetKeyType],
        *,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None,
        schema: str = "stg",
    ) -> list[dict[str, Any]]:
        """
        指定したデータセットをDBから取得
        
        Args:
            dataset_key: データセットキー（Enum or 文字列）
            start_date: 開始日（伝票日付でフィルタ）
            end_date: 終了日（伝票日付でフィルタ）
            limit: 取得件数上限
            schema: スキーマ名（デフォルト: stg）
        
        Returns:
            list[dict]: 取得したデータ（カラム名は英語名）
        
        Raises:
            ShogunDatasetFetcherError: データセットキー不正、view未定義等
        
        例:
            data = fetcher.fetch(
                ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
                start_date=date(2024, 4, 1),
                end_date=date(2024, 10, 31),
                limit=10000
            )
        """
        # dataset_key を Enum に変換
        if isinstance(dataset_key, str):
            try:
                dataset_key = ShogunDatasetKey(dataset_key)
            except ValueError:
                raise ShogunDatasetFetcherError(
                    f"不正なdataset_key: {dataset_key}。"
                    f"有効な値: {[k.value for k in ShogunDatasetKey]}"
                )
        
        # view名を解決
        view_name = self._resolve_view_name(dataset_key, schema)
        
        # SQLクエリ構築
        query = self._build_query(
            view_name=view_name,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        # 実行
        logger.info(
            f"Fetching {dataset_key.value} from {view_name}",
            extra={
                "dataset_key": dataset_key.value,
                "view_name": view_name,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "limit": limit,
            }
        )
        
        try:
            result = self.session.execute(query)
            rows = result.mappings().all()
            
            # dict型に変換
            data = [dict(row) for row in rows]
            
            logger.info(
                f"Fetched {len(data)} rows from {view_name}",
                extra={"row_count": len(data)}
            )
            
            return data
        
        except Exception as e:
            logger.error(
                f"Failed to fetch {dataset_key.value} from {view_name}: {e}",
                extra={"error": str(e)},
                exc_info=True
            )
            raise ShogunDatasetFetcherError(
                f"データ取得失敗: {dataset_key.value} from {view_name}"
            ) from e
    
    def fetch_df(
        self,
        dataset_key: Union[ShogunDatasetKey, ShogunDatasetKeyType],
        **kwargs
    ) -> pd.DataFrame:
        """
        指定したデータセットをDataFrame形式で取得
        
        Args:
            dataset_key: データセットキー
            **kwargs: fetch() に渡す引数（start_date, end_date, limit等）
        
        Returns:
            pd.DataFrame: 取得したデータ
        
        例:
            df = fetcher.fetch_df(
                ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
                start_date=date(2024, 4, 1)
            )
        """
        data = self.fetch(dataset_key, **kwargs)
        return pd.DataFrame(data)
    
    # 便利メソッド（6種類）
    
    def get_final_receive(self, **kwargs) -> list[dict[str, Any]]:
        """受入一覧（確定）を取得"""
        return self.fetch(ShogunDatasetKey.SHOGUN_FINAL_RECEIVE, **kwargs)
    
    def get_final_shipment(self, **kwargs) -> list[dict[str, Any]]:
        """出荷一覧（確定）を取得"""
        return self.fetch(ShogunDatasetKey.SHOGUN_FINAL_SHIPMENT, **kwargs)
    
    def get_final_yard(self, **kwargs) -> list[dict[str, Any]]:
        """ヤード一覧（確定）を取得"""
        return self.fetch(ShogunDatasetKey.SHOGUN_FINAL_YARD, **kwargs)
    
    def get_flash_receive(self, **kwargs) -> list[dict[str, Any]]:
        """受入一覧（速報）を取得"""
        return self.fetch(ShogunDatasetKey.SHOGUN_FLASH_RECEIVE, **kwargs)
    
    def get_flash_shipment(self, **kwargs) -> list[dict[str, Any]]:
        """出荷一覧（速報）を取得"""
        return self.fetch(ShogunDatasetKey.SHOGUN_FLASH_SHIPMENT, **kwargs)
    
    def get_flash_yard(self, **kwargs) -> list[dict[str, Any]]:
        """ヤード一覧（速報）を取得"""
        return self.fetch(ShogunDatasetKey.SHOGUN_FLASH_YARD, **kwargs)
    
    # 内部メソッド
    
    def _resolve_view_name(self, dataset_key: ShogunDatasetKey, schema: str) -> str:
        """
        dataset_key から view名を解決
        
        Args:
            dataset_key: データセットキー
            schema: スキーマ名
        
        Returns:
            str: 完全修飾view名（例: "stg.v_active_shogun_final_receive"）
        
        Raises:
            ShogunDatasetFetcherError: view名が未定義の場合
        """
        base_view_name = self._VIEW_MAP.get(dataset_key)
        
        if not base_view_name:
            raise ShogunDatasetFetcherError(
                f"dataset_key {dataset_key.value} に対応するview名が未定義です。"
            )
        
        return f"{schema}.{base_view_name}"
    
    def _build_query(
        self,
        view_name: str,
        start_date: Optional[date],
        end_date: Optional[date],
        limit: Optional[int]
    ) -> text:
        """
        SQLクエリを構築
        
        Args:
            view_name: view名
            start_date: 開始日
            end_date: 終了日
            limit: 取得件数上限
        
        Returns:
            text: SQLクエリ
        """
        # ベースクエリ
        sql = f"SELECT * FROM {view_name}"
        
        # WHERE句
        conditions = []
        if start_date:
            conditions.append(f"slip_date >= '{start_date.isoformat()}'")
        if end_date:
            conditions.append(f"slip_date <= '{end_date.isoformat()}'")
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        # ORDER BY（常に伝票日付でソート）
        sql += " ORDER BY slip_date DESC"
        
        # LIMIT
        if limit:
            sql += f" LIMIT {limit}"
        
        return text(sql)
    
    def get_dataset_label(self, dataset_key: Union[ShogunDatasetKey, ShogunDatasetKeyType]) -> str:
        """
        データセットの日本語ラベルを取得
        
        Args:
            dataset_key: データセットキー
        
        Returns:
            str: 日本語ラベル（例: "受入一覧"）
        
        例:
            label = fetcher.get_dataset_label(ShogunDatasetKey.SHOGUN_FINAL_RECEIVE)
            # => "受入一覧"
        """
        if isinstance(dataset_key, str):
            dataset_key_str = dataset_key
        else:
            dataset_key_str = dataset_key.value
        
        return self.name_mapper.get_dataset_label(dataset_key_str)
