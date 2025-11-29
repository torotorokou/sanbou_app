/**
 * Notification Feature - Public API
 * MVVM+SOLID アーキテクチャに準拠した barrel export
 */

// Domain Types
export * from './domain/types/notification.types';
export * from './domain/types/contract';
export * from './domain/config';

// Ports
export type { INotificationRepository } from './ports/repository';

// Model (Store & ViewModel)
export * from './model/useNotificationVM';

// Infrastructure - Job Service
export * from './infrastructure/jobService';

// UI Components
export { default as NotificationCenter } from './ui/components/NotificationCenter';
export { default as NotificationCenterAntd } from './ui/components/NotificationCenterAntd';
