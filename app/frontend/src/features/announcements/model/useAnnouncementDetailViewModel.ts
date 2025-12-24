/**
 * useAnnouncementDetailViewModel - 詳細ページ用ViewModel
 * 
 * お知らせ詳細ページのロジック。
 * - ID指定でお知らせ取得
 * - 初回表示時に既読化
 */

import { useState, useEffect } from 'react';
import type { Announcement } from '../domain/announcement';
import { announcementRepository } from '../infrastructure/LocalAnnouncementRepository';
import { markAsRead } from '../infrastructure/announcementUserStateStorage';

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
 * @param userKey - ユーザー識別子（未ログイン時は"local"）
 */
export function useAnnouncementDetailViewModel(
  id: string,
  userKey: string = 'local'
): UseAnnouncementDetailViewModelResult {
  const [announcement, setAnnouncement] = useState<Announcement | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

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
            // 詳細ページ表示時に既読化
            markAsRead(userKey, id);
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
  }, [id, userKey]);

  return {
    announcement,
    isLoading,
    notFound,
  };
}
