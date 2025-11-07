/**
 * バリデーションルール定義
 */

export interface ValidationRule {
  field: string;
  required?: boolean;
  pattern?: RegExp;
  minLength?: number;
  maxLength?: number;
}

export const VALIDATION_RULES: Record<string, ValidationRule[]> = {
  // 将来的な拡張用
  // shogun_flash_ship: [
  //   { field: '伝票日付', required: true },
  //   { field: '荷主', required: true },
  // ],
};
