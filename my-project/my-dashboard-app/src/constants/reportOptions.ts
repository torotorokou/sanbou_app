// src/constants/reportOptions.ts

export const REPORT_OPTIONS = [
    { value: 'factory', label: '工場日報' },
    { value: 'attendance', label: '搬出入収支表' },
    { value: 'abc', label: 'ABC集計表' },
    { value: 'block', label: 'ブロック単価表' },
    { value: 'management', label: '管理表' },
    // 他帳票追加可
];

// valueだけ抽出した定数（configで利用するため）
export const REPORT_KEYS = REPORT_OPTIONS.map((opt) => opt.value);
