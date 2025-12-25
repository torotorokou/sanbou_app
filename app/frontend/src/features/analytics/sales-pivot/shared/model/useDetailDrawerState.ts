/**
 * DetailDrawer状態管理フック
 * 詳細明細行表示用ドロワーの状態管理
 */

import { useState } from "react";
import type { DetailMode, DetailLine } from "./types";

export interface DetailDrawerState {
  detailDrawerOpen: boolean;
  detailDrawerLoading: boolean;
  detailDrawerTitle: string;
  detailDrawerMode: DetailMode | null;
  detailDrawerRows: DetailLine[];
  detailDrawerTotalCount: number;
  setDetailDrawerOpen: (open: boolean) => void;
  setDetailDrawerLoading: (loading: boolean) => void;
  setDetailDrawerTitle: (title: string) => void;
  setDetailDrawerMode: (mode: DetailMode | null) => void;
  setDetailDrawerRows: (rows: DetailLine[]) => void;
  setDetailDrawerTotalCount: (count: number) => void;
}

/**
 * DetailDrawer状態管理フック
 */
export function useDetailDrawerState(): DetailDrawerState {
  const [detailDrawerOpen, setDetailDrawerOpen] = useState<boolean>(false);
  const [detailDrawerLoading, setDetailDrawerLoading] =
    useState<boolean>(false);
  const [detailDrawerTitle, setDetailDrawerTitle] = useState<string>("");
  const [detailDrawerMode, setDetailDrawerMode] = useState<DetailMode | null>(
    null,
  );
  const [detailDrawerRows, setDetailDrawerRows] = useState<DetailLine[]>([]);
  const [detailDrawerTotalCount, setDetailDrawerTotalCount] =
    useState<number>(0);

  return {
    detailDrawerOpen,
    detailDrawerLoading,
    detailDrawerTitle,
    detailDrawerMode,
    detailDrawerRows,
    detailDrawerTotalCount,
    setDetailDrawerOpen,
    setDetailDrawerLoading,
    setDetailDrawerTitle,
    setDetailDrawerMode,
    setDetailDrawerRows,
    setDetailDrawerTotalCount,
  };
}
