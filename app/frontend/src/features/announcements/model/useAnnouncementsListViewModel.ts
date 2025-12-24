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
import { isVisibleForAudience } from '../domain/announcement';
import { announcementRepository } from '../infrastructure';
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
 * ソート種類
 */
export type AnnouncementSortType = 'date-desc' | 'date-asc' | 'severity';

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
  /** 選択中のソート種類 */
  sortType: AnnouncementSortType;
  /** ソート種類切替 */
  setSortType: (sort: AnnouncementSortType) => void;
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
 * @param userKey - ユーザー識別子（未ログイン時は"local"）※現在は未使用
 */
export function useAnnouncementsListViewModel(
  userKey: string = 'local'
): UseAnnouncementsListViewModelResult {
  // userKey は将来のユーザー認証対応時に使用予定
  void userKey;

  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAnnouncement, setSelectedAnnouncement] =
    useState<Announcement | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  // 既読状態マップ（API or localStorage から取得）
  const [readAtMap, setReadAtMap] = useState<Record<string, string | null>>({});
  // タブ状態
  const [selectedTab, setSelectedTab] = useState<AnnouncementFilterTab>('all');
  // ソート状態
  const [sortType, setSortType] = useState<AnnouncementSortType>('date-desc');

  useEffect(() => {
    let cancelled = false;

    const fetchAnnouncements = async () => {
      try {
        const result = await announcementRepository.list();
        if (!cancelled) {
          setAnnouncements(result.announcements);
          // 既読状態マップをセット（APIから取得）
          if (result.readAtMap) {
            setReadAtMap(result.readAtMap);
          }
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
    async (id: string) => {
      const ann = announcements.find((a) => a.id === id);
      if (ann) {
        // 既読にする（API経由）
        await announcementRepository.markRead(id);
        // ローカル状態を即座に更新
        setReadAtMap((prev) => ({
          ...prev,
          [id]: new Date().toISOString(),
        }));
        setSelectedAnnouncement(ann);
        setIsDetailOpen(true);
      }
    },
    [announcements]
  );

  const closeDetail = useCallback(() => {
    setSelectedAnnouncement(null);
    setIsDetailOpen(false);
  }, []);

  const isUnread = useCallback(
    (id: string): boolean => {
      // readAtMap から既読状態を判定
      return readAtMap[id] === null || readAtMap[id] === undefined;
    },
    [readAtMap]
  );

  const unreadCount = useMemo(() => {
    // 対象フィルタ適用後のお知らせで未読数を計算
    const filteredAnnouncements = announcements.filter((ann) =>
      isVisibleForAudience(ann, CURRENT_AUDIENCE)
    );
    return filteredAnnouncements.filter((ann) => 
      readAtMap[ann.id] === null || readAtMap[ann.id] === undefined
    ).length;
  }, [announcements, readAtMap]);

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
   * ソート関数
   */
  const sortItems = useCallback((items: AnnouncementDisplayItem[]): AnnouncementDisplayItem[] => {
    const sorted = [...items];
    
    switch (sortType) {
      case 'date-desc':
        // 日付降順（新しい順）
        sorted.sort((a, b) => {
          const dateA = new Date(visibleAnnouncements.find(ann => ann.id === a.id)?.publishFrom || 0);
          const dateB = new Date(visibleAnnouncements.find(ann => ann.id === b.id)?.publishFrom || 0);
          return dateB.getTime() - dateA.getTime();
        });
        break;
      case 'date-asc':
        // 日付昇順（古い順）
        sorted.sort((a, b) => {
          const dateA = new Date(visibleAnnouncements.find(ann => ann.id === a.id)?.publishFrom || 0);
          const dateB = new Date(visibleAnnouncements.find(ann => ann.id === b.id)?.publishFrom || 0);
          return dateA.getTime() - dateB.getTime();
        });
        break;
      case 'severity':
        // 重要度順（critical→warn→info）
        const severityOrder = { critical: 0, warn: 1, info: 2 };
        sorted.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);
        break;
    }
    
    return sorted;
  }, [sortType, visibleAnnouncements]);

  /**
   * 重要・注意アイツム（warn/critical、タブフィルタ・ソート適用済み）
   */
  const importantItems = useMemo<AnnouncementDisplayItem[]>(() => {
    const important = displayItems.filter(
      (item) => item.severity === 'warn' || item.severity === 'critical'
    );
    const filtered = selectedTab === 'unread' 
      ? important.filter((item) => item.isUnread)
      : important;
    return sortItems(filtered);
  }, [displayItems, selectedTab, sortItems]);

  /**
   * その他アイテム（info等、タブフィルタ・ソート適用済み）
   */
  const otherItems = useMemo<AnnouncementDisplayItem[]>(() => {
    const other = displayItems.filter(
      (item) => item.severity !== 'warn' && item.severity !== 'critical'
    );
    const filtered = selectedTab === 'unread'
      ? other.filter((item) => item.isUnread)
      : other;
    return sortItems(filtered);
  }, [displayItems, selectedTab, sortItems]);

  return {
    announcements,
    selectedTab,
    setSelectedTab,
    sortType,
    setSortType,
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
