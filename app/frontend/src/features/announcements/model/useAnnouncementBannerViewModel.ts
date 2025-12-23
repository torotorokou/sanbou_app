/**
 * useAnnouncementBannerViewModel - バナー用ViewModel
 * 
 * トップページに表示する重要通知バナーのロジック。
 * - pinned かつ severity が warn/critical のお知らせを対象
 * - 未確認（未ack）のもののうち1件を選択
 */

import { useState, useEffect, useCallback } from 'react';
import type { Announcement } from '../domain/announcement';
import { isBannerTarget } from '../domain/announcement';
import { announcementRepository } from '../infrastructure/LocalAnnouncementRepository';
import {
  isAcknowledged,
  markAsAcknowledged,
} from '../infrastructure/announcementUserStateStorage';

interface UseAnnouncementBannerViewModelResult {
  /** 表示すべきお知らせ（なければnull） */
  announcement: Announcement | null;
  /** ローディング中かどうか */
  isLoading: boolean;
  /** 確認済みにする関数 */
  onAcknowledge: () => void;
}

/**
 * バナー用ViewModel
 * 
 * @param userKey - ユーザー識別子（未ログイン時は"local"）
 */
export function useAnnouncementBannerViewModel(
  userKey: string = 'local'
): UseAnnouncementBannerViewModelResult {
  const [announcement, setAnnouncement] = useState<Announcement | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchBannerAnnouncement = async () => {
      try {
        const all = await announcementRepository.list();
        // バナー対象 かつ 未確認 のものを抽出
        const bannerCandidates = all.filter(
          (ann) => isBannerTarget(ann) && !isAcknowledged(userKey, ann.id)
        );
        // 最初の1件を選択（優先度が必要なら後で拡張）
        if (!cancelled) {
          setAnnouncement(bannerCandidates[0] ?? null);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchBannerAnnouncement();

    return () => {
      cancelled = true;
    };
  }, [userKey]);

  const onAcknowledge = useCallback(() => {
    if (announcement) {
      markAsAcknowledged(userKey, announcement.id);
      setAnnouncement(null);
    }
  }, [announcement, userKey]);

  return {
    announcement,
    isLoading,
    onAcknowledge,
  };
}
