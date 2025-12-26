/**
 * BottomSheet UI Component
 * モバイルでページ内セクションナビゲーションを表示する
 *
 * FSD + MVVM準拠：
 * - 純UIコンポーネント（状態管理なし）
 * - Portal使用
 * - Backdrop click/ESC で閉じる
 * - Body scroll lock
 */
import React, { useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import styles from "./BottomSheet.module.css";

export interface BottomSheetProps {
  /** 開閉状態 */
  open: boolean;
  /** 閉じる処理 */
  onClose: () => void;
  /** タイトル */
  title?: string;
  /** コンテンツ */
  children: React.ReactNode;
  /** 高さ（デフォルト: 70%） */
  height?: string;
}

/**
 * BottomSheet Component
 */
export const BottomSheet: React.FC<BottomSheetProps> = ({
  open,
  onClose,
  title = "目次",
  children,
  height = "70%",
}) => {
  // ESCキーで閉じる
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) {
        onClose();
      }
    },
    [open, onClose],
  );

  useEffect(() => {
    if (open) {
      document.addEventListener("keydown", handleKeyDown);
      // Body scroll lock
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, handleKeyDown]);

  if (!open) return null;

  return createPortal(
    <div className={styles.overlay} onClick={onClose}>
      <div
        className={styles.sheet}
        style={{ height }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className={styles.header}>
          <div className={styles.handle} />
          <h3 className={styles.title}>{title}</h3>
        </div>
        <div className={styles.content}>{children}</div>
      </div>
    </div>,
    document.body,
  );
};
