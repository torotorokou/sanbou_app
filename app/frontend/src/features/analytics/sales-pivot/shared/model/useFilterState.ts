/**
 * shared/model/useFilterState.ts
 * フィルター状態管理用カスタムフック
 */

import { useState, useEffect } from "react";
import type { Mode, SortKey, SortOrder, ID } from "./types";

/**
 * フィルター状態管理の戻り値
 */
export interface FilterState {
  // フィルターパネル用（API取得条件）
  mode: Mode;
  filterTopN: 10 | 20 | 50 | "all";
  filterSortBy: SortKey;
  filterOrder: SortOrder;
  repIds: ID[];
  filterIds: ID[];

  // セッター関数
  setMode: (mode: Mode) => void;
  setFilterTopN: (topN: 10 | 20 | 50 | "all") => void;
  setFilterSortBy: (sortBy: SortKey) => void;
  setFilterOrder: (order: SortOrder) => void;
  setRepIds: (ids: ID[]) => void;
  setFilterIds: (ids: ID[]) => void;

  // テーブル用（クライアント側処理）
  tableSortBy: SortKey;
  tableOrder: SortOrder;
  setTableSortBy: (sortBy: SortKey) => void;
  setTableOrder: (order: SortOrder) => void;
}

/**
 * フィルター関連の状態を管理するカスタムフック
 *
 * @description
 * - API取得条件用のフィルター状態
 * - テーブル表示用のソート状態
 * - フィルターパネルの並び順が変わったらテーブルの並び順も自動同期
 *
 * @returns {FilterState} フィルター状態とセッター関数
 */
export function useFilterState(): FilterState {
  // フィルターパネル用（API取得条件）
  const [mode, setMode] = useState<Mode>("customer");
  const [filterTopN, setFilterTopN] = useState<10 | 20 | 50 | "all">("all");
  const [filterSortBy, setFilterSortBy] = useState<SortKey>("amount");
  const [filterOrder, setFilterOrder] = useState<SortOrder>("desc");
  const [repIds, setRepIds] = useState<ID[]>([]);
  const [filterIds, setFilterIds] = useState<ID[]>([]);

  // テーブル用（クライアント側処理）
  const [tableSortBy, setTableSortBy] = useState<SortKey>("amount");
  const [tableOrder, setTableOrder] = useState<SortOrder>("desc");

  // フィルターパネルの並び順が変わったらテーブルの並び順も同期
  useEffect(() => {
    setTableSortBy(filterSortBy);
    setTableOrder(filterOrder);
  }, [filterSortBy, filterOrder]);

  return {
    mode,
    filterTopN,
    filterSortBy,
    filterOrder,
    repIds,
    filterIds,
    setMode,
    setFilterTopN,
    setFilterSortBy,
    setFilterOrder,
    setRepIds,
    setFilterIds,
    tableSortBy,
    tableOrder,
    setTableSortBy,
    setTableOrder,
  };
}
