/**
 * useUnreadAnnouncementCountViewModel - 未読数ViewModel
 * 
 * サイドバー用の軽量ViewModel。
 * 未読のお知らせ数を返す。
 * 対象フィルタ（audience）適用済み。
 */

import { useState, useEffect, useCallback } from 'react';
import type { Audience } from '../domain/announcement';
import { isVisibleForAudience } from '../domain/announcement';
import { announcementRepository } from '../infrastructure/LocalAnnouncementRepository';
import { getUnreadCount } from '../infrastructure/announcementUserStateStorage';

/**
 * 現在のユーザーオーディエンス
 * 
 * TODO: 将来的にはユーザープロファイル（認証情報/ユーザー設定）から取得する
 * 現在はデモ用に 'site:narita' を設定
 */
const CURRENT_AUDIENCE: Audience = 'site:narita';

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
 * @param userKey - ユーザー識別子（未ログイン時は"local"）
 */
export function useUnreadAnnouncementCountViewModel(
  userKey: string = 'local'
): UseUnreadAnnouncementCountViewModelResult {
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchTrigger, setFetchTrigger] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const fetchUnreadCount = async () => {
      try {
        setIsLoading(true);
        const all = await announcementRepository.list();
        // 対象フィルタ適用
        const visible = all.filter((ann) =>
          isVisibleForAudience(ann, CURRENT_AUDIENCE)
        );
        const ids = visible.map((ann) => ann.id);
        const count = getUnreadCount(userKey, ids);
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

    // localStorage変更を検知して自動再読み込み
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key && e.key.startsWith('announcements.v1.')) {
        fetchUnreadCount();
      }
    };

    // 同一タブ内での変更検知用カスタムイベント
    const handleCustomStorageChange = () => {
      fetchUnreadCount();
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('announcement-storage-change', handleCustomStorageChange);

    return () => {
      cancelled = true;
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('announcement-storage-change', handleCustomStorageChange);
    };
  }, [userKey, fetchTrigger]);

  const refetch = useCallback(() => {
    setFetchTrigger((v) => v + 1);
  }, []);

  return {
    unreadCount,
    isLoading,
    refetch,
  };
}
