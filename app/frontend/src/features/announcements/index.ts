/**
 * Announcements Feature - お知らせ機能
 * 
 * Feature-Sliced Design (FSD) に基づいた構成。
 * 
 * 【エクスポート】
 * - Domain: Announcement型, severity型, 判定関数
 * - Repository: AnnouncementRepository（ポート）
 * - Infrastructure: LocalAnnouncementRepository, userStateStorage
 * - ViewModel: useAnnouncementBannerViewModel, useAnnouncementsListViewModel, useUnreadAnnouncementCountViewModel
 * - UI: AnnouncementBanner, AnnouncementList, AnnouncementDetailModal
 */

// Domain
export type {
  Announcement,
  AnnouncementSeverity,
  Audience,
  Attachment,
  NotificationChannel,
  NotificationPlan,
} from './domain/announcement';
export {
  isAnnouncementActive,
  isVisibleForAudience,
  isBannerTarget,
} from './domain/announcement';

// Ports
export type { AnnouncementRepository } from './ports/AnnouncementRepository';

// Infrastructure
export { LocalAnnouncementRepository, announcementRepository } from './infrastructure/LocalAnnouncementRepository';
export {
  loadUserState,
  saveUserState,
  markAsRead,
  markAsAcknowledged,
  isRead,
  isAcknowledged,
  getUnreadCount,
} from './infrastructure/announcementUserStateStorage';
export type { AnnouncementUserState } from './infrastructure/announcementUserStateStorage';

// ViewModel (Step Bで追加)
export { useAnnouncementBannerViewModel } from './model/useAnnouncementBannerViewModel';
export { useAnnouncementsListViewModel } from './model/useAnnouncementsListViewModel';
export type { AnnouncementDisplayItem, AnnouncementBadge, AnnouncementFilterTab, AnnouncementSortType } from './model/useAnnouncementsListViewModel';
export { useUnreadAnnouncementCountViewModel } from './model/useUnreadAnnouncementCountViewModel';
export { useAnnouncementDetailViewModel } from './model/useAnnouncementDetailViewModel';

// UI (Step Cで追加)
export { AnnouncementBanner } from './ui/AnnouncementBanner';
export { AnnouncementList } from './ui/AnnouncementList';
export { AnnouncementListItem } from './ui/AnnouncementListItem';
export { AnnouncementDetailModal } from './ui/AnnouncementDetailModal';
export { NewsMenuLabel } from './ui/NewsMenuLabel';
export { NewsMenuIcon } from './ui/NewsMenuIcon';
export { useUnreadCount } from './ui/useUnreadCount';
export { AnnouncementFilterTabs } from './ui/AnnouncementFilterTabs';
export { AnnouncementSortSelector } from './ui/AnnouncementSortSelector';
export { AnnouncementDetail } from './ui/AnnouncementDetail';
export { ResponsiveNotice } from './ui/ResponsiveNotice';
export type { ResponsiveNoticeProps } from './ui/ResponsiveNotice';
