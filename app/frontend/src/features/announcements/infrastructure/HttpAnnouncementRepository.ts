/**
 * HTTP Announcement Repository - API連携実装
 * 
 * バックエンドAPIからお知らせを取得する実装。
 * /core_api/announcements エンドポイントと連携。
 * 
 * 【Repository の責務】
 * - APIからアクティブなお知らせを取得
 * - 既読/確認状態をAPIに送信
 * - レスポンスをドメインモデルに変換
 */

import type { Announcement, AnnouncementSeverity, Audience, Attachment } from '../domain/announcement';
import type { AnnouncementRepository, AnnouncementListResponse, AnnouncementReadStateMap } from '../ports/AnnouncementRepository';
import { coreApi } from '@/shared';

// ==============================================
// API Response Types
// ==============================================

interface ApiAnnouncementListItem {
  id: number;
  title: string;
  severity: AnnouncementSeverity;
  tags: string[];
  publish_from: string;
  publish_to: string | null;
  audience: Audience;
  read_at: string | null;
  ack_at: string | null;
  created_at: string;
}

interface ApiAnnouncementListResponse {
  announcements: ApiAnnouncementListItem[];
  total: number;
  unread_count: number;
}

interface ApiAnnouncementDetail {
  id: number;
  title: string;
  body_md: string;
  severity: AnnouncementSeverity;
  tags: string[];
  publish_from: string;
  publish_to: string | null;
  audience: Audience;
  attachments: Array<{ label: string; url: string }>;
  notification_plan: { email: boolean; in_app: boolean } | null;
  read_at: string | null;
  ack_at: string | null;
  created_at: string;
  updated_at: string;
}

interface ApiUnreadCountResponse {
  unread_count: number;
}

// ==============================================
// API → Domain 変換
// ==============================================

/**
 * API一覧アイテムをドメインモデルに変換
 */
function toAnnouncementFromListItem(item: ApiAnnouncementListItem): Announcement {
  return {
    id: String(item.id),
    title: item.title,
    bodyMd: '', // 一覧では本文なし
    severity: item.severity,
    tags: item.tags,
    publishFrom: item.publish_from,
    publishTo: item.publish_to,
    audience: item.audience,
    attachments: [],
    notification: undefined,
  };
}

/**
 * API詳細をドメインモデルに変換
 */
function toAnnouncementFromDetail(detail: ApiAnnouncementDetail): Announcement {
  const attachments: Attachment[] = detail.attachments.map((att) => ({
    label: att.label,
    url: att.url,
  }));

  return {
    id: String(detail.id),
    title: detail.title,
    bodyMd: detail.body_md,
    severity: detail.severity,
    tags: detail.tags,
    publishFrom: detail.publish_from,
    publishTo: detail.publish_to,
    audience: detail.audience,
    attachments,
    notification: detail.notification_plan
      ? {
          channels: ['inApp'],
          sendOnPublish: detail.notification_plan.in_app,
        }
      : undefined,
  };
}

// ==============================================
// HTTP Repository Implementation
// ==============================================

/**
 * HTTP（API連携）リポジトリ実装
 */
export class HttpAnnouncementRepository implements AnnouncementRepository {
  /**
   * アクティブなお知らせ一覧を取得
   */
  async list(): Promise<AnnouncementListResponse> {
    const response = await coreApi.get<ApiAnnouncementListResponse>(
      '/core_api/announcements'
    );

    const announcements = response.announcements.map(toAnnouncementFromListItem);

    // 既読状態マップを構築
    const readAtMap: AnnouncementReadStateMap = {};
    for (const item of response.announcements) {
      readAtMap[String(item.id)] = item.read_at;
    }

    return {
      announcements,
      total: response.total,
      unreadCount: response.unread_count,
      readAtMap,
    };
  }

  /**
   * 指定IDのお知らせを取得
   */
  async get(id: string): Promise<Announcement | null> {
    try {
      const response = await coreApi.get<ApiAnnouncementDetail>(
        `/core_api/announcements/${id}`
      );
      return toAnnouncementFromDetail(response);
    } catch (error: unknown) {
      // 404 の場合は null を返す
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 404) {
          return null;
        }
      }
      throw error;
    }
  }

  /**
   * お知らせを既読にする
   */
  async markRead(id: string): Promise<void> {
    await coreApi.post(`/core_api/announcements/${id}/read`);
  }

  /**
   * お知らせを確認済みにする（critical用）
   */
  async markAcknowledged(id: string): Promise<void> {
    await coreApi.post(`/core_api/announcements/${id}/acknowledge`);
  }

  /**
   * 未読お知らせ数を取得
   */
  async getUnreadCount(): Promise<number> {
    const response = await coreApi.get<ApiUnreadCountResponse>(
      '/core_api/announcements/unread-count'
    );
    return response.unread_count;
  }
}

/**
 * HTTPリポジトリインスタンス
 */
export const httpAnnouncementRepository = new HttpAnnouncementRepository();
