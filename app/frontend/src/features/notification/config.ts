export const NOTIFY_DEFAULTS = {
  successMs: 4000,
  infoMs: 5000,
  warningMs: 5000,
  errorMs: 6000,
  persistent: null as number | null, // 自動削除しない
} as const;
