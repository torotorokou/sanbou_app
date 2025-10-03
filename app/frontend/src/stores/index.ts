export { useManualsStore } from './manualsStore';
// Notification store は features/notification に移動しました
export { useNotificationStore } from '@features/notification';

// ここでまとめてエクスポートしておくと、インポート側で
// `import { useNotificationStore } from 'src/stores'` のように
// ルートから簡潔に参照できます。
