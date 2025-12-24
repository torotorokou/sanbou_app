/**
 * Portal Feature - Public API
 * Feature-Sliced Design に従ったエクスポート
 */

// UI Components
export { PortalCard } from './ui/PortalCard';
export { CardIcon } from './ui/CardIcon';
export { CardContent } from './ui/CardContent';
export { CardButton } from './ui/CardButton';

// Model (ViewModel & Hooks)
export { usePortalCardStyles } from './model/usePortalCardStyles';
export * from './model/colorUtils';
export type { PortalCardProps, Notice } from './model/types';

// Domain
export * from './domain/constants';

// Infrastructure
export { portalMenus } from './infrastructure/portalMenus';
