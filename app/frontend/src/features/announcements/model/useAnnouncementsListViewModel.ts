/**
 * useAnnouncementsListViewModel - 一覧用ViewModel
 * 
 * お知らせ一覧ページのロジック。
 * - 一覧取得
 * - 詳細表示の開閉
 * - 詳細を開いたら既読にする
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import type { Announcement } from '../domain/announcement';
import { announcementRepository } from '../infrastructure/LocalAnnouncementRepository';
import {
  isRead,
  markAsRead,
  loadUserState,
} from '../infrastructure/announcementUserStateStorage';

/**
 * バッジ表示用データ
 */
export interface AnnouncementBadge {
  label: string;
  color: string;
}

/**
 * 表示用に整形されたお知らせアイテム
 */
export interface AnnouncementDisplayItem {
  id: string;
  title: string;
  publishedLabel: string;
  snippet: string;
  badges: AnnouncementBadge[];
  isUnread: boolean;
}

interface UseAnnouncementsListViewModelResult {
  /** お知らせ一覧（生データ） */
  announcements: Announcement[];
  /** 表示用に整形されたお知らせ一覧 */
  displayItems: AnnouncementDisplayItem[];
  /** ローディング中かどうか */
  isLoading: boolean;
  /** 詳細表示中のお知らせ（なければnull） */
  selectedAnnouncement: Announcement | null;
  /** 詳細モーダルが開いているかどうか */
  isDetailOpen: boolean;
  /** 詳細を開く */
  openDetail: (id: string) => void;
  /** 詳細を閉じる */
  closeDetail: () => void;
  /** 指定IDが未読かどうか */
  isUnread: (id: string) => boolean;
  /** 未読数 */
  unreadCount: number;
}

/**
 * 一覧用ViewModel
 * 
 * @param userKey - ユーザー識別子（未ログイン時は"local"）
 */
export function useAnnouncementsListViewModel(
  userKey: string = 'local'
): UseAnnouncementsListViewModelResult {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAnnouncement, setSelectedAnnouncement] =
    useState<Announcement | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  // 既読状態の変更を検知するためのカウンター
  const [stateVersion, setStateVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const fetchAnnouncements = async () => {
      try {
        const all = await announcementRepository.list();
        if (!cancelled) {
          setAnnouncements(all);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchAnnouncements();

    return () => {
      cancelled = true;
    };
  }, []);

  const openDetail = useCallback(
    (id: string) => {
      const ann = announcements.find((a) => a.id === id);
      if (ann) {
        // 既読にする
        markAsRead(userKey, id);
        setStateVersion((v) => v + 1);
        setSelectedAnnouncement(ann);
        setIsDetailOpen(true);
      }
    },
    [announcements, userKey]
  );

  const closeDetail = useCallback(() => {
    setSelectedAnnouncement(null);
    setIsDetailOpen(false);
  }, []);

  const isUnread = useCallback(
    (id: string): boolean => {
      // stateVersion に依存させることで再計算を促す
      void stateVersion;
      return !isRead(userKey, id);
    },
    [userKey, stateVersion]
  );

  const unreadCount = useMemo(() => {
    // stateVersion に依存させることで再計算を促す
    void stateVersion;
    const state = loadUserState(userKey);
    return announcements.filter((ann) => !state.readAtById[ann.id]).length;
  }, [announcements, userKey, stateVersion]);

  /**
   * 表示用に整形されたアイテムを生成
   */
  const displayItems = useMemo<AnnouncementDisplayItem[]>(() => {
    return announcements.map((ann) => {
      // 公開日をフォーマット
      const publishedDate = new Date(ann.publishFrom);
      const publishedLabel = publishedDate.toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      });

      // 本文スニペット（先頭80文字、改行除去）
      const snippet = ann.bodyMd
        .replace(/\n/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .substring(0, 80) + (ann.bodyMd.length > 80 ? '...' : '');

      // バッジを生成
      const badges: AnnouncementBadge[] = [];

      // 重要度バッジ
      switch (ann.severity) {
        case 'critical':
          badges.push({ label: '重要', color: 'red' });
          break;
        case 'warn':
          badges.push({ label: '注意', color: 'orange' });
          break;
        case 'info':
          badges.push({ label: '情報', color: 'blue' });
          break;
      }

      // ピン留めバッジ
      if (ann.pinned) {
        badges.push({ label: 'ピン留め', color: 'purple' });
      }

      return {
        id: ann.id,
        title: ann.title,
        publishedLabel,
        snippet,
        badges,
        isUnread: isUnread(ann.id),
      };
    });
  }, [announcements, isUnread]);

  return {
    announcements,
    displayItems,
    isLoading,
    selectedAnnouncement,
    isDetailOpen,
    openDetail,
    closeDetail,
    isUnread,
    unreadCount,
  };
}
