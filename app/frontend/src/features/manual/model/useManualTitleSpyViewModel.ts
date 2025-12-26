/**
 * useManualTitleSpyViewModel
 * スクロール位置に応じて現在表示中のマニュアルセクションを追跡するViewModel
 *
 * FSD + MVVM準拠：
 * - IntersectionObserverでスクロール位置を監視
 * - 各セクションの sentinel要素を登録/管理
 * - 現在アクティブなセクションのID/タイトルを返す
 */
import { useState, useEffect, useCallback, useRef } from "react";
import type { ManualSection } from "../domain/types/shogun.types";
import { logger } from "@/shared";

export interface UseManualTitleSpyViewModelParams {
  /** マニュアルセクション一覧 */
  sections: ManualSection[];
  /** スクロールコンテナ（nullの場合はwindow） */
  scrollRoot?: HTMLElement | null;
  /** IntersectionObserver の rootMargin（デフォルト: '-80px 0px -70% 0px'） */
  rootMargin?: string;
}

export interface UseManualTitleSpyViewModelResult {
  /** 現在アクティブなセクションID */
  activeSectionId: string | null;
  /** 現在アクティブなセクションタイトル */
  activeTitle: string;
  /** Sentinel要素を登録するためのref関数 */
  registerSentinel: (
    sectionId: string,
  ) => (element: HTMLElement | null) => void;
}

/**
 * マニュアルタイトルScrollSpy ViewModel
 */
export function useManualTitleSpyViewModel(
  params: UseManualTitleSpyViewModelParams,
): UseManualTitleSpyViewModelResult {
  const { sections, scrollRoot, rootMargin = "-80px 0px -70% 0px" } = params;

  const [activeSectionId, setActiveSectionId] = useState<string | null>(
    sections.length > 0 ? sections[0].id : null,
  );

  // Sentinel要素の参照を保持
  const sentinelRefs = useRef<Map<string, HTMLElement>>(new Map());
  const observerRef = useRef<IntersectionObserver | null>(null);

  // セクションIDからタイトルを取得
  const activeTitle =
    sections.find((s) => s.id === activeSectionId)?.title ?? "";

  // Sentinel要素を登録
  const registerSentinel = useCallback((sectionId: string) => {
    return (element: HTMLElement | null) => {
      if (element) {
        sentinelRefs.current.set(sectionId, element);
        observerRef.current?.observe(element);
      } else {
        const existing = sentinelRefs.current.get(sectionId);
        if (existing) {
          observerRef.current?.unobserve(existing);
          sentinelRefs.current.delete(sectionId);
        }
      }
    };
  }, []);

  // IntersectionObserver のセットアップ
  useEffect(() => {
    if (sections.length === 0) {
      setActiveSectionId(null);
      return;
    }

    // Observer作成
    const observer = new IntersectionObserver(
      (entries) => {
        // 交差している要素を取得
        const intersecting = entries.filter((entry) => entry.isIntersecting);

        if (intersecting.length === 0) {
          // 何も交差していない場合は変更しない
          return;
        }

        // 複数交差している場合は、最も上にあるものを選択
        // boundingClientRect.top が最も小さい（画面上部に近い）ものを優先
        const topmost = intersecting.reduce((prev, curr) => {
          return curr.boundingClientRect.top < prev.boundingClientRect.top
            ? curr
            : prev;
        });

        const sectionId = (topmost.target as HTMLElement).dataset.sectionId;
        if (sectionId && sectionId !== activeSectionId) {
          logger.debug(
            "[useManualTitleSpyViewModel] Active section changed:",
            sectionId,
          );
          setActiveSectionId(sectionId);
        }
      },
      {
        root: scrollRoot,
        rootMargin,
        threshold: [0, 0.1, 0.5, 1.0],
      },
    );

    observerRef.current = observer;

    // 既存のsentinelを監視
    sentinelRefs.current.forEach((element) => {
      observer.observe(element);
    });

    return () => {
      observer.disconnect();
      observerRef.current = null;
    };
  }, [sections, scrollRoot, rootMargin, activeSectionId]);

  // sections変更時に初期状態をリセット
  useEffect(() => {
    if (sections.length > 0 && !activeSectionId) {
      setActiveSectionId(sections[0].id);
    }
  }, [sections, activeSectionId]);

  return {
    activeSectionId,
    activeTitle,
    registerSentinel,
  };
}
