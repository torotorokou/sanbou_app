/**
 * useAnnouncementBannerViewModel - バナー用ViewModel
 * 
 * トップページに表示する重要通知バナーのロジック。
 * - severity が warn/critical のお知らせを対象
 * - 未読のもののうち1件を選択（お知らせ一覧と既読状態を共有）
 * - 期限切れ・対象外は除外（API側でフィルタ済み）
 */

import { useState, useEffect, useCallback } from 'react';
import type { Announcement } from '../domain/announcement';
import { isBannerTarget } from '../domain/announcement';
import { announcementRepository } from '../infrastructure';
import { useAnnouncementState } from './AnnouncementStateContext';

interface UseAnnouncementBannerViewModelResult {
  /** 表示すべきお知らせ（なければnull） */
  announcement: Announcement | null;
  /** ローディング中かどうか */
  isLoading: boolean;
  /** 既読にする（バナーを閉じる）関数 */
  onAcknowledge: () => void;
  /** 詳細ページへ遷移する関数（既読にして遷移） */
  onNavigateToDetail: (navigateFn: () => void) => void;
}

/**
 * バナー用ViewModel
 * 
 * @param userKey - ユーザー識別子（未ログイン時は"local"）※現在は未使用
 */
export function useAnnouncementBannerViewModel(
  userKey: string = 'local'
): UseAnnouncementBannerViewModelResult {
  // userKey は将来のユーザー認証対応時に使用予定
  void userKey;

  const [announcement, setAnnouncement] = useState<Announcement | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // 既読状態の変更を通知するための関数を取得
  const { notifyReadStateChanged } = useAnnouncementState();

  useEffect(() => {
    let cancelled = false;

    const fetchBannerAnnouncement = async () => {
      try {
        const result = await announcementRepository.list();
        // バナー対象 かつ 未読 のものを抽出
        // readAtMap から未読を判定
        const bannerCandidates = result.announcements.filter(
          (ann) =>
            isBannerTarget(ann) &&
            (result.readAtMap?.[ann.id] === null || result.readAtMap?.[ann.id] === undefined)
        );
        // critical を優先、その後 warn
        bannerCandidates.sort((a, b) => {
          if (a.severity === 'critical' && b.severity !== 'critical') return -1;
          if (a.severity !== 'critical' && b.severity === 'critical') return 1;
          return 0;
        });
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
  }, []);

  const onAcknowledge = useCallback(async () => {
    if (announcement) {
      // 既読にしてバナーを閉じる（API経由）
      await announcementRepository.markRead(announcement.id);
      setAnnouncement(null);
      // 既読状態の変更を通知
      notifyReadStateChanged();
    }
  }, [announcement, notifyReadStateChanged]);

  const onNavigateToDetail = useCallback(async (navigateFn: () => void) => {
    if (announcement) {
      // 既読にしてから詳細ページへ遷移（API経由）
      await announcementRepository.markRead(announcement.id);
      setAnnouncement(null);
      // 既読状態の変更を通知
      notifyReadStateChanged();
      navigateFn();
    }
  }, [announcement, notifyReadStateChanged]);

  return {
    announcement,
    isLoading,
    onAcknowledge,
    onNavigateToDetail,
  };
}
