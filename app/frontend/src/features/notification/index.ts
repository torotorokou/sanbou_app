/**
 * Notification Feature - Public API
 * MVVM+SOLID アーキテクチャに準拠した barrel export
 */

// Domain Types
export type {
    NotificationType,
    Notification,
    CreateNotificationData,
} from './domain/types/notification.types';

export type {
    Severity,
    ProblemDetails,
    NotificationEvent,
} from './domain/types/contract';

export {
    NOTIFY_DEFAULTS,
    codeCatalog,
    getNotificationConfig,
} from './domain/config';

// Ports
export type { INotificationRepository } from './ports/repository';

// Model (Store & ViewModel)
export {
    useNotificationStore,
    startSSE,
    stopSSE,
    getSSEState,
    notifySuccess,
    notifyError,
    notifyWarning,
    notifyInfo,
    notifyApiError,
} from './model/useNotificationVM';

// Infrastructure - Job Service
export {
    pollJob,
    type JobStatusType,
    type JobStatus,
} from './infrastructure/jobService';

// UI Components
export { default as NotificationCenter } from './ui/components/NotificationCenter';
export { default as NotificationCenterAntd } from './ui/components/NotificationCenterAntd';
