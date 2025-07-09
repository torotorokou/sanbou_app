// src/config/reportConfigs.ts
import { REPORT_OPTIONS } from '@/constants/reportOptions';

// --- CSVパース関数（仮） ---
const parseValuableCSV = (text: string) => {
    console.log('💎 受入CSV parsed', text);
};
const parseShipmentCSV = (text: string) => {
    console.log('🚚 出荷CSV parsed', text);
};
const parseWorkerCSV = (text: string) => {
    console.log('👷‍♂️ ヤードCSV parsed', text);
};

// --- 帳票ごとのconfig ---
export const reportConfigMap = {
    factory: {
        reportKey: 'factory',
        csvConfigs: [
            { label: '出荷CSV', onParse: parseShipmentCSV },
            { label: 'ヤードCSV', onParse: parseWorkerCSV },
        ],
        steps: ['データ選択', 'PDF生成中', '完了'],
        generatePdf: async () => '/factory_report.pdf',
    },
    attendance: {
        reportKey: 'attendance',
        csvConfigs: [
            { label: '受入CSV', onParse: parseValuableCSV },
            { label: '出荷CSV', onParse: parseShipmentCSV },
            { label: 'ヤードCSV', onParse: parseWorkerCSV },
        ],
        steps: ['CSV読み込み', '帳票作成中', '完了'],
        generatePdf: async () => '/attendance_report.pdf',
    },
    // abc, block, management も必要に応じて同様に追加
};

// --- 型補助: 選択肢のvalue一覧をtype化（拡張性向上のため） ---
export type ReportKey = (typeof REPORT_OPTIONS)[number]['value'];

// --- config取得ヘルパー ---
export function getReportConfig(key: ReportKey) {
    return reportConfigMap[key];
}
