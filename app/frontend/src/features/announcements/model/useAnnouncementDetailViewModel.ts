/**
 * useAnnouncementDetailViewModel - 詳細ページ用ViewModel
 * 
 * お知らせ詳細ページのロジック。
 * - ID指定でお知らせ取得
 * - 初回表示時に既読化
 */

import { useState, useEffect, useCallback } from 'react';
import type { Announcement } from '../domain/announcement';
import { announcementRepository } from '../infrastructure';
import { useAnnouncementState } from './AnnouncementStateContext';

interface UseAnnouncementDetailViewModelResult {
  /** お知らせデータ */
  announcement: Announcement | null;
  /** ローディング中かどうか */
  isLoading: boolean;
  /** NotFound（IDが見つからない） */
  notFound: boolean;
}

/**
 * 詳細ページ用ViewModel
 * 
 * @param id - お知らせID
 * @param userKey - ユーザー識別子（未ログイン時は"local"）※現在は未使用
 */
export function useAnnouncementDetailViewModel(
  id: string,
  userKey: string = 'local'
): UseAnnouncementDetailViewModelResult {
  // userKey は将来のユーザー認証対応時に使用予定
  void userKey;

  const [announcement, setAnnouncement] = useState<Announcement | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  // 既読状態の変更を通知するための関数を取得
  const { notifyReadStateChanged } = useAnnouncementState();

  useEffect(() => {
    let cancelled = false;

    const fetchAndMarkRead = async () => {
      try {
        setIsLoading(true);
        setNotFound(false);

        const data = await announcementRepository.get(id);

        if (!cancelled) {
          if (data) {
            setAnnouncement(data);
            // 詳細ページ表示時に既読化（API経由）
            await announcementRepository.markRead(id);
            // 既読状態の変更を通知
            notifyReadStateChanged();
          } else {
            setNotFound(true);
          }
        }
      } catch (error) {
        console.error('Failed to fetch announcement:', error);
        if (!cancelled) {
          setNotFound(true);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchAndMarkRead();

    return () => {
      cancelled = true;
    };
  }, [id, notifyReadStateChanged]);

  return {
    announcement,
    isLoading,
    notFound,
  };
}
