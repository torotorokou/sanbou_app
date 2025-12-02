// shared/index.ts
// shared 層の公開API - Single Source of Truth

// ===================================================
// Constants - ブレークポイント・定数
// ===================================================
export { 
  bp, 
  mq, 
  match, 
  ANT,  // @deprecated bp を使用してください
  BP, 
  tierOf, 
  isMobile, 
  isTabletOrHalf, 
  isDesktop,
  type BpKey,
  type AntKey,  // @deprecated
  type ViewportTier,
} from './constants/breakpoints';

// ===================================================
// Config - API Endpoints & Configuration
// ===================================================
export * from './config';

// ===================================================
// Utils - 日付・数値・汎用ユーティリティ
// ===================================================
export * from './utils/dateUtils';
export * from './utils/anchors';
export * from './utils/pdf/workerLoader';
export * from './utils/responsiveTest';

// ===================================================
// Theme - トークン・カラーマップ
// ===================================================
export * from './theme';

// ===================================================
// Infrastructure - HTTP/Job
// ===================================================
// ===================================================
// Infrastructure - HTTP Client
// ===================================================
export { 
  coreApi,
  apiGet, 
  apiPost, 
  apiGetBlob, 
  apiPostBlob,
  fetchWithTimeout,
  ApiError,
  client,
} from './infrastructure/http';

// ===================================================
// Utils - ユーティリティ
// ===================================================
export * from './utils';

// ===================================================
// Types - 型定義
// ===================================================
export * from './types';

// ===================================================
// Hooks - 公開Hook（推奨）
// ===================================================
export { 
  // レスポンシブ（推奨）
  useResponsive,
  // 内部実装（必要な場合のみ）
  useContainerSize,
  useScrollTracker,
  useSidebar,
} from './hooks/ui';

// ===================================================
// UI Components - 再利用可能なコンポーネント
// ===================================================
export * from './ui';

// ===================================================
// Styles - グローバルCSS（直接importで使用）
// ===================================================
// Note: styles/ はグローバルインポートで使用されるため、ここではエクスポートしない
// main.tsx等で直接 import '@shared/styles/base.css' してください
