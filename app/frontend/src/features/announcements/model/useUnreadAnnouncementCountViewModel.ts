/**
 * useUnreadAnnouncementCountViewModel - 未読数ViewModel
 *
 * サイドバー用の軽量ViewModel。
 * 未読のお知らせ数を返す。
 * 対象フィルタ（audience）はAPI側で適用済み。
 */

import { useState, useEffect, useCallback } from "react";
import { announcementRepository } from "../infrastructure";
import { useAnnouncementState } from "./AnnouncementStateContext";

interface UseUnreadAnnouncementCountViewModelResult {
  /** 未読数 */
  unreadCount: number;
  /** ローディング中かどうか */
  isLoading: boolean;
  /** 未読数を再取得する */
  refetch: () => void;
}

/**
 * 未読数ViewModel
 *
 * @param userKey - ユーザー識別子（未ログイン時は"local"）※現在は未使用
 */
export function useUnreadAnnouncementCountViewModel(
  userKey: string = "local",
): UseUnreadAnnouncementCountViewModelResult {
  // userKey は将来のユーザー認証対応時に使用予定
  void userKey;

  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchTrigger, setFetchTrigger] = useState(0);

  // 既読状態の変更を検知
  const { readStateVersion } = useAnnouncementState();

  useEffect(() => {
    let cancelled = false;

    const fetchUnreadCount = async () => {
      try {
        setIsLoading(true);
        // APIから未読数を直接取得
        const count = await announcementRepository.getUnreadCount();
        if (!cancelled) {
          setUnreadCount(count);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchUnreadCount();

    return () => {
      cancelled = true;
    };
  }, [fetchTrigger, readStateVersion]); // readStateVersionを依存配列に追加

  const refetch = useCallback(() => {
    setFetchTrigger((v) => v + 1);
  }, []);

  return {
    unreadCount,
    isLoading,
    refetch,
  };
}
