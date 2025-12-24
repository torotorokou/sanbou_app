/**
 * useUnreadCount - 未読数取得フック（共通化）
 * 
 * お知らせの未読数を取得する共通ロジック。
 * 各UIコンポーネントから再利用可能。
 */

import { useAuth } from '@features/authStatus';
import { useUnreadAnnouncementCountViewModel } from '@features/announcements';

/**
 * 未読数を取得するカスタムフック
 */
export const useUnreadCount = () => {
  const { user } = useAuth();
  const userKey = user?.userId ?? 'local';
  const { unreadCount } = useUnreadAnnouncementCountViewModel(userKey);
  
  return unreadCount;
};
