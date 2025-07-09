// src/constants/reportManage.ts

import {
    parseReceiveCSV,
    parseShipmentCSV,
    parseYardCSV,
} from '@/parsers/csvParsers';

//
// ==============================
// 🧩 帳票定義（キー + ラベル）
// ==============================
//

export const REPORT_KEYS = {
    factory: { value: 'factory', label: '工場日報' },
    attendance: { value: 'attendance', label: '搬出入収支表' },
    abc: { value: 'abc', label: 'ABC集計表' },
    block: { value: 'block', label: 'ブロック単価表' },
    management: { value: 'management', label: '管理表' },
} as const;

export type ReportKey = keyof typeof REPORT_KEYS;
export const REPORT_OPTIONS = Object.values(REPORT_KEYS);

//
// =================================
// 📄 CSVファイル構成（帳票別）
// =================================
//

type CsvConfig = {
    label: string;
    onParse: (text: string) => void;
};

export const csvConfigMap: Record<ReportKey, CsvConfig[]> = {
    factory: [
        { label: '出荷CSV', onParse: parseShipmentCSV },
        { label: 'ヤードCSV', onParse: parseYardCSV },
    ],
    attendance: [
        { label: '受入CSV', onParse: parseReceiveCSV },
        { label: '出荷CSV', onParse: parseShipmentCSV },
        { label: 'ヤードCSV', onParse: parseYardCSV },
    ],
    abc: [{ label: '受入CSV', onParse: parseReceiveCSV }],
    block: [{ label: '出荷CSV', onParse: parseShipmentCSV }],
    management: [
        { label: '受入CSV', onParse: parseReceiveCSV },
        { label: '出荷CSV', onParse: parseShipmentCSV },
        { label: 'ヤードCSV', onParse: parseYardCSV },
    ],
};

//
// =====================================
// 🔁 ステップ構成（帳票ごとの進行表示）
// =====================================
//

export const stepConfigMap: Record<ReportKey, string[]> = {
    factory: ['CSV選択', 'PDF生成中', '完了'],
    attendance: ['CSV読み込み', '帳票生成', '完了'],
    abc: ['準備中'],
    block: ['準備中'],
    management: ['準備中'],
};

//
// ===================================
// 📤 PDF出力関数（帳票ごとに切替）
// ===================================
//

export const pdfGeneratorMap: Record<ReportKey, () => Promise<string>> = {
    factory: async () => '/factory_report.pdf',
    attendance: async () => '/attendance_report.pdf',
    abc: async () => '/abc_report.pdf',
    block: async () => '/block_report.pdf',
    management: async () => '/management_report.pdf',
};
