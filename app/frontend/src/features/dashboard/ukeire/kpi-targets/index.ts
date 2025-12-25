/**
 * KPI Targets Feature
 * 目標 KPI の表示
 */

// Model (ViewModel)
export { useTargetsVM, type AchievementMode, type UseTargetsVMParams } from './model/useTargetsVM';
export { useTargetMetrics } from './model/useTargetMetrics';

// UI
export {
  TargetCard,
  type TargetCardProps,
  type AchievementMode as TargetCardAchievementMode,
} from './ui/cards/TargetCard';
