/**
 * Announcement User State Storage - ユーザー状態永続化
 *
 * お知らせの既読・確認済み状態をlocalStorageに永続化。
 * userKeyごとに状態を分離（マルチユーザー対応準備）。
 */

/**
 * ユーザー状態の型
 */
export interface AnnouncementUserState {
  /** 既読日時（ID→ISO8601） */
  readAtById: Record<string, string>;
  /** 確認済み日時（ID→ISO8601） */
  ackAtById: Record<string, string>;
}

const STORAGE_VERSION = 'v1';
const STORAGE_KEY_PREFIX = 'announcements';

/**
 * ストレージキーを生成
 */
function getStorageKey(userKey: string): string {
  return `${STORAGE_KEY_PREFIX}.${STORAGE_VERSION}.${userKey}`;
}

/**
 * 初期状態
 */
function createInitialState(): AnnouncementUserState {
  return {
    readAtById: {},
    ackAtById: {},
  };
}

/**
 * ユーザー状態を読み込み
 *
 * @param userKey - ユーザー識別子（未ログイン時は"local"）
 * @returns ユーザー状態
 */
export function loadUserState(userKey: string): AnnouncementUserState {
  try {
    const key = getStorageKey(userKey);
    const raw = localStorage.getItem(key);
    if (!raw) {
      return createInitialState();
    }
    const parsed = JSON.parse(raw) as unknown;
    // 型チェック
    if (
      typeof parsed === 'object' &&
      parsed !== null &&
      'readAtById' in parsed &&
      'ackAtById' in parsed
    ) {
      return parsed as AnnouncementUserState;
    }
    // 不正な形式 → 初期化
    return createInitialState();
  } catch {
    // JSON壊れ等 → 初期化して復旧
    return createInitialState();
  }
}

/**
 * ユーザー状態を保存
 *
 * @param userKey - ユーザー識別子
 * @param state - 保存する状態
 */
export function saveUserState(userKey: string, state: AnnouncementUserState): void {
  try {
    const key = getStorageKey(userKey);
    localStorage.setItem(key, JSON.stringify(state));
    // 同一タブ内での変更通知用カスタムイベント
    window.dispatchEvent(new Event('announcement-storage-change'));
  } catch {
    // ストレージフル等 → 無視（最悪リロードで状態が消えるだけ）
    console.warn('[announcements] Failed to save user state');
  }
}

/**
 * お知らせを既読にする
 *
 * @param userKey - ユーザー識別子
 * @param announcementId - お知らせID
 */
export function markAsRead(userKey: string, announcementId: string): void {
  const state = loadUserState(userKey);
  if (!state.readAtById[announcementId]) {
    state.readAtById[announcementId] = new Date().toISOString();
    saveUserState(userKey, state);
  }
}

/**
 * お知らせを確認済みにする（バナーの「理解した」など）
 *
 * @param userKey - ユーザー識別子
 * @param announcementId - お知らせID
 */
export function markAsAcknowledged(userKey: string, announcementId: string): void {
  const state = loadUserState(userKey);
  if (!state.ackAtById[announcementId]) {
    state.ackAtById[announcementId] = new Date().toISOString();
    saveUserState(userKey, state);
  }
}

/**
 * お知らせが既読かどうかを判定
 *
 * @param userKey - ユーザー識別子
 * @param announcementId - お知らせID
 * @returns 既読ならtrue
 */
export function isRead(userKey: string, announcementId: string): boolean {
  const state = loadUserState(userKey);
  return !!state.readAtById[announcementId];
}

/**
 * お知らせが確認済みかどうかを判定
 *
 * @param userKey - ユーザー識別子
 * @param announcementId - お知らせID
 * @returns 確認済みならtrue
 */
export function isAcknowledged(userKey: string, announcementId: string): boolean {
  const state = loadUserState(userKey);
  return !!state.ackAtById[announcementId];
}

/**
 * 未読のお知らせ数を取得
 *
 * @param userKey - ユーザー識別子
 * @param announcementIds - 対象のお知らせID配列
 * @returns 未読数
 */
export function getUnreadCount(userKey: string, announcementIds: string[]): number {
  const state = loadUserState(userKey);
  return announcementIds.filter((id) => !state.readAtById[id]).length;
}
