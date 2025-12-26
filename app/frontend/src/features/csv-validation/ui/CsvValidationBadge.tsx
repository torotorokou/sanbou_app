/**
 * CsvValidationBadge - CSV バリデーション専用のステータスバッジ
 *
 * @/shared/ui/ValidationBadge のCSV用ラッパー
 * CSV アップロード機能で使用するバリデーションステータスを表示
 *
 * 使用例:
 * ```tsx
 * import { CsvValidationBadge } from '@features/csv-validation';
 *
 * <CsvValidationBadge status="valid" />  // 緑の「OK」バッジ
 * <CsvValidationBadge status="invalid" /> // 赤の「NG」バッジ
 * <CsvValidationBadge status="unknown" /> // グレーの「未検証」バッジ
 * ```
 */

import React from 'react';
import { ValidationBadge } from '@/shared/ui';
import type { CsvValidationStatus } from '../model/validationStatus';

export interface CsvValidationBadgeProps {
  /**
   * CSV バリデーションステータス
   * - 'valid': バリデーション成功（緑・OK）
   * - 'invalid': バリデーション失敗（赤・NG）
   * - 'unknown': 未検証（グレー・未検証）
   */
  status: CsvValidationStatus;
  /**
   * バッジのサイズ
   * - 'small': コンパクト表示（13px）
   * - 'default': 通常表示（14px）
   * @default 'default'
   */
  size?: 'small' | 'default';
}

/**
 * CSV バリデーションステータスを表示するバッジコンポーネント
 *
 * @/shared/ui/ValidationBadge の薄いラッパーで、CSV 特化の型を提供
 * 実装は共通コンポーネントに委譲し、型レベルでの CSV 特化を実現
 */
export const CsvValidationBadge: React.FC<CsvValidationBadgeProps> = ({
  status,
  size = 'default',
}) => {
  return <ValidationBadge status={status} size={size} />;
};
