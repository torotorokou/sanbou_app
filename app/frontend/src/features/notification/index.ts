// features/notification/index.ts
// Public API for notification feature

// Types
export * from './model/notification.types';
export type { ProblemDetails, NotificationEvent, Severity } from './model/contract';

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

// SSE Controller
export { startSSE, stopSSE, getSSEState } from './controller/sse';

// View components
export { NotificationCenter } from './view/NotificationCenter';
export { default as NotificationCenterAntd } from './view/NotificationCenterAntd';

// Config
export { NOTIFY_DEFAULTS, codeCatalog, getNotificationConfig } from './config';
