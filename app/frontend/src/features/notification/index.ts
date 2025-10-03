// features/notification/index.ts
// Public API for notification feature

// Types
export * from './model/notification.types';

// Store
export { useNotificationStore } from './model/notification.store';
export type { NotificationState } from './model/notification.store';

// Controller (notification functions)
export {
    notifySuccess,
    notifyError,
    notifyInfo,
    notifyWarning,
    notifyPersistent,
    notifyApiError,
} from './controller/notify';

// View components
export { NotificationCenter } from './view/NotificationCenter';
export { default as NotificationCenterAntd } from './view/NotificationCenterAntd';

// Config
export { NOTIFY_DEFAULTS } from './config';
