/**
 * useUnreadAnnouncementCountViewModel - 未読数ViewModel
 * 
 * サイドバー用の軽量ViewModel。
 * 未読のお知らせ数を返す。
 */

import { useState, useEffect, useCallback } from 'react';
import { announcementRepository } from '../infrastructure/LocalAnnouncementRepository';
import { getUnreadCount } from '../infrastructure/announcementUserStateStorage';

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
        const ids = all.map((ann) => ann.id);
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

    return () => {
      cancelled = true;
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
