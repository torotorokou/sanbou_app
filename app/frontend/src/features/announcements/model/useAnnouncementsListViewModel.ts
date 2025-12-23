/**
 * useAnnouncementsListViewModel - 一覧用ViewModel
 * 
 * お知らせ一覧ページのロジック。
 * - 一覧取得
 * - 詳細表示の開閉
 * - 詳細を開いたら既読にする
 * - 期限・対象フィルタ適用
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import type { Announcement, AnnouncementSeverity, Audience } from '../domain/announcement';
import { isAnnouncementActive, isVisibleForAudience } from '../domain/announcement';
import { announcementRepository } from '../infrastructure/LocalAnnouncementRepository';
import {
  isRead,
  markAsRead,
  loadUserState,
} from '../infrastructure/announcementUserStateStorage';
import { stripMarkdownForSnippet } from '../domain/stripMarkdownForSnippet';

/**
 * 現在のユーザーオーディエンス
 * 
 * TODO: 将来的にはユーザープロファイル（認証情報/ユーザー設定）から取得する
 * 現在はデモ用に 'site:narita' を設定
 */
const CURRENT_AUDIENCE: Audience = 'site:narita';

/**
 * フィルタタブの種類
 */
export type AnnouncementFilterTab = 'all' | 'unread';

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
  isPinned: boolean;
  severity: AnnouncementSeverity;
  /** タグ（最大3個表示） */
  tags: string[];
  /** 添付があるかどうか */
  hasAttachments: boolean;
}

interface UseAnnouncementsListViewModelResult {
  /** お知らせ一覧（生データ） */
  announcements: Announcement[];
  /** 選択中のタブ */
  selectedTab: AnnouncementFilterTab;
  /** タブ切替 */
  setSelectedTab: (tab: AnnouncementFilterTab) => void;
  /** 重要・注意アイテム（warn/critical、タブフィルタ適用済み） */
  importantItems: AnnouncementDisplayItem[];
  /** その他アイテム（info等、タブフィルタ適用済み） */
  otherItems: AnnouncementDisplayItem[];
  /** 表示用に整形されたお知らせ一覧（全件） */
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
  // タブ状態
  const [selectedTab, setSelectedTab] = useState<AnnouncementFilterTab>('all');

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
    // 対象フィルタ適用後のお知らせで未読数を計算
    const visibleAnnouncements = announcements.filter((ann) =>
      isVisibleForAudience(ann, CURRENT_AUDIENCE)
    );
    return visibleAnnouncements.filter((ann) => !state.readAtById[ann.id]).length;
  }, [announcements, userKey, stateVersion]);

  /**
   * 対象フィルタ適用済みのお知らせ
   */
  const visibleAnnouncements = useMemo(() => {
    return announcements.filter((ann) =>
      isVisibleForAudience(ann, CURRENT_AUDIENCE)
    );
  }, [announcements]);

  /**
   * 表示用に整形されたアイテムを生成
   * 対象フィルタ適用済み
   */
  const displayItems = useMemo<AnnouncementDisplayItem[]>(() => {
    return visibleAnnouncements.map((ann) => {
      // 公開日をフォーマット
      const publishedDate = new Date(ann.publishFrom);
      const publishedLabel = publishedDate.toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      });

      // 本文スニペット（Markdown記号除去）
      const snippet = stripMarkdownForSnippet(ann.bodyMd, 120);

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

      // タグ（最大3個）
      const tags = ann.tags?.slice(0, 3) ?? [];

      // 添付有無
      const hasAttachments = (ann.attachments?.length ?? 0) > 0;

      return {
        id: ann.id,
        title: ann.title,
        publishedLabel,
        snippet,
        badges,
        isUnread: isUnread(ann.id),
        isPinned: false,
        severity: ann.severity,
        tags,
        hasAttachments,
      };
    });
  }, [visibleAnnouncements, isUnread]);

  /**
   * 重要・注意アイツム（warn/critical、タブフィルタ適用済み）
   */
  const importantItems = useMemo<AnnouncementDisplayItem[]>(() => {
    const important = displayItems.filter(
      (item) => item.severity === 'warn' || item.severity === 'critical'
    );
    if (selectedTab === 'unread') {
      return important.filter((item) => item.isUnread);
    }
    return important;
  }, [displayItems, selectedTab]);

  /**
   * その他アイテム（info等、タブフィルタ適用済み）
   */
  const otherItems = useMemo<AnnouncementDisplayItem[]>(() => {
    const other = displayItems.filter(
      (item) => item.severity !== 'warn' && item.severity !== 'critical'
    );
    if (selectedTab === 'unread') {
      return other.filter((item) => item.isUnread);
    }
    return other;
  }, [displayItems, selectedTab]);

  return {
    announcements,
    selectedTab,
    setSelectedTab,
    importantItems,
    otherItems,
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
