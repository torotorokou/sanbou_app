// features/notification の使用例

// ✅ 推奨: features/notification から直接インポート
import {
    notifySuccess,
    notifyError,
    notifyInfo,
    notifyWarning,
    notifyPersistent,
    notifyApiError,
    useNotificationStore,
    NotificationCenter,
    NotificationCenterAntd,
    NOTIFY_DEFAULTS,
} from '@features/notification';

// ✅ 互換性: 既存のパスも動作（内部で @features/notification に転送）
import { notifySuccess as notifySuccess2 } from '@/utils/notify';
import { useNotificationStore as useNotificationStore2 } from '@stores';

// 基本的な使用
export function ExampleUsage() {
    const handleSuccess = () => {
        notifySuccess('保存完了', 'データが正常に保存されました');
    };

    const handleError = () => {
        notifyError('エラー', '処理に失敗しました');
    };

    const handleApiError = async () => {
        try {
            throw new Error('API Error');
        } catch (error) {
            notifyApiError(error, 'APIエラーが発生しました');
        }
    };

    const handlePersistent = () => {
        notifyPersistent('warning', '重要', 'この通知は手動で閉じるまで表示されます');
    };

    return (
        <div>
            <button onClick={handleSuccess}>成功通知</button>
            <button onClick={handleError}>エラー通知</button>
            <button onClick={handleApiError}>APIエラー通知</button>
            <button onClick={handlePersistent}>永続通知</button>
        </div>
    );
}

// ストアの直接使用
export function StoreUsage() {
    const { notifications, removeNotification, clearAllNotifications } = useNotificationStore();

    return (
        <div>
            <h3>通知一覧 ({notifications.length}件)</h3>
            {notifications.map(n => (
                <div key={n.id}>
                    <strong>{n.title}</strong>: {n.message}
                    <button onClick={() => removeNotification(n.id)}>削除</button>
                </div>
            ))}
            <button onClick={clearAllNotifications}>全て削除</button>
        </div>
    );
}

// 通知センターの配置
export function App() {
    return (
        <>
            {/* Ant Design版を使用 */}
            <NotificationCenterAntd />
            
            {/* または基本版を使用 */}
            {/* <NotificationCenter /> */}
            
            <ExampleUsage />
            <StoreUsage />
        </>
    );
}
