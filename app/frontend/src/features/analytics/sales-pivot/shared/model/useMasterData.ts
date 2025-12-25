/**
 * マスタデータ状態管理フック
 * 営業担当者・顧客・商品のマスタデータ取得と管理
 */

import { useState, useEffect, useRef } from "react";
import type { ID, CategoryKind } from "./types";
import type { SalesPivotRepository } from "../infrastructure/salesPivot.repository";

export interface MasterDataState {
  reps: Array<{ id: ID; name: string }>;
  customers: Array<{ id: ID; name: string }>;
  items: Array<{ id: ID; name: string }>;
}

/**
 * マスタデータ状態管理フック
 * @param repository リポジトリインスタンス
 * @param categoryKind カテゴリ種別（廃棄物/有価物）
 * @param onError エラーハンドラ
 */
export function useMasterData(
  repository: SalesPivotRepository,
  categoryKind: CategoryKind,
  onError?: (message: string) => void,
): MasterDataState {
  const [reps, setReps] = useState<Array<{ id: ID; name: string }>>([]);
  const [customers, setCustomers] = useState<Array<{ id: ID; name: string }>>(
    [],
  );
  const [items, setItems] = useState<Array<{ id: ID; name: string }>>([]);

  // onErrorの最新の参照を保持（依存配列に含めないため）
  const onErrorRef = useRef(onError);
  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    const loadMasters = async () => {
      try {
        const [repData, custData, itemData] = await Promise.all([
          repository.getSalesReps(),
          repository.getCustomers(),
          repository.getItems(),
        ]);
        console.log("マスタデータ取得成功:", {
          営業: repData.length,
          顧客: custData.length,
          商品: itemData.length,
        });
        setReps(repData);
        setCustomers(custData);
        setItems(itemData);
      } catch (error) {
        console.error("マスタデータ取得エラー:", error);
        onErrorRef.current?.("マスタデータの取得に失敗しました。");
      }
    };
    loadMasters();
  }, [repository, categoryKind]);

  return { reps, customers, items };
}
