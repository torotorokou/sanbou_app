/**
 * useSectionNavViewModel
 * ページ内セクションナビゲーション用ViewModel
 *
 * FSD + MVVM準拠：
 * - 状態管理（isOpen）
 * - 操作（open/close/onSelect）
 * - スクロール/ルート遷移の処理
 */
import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import type { SectionNavItem } from "../domain/types/sectionNav.types";
import { logger } from "@/shared";

export interface UseSectionNavViewModelParams {
  /** セクションナビゲーション項目 */
  items: SectionNavItem[];
}

export interface UseSectionNavViewModelResult {
  /** BottomSheetの開閉状態 */
  isOpen: boolean;
  /** BottomSheetを開く */
  open: () => void;
  /** BottomSheetを閉じる */
  close: () => void;
  /** 項目選択時の処理 */
  onSelect: (item: SectionNavItem) => void;
}

/**
 * セクションナビゲーションViewModel
 */
export function useSectionNavViewModel(
  params: UseSectionNavViewModelParams,
): UseSectionNavViewModelResult {
  const { items } = params;
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  const open = useCallback(() => {
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
  }, []);

  const onSelect = useCallback(
    (item: SectionNavItem) => {
      logger.debug("[useSectionNavViewModel] onSelect:", item);

      if (item.kind === "scroll") {
        // ページ内スクロール
        const element = document.querySelector(item.target);
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "start" });
        } else {
          logger.warn(
            `[useSectionNavViewModel] Element not found: ${item.target}`,
          );
        }
      } else if (item.kind === "route") {
        // ページ遷移
        navigate(item.target);
      }

      // BottomSheetを閉じる
      close();
    },
    [navigate, close],
  );

  return {
    isOpen,
    open,
    close,
    onSelect,
  };
}
