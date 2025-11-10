/**
 * PanelFileItem → FileState への変換マッパ
 * VM から受け取る panelFiles を安全に UI 用の型に変換
 */

import type { FileState } from './types';
import type { PanelFileItem } from '../../dataset-import/model/types';

/**
 * PanelFileItem[] を FileState[] に変換
 * required が undefined の場合は true として扱う（旧データ互換）
 */
export function toFileStates(panelFiles: PanelFileItem[]): FileState[] {
  return (panelFiles ?? []).map((p) => ({
    typeKey: p.typeKey,
    label: p.label,
    required: p.required !== false,
    status: p.status === 'valid' ? 'valid' : p.status === 'invalid' ? 'invalid' : 'unknown',
    missingHeaders: [], // 将来的に PanelFileItem に追加されたら p.missingHeaders を使用
  }));
}
