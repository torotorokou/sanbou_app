// 型定義を直接定義
export type CsvType =
    | 'shipment'
    | 'receive'
    | 'yard'
    // 📝 テンプレート例文用 - 新しいCSV種類
    | 'performance_data'
    | 'transport_volume'
    | 'inventory_data'
    | 'quality_check'
    | 'operation_log'
    | 'environmental_data'
    | 'cost_data'
    | 'production_log';
// | 'payable'
// | 'sales_summary';

export interface CsvDefinition {
    type: CsvType;
    label: string;
    expectedHeaders: string[];
    onParse: (text: string) => void;
}

import {
    parseShipmentCSV,
    parseReceiveCSV,
    parseYardCSV,
    // parsePayableCSV,
    // parseSalesSummaryCSV,
} from '@/parsers/csvParsers';

// 直接定義で簡素化（正しいヘッダーを設定）
export const CSV_DEFINITIONS: Record<CsvType, CsvDefinition> = {
    shipment: {
        type: 'shipment',
        label: '出荷一覧',
        expectedHeaders: [
            '伝票日付',
            '出荷番号',
            '取引先名',
            '業者CD',
            '業者名',
        ],
        onParse: parseShipmentCSV,
    },
    receive: {
        type: 'receive',
        label: '受入一覧',
        expectedHeaders: [
            '伝票日付',
            '売上日付',
            '支払日付',
            '業者CD',
            '業者名',
        ],
        onParse: parseReceiveCSV,
    },
    yard: {
        type: 'yard',
        label: 'ヤード一覧',
        expectedHeaders: ['伝票日付', '取引先名', '品名', '正味重量', '数量'],
        onParse: parseYardCSV,
    },

    // 📝 テンプレート例文用 - 新しいCSV種類の定義
    performance_data: {
        type: 'performance_data',
        label: '実績データ',
        expectedHeaders: ['日付', '作業者ID', '作業時間', '生産量', '不良品数'],
        onParse: (text: string) =>
            console.log(
                'Template: Performance data parsed',
                text.slice(0, 100)
            ),
    },
    transport_volume: {
        type: 'transport_volume',
        label: '搬入量データ',
        expectedHeaders: ['搬入日', '車両番号', '品目', '重量', '運転手'],
        onParse: (text: string) =>
            console.log(
                'Template: Transport volume parsed',
                text.slice(0, 100)
            ),
    },
    inventory_data: {
        type: 'inventory_data',
        label: '在庫データ',
        expectedHeaders: [
            '品目コード',
            '品目名',
            '在庫数量',
            '単価',
            '最終更新日',
        ],
        onParse: (text: string) =>
            console.log('Template: Inventory data parsed', text.slice(0, 100)),
    },
    quality_check: {
        type: 'quality_check',
        label: '品質検査データ',
        expectedHeaders: [
            '検査日',
            'ロット番号',
            '検査項目',
            '合格基準',
            '判定',
        ],
        onParse: (text: string) =>
            console.log('Template: Quality check parsed', text.slice(0, 100)),
    },
    operation_log: {
        type: 'operation_log',
        label: '運営ログ',
        expectedHeaders: ['日時', '操作者', '操作内容', 'ステータス', '備考'],
        onParse: (text: string) =>
            console.log('Template: Operation log parsed', text.slice(0, 100)),
    },
    environmental_data: {
        type: 'environmental_data',
        label: '環境監視データ',
        expectedHeaders: ['測定日時', '測定地点', '温度', '湿度', 'PM2.5'],
        onParse: (text: string) =>
            console.log(
                'Template: Environmental data parsed',
                text.slice(0, 100)
            ),
    },
    cost_data: {
        type: 'cost_data',
        label: 'コストデータ',
        expectedHeaders: ['項目', '分類', '金額', '計上日', '備考'],
        onParse: (text: string) =>
            console.log('Template: Cost data parsed', text.slice(0, 100)),
    },
    production_log: {
        type: 'production_log',
        label: '生産ログ',
        expectedHeaders: [
            '生産日',
            '製品コード',
            '生産数量',
            '作業時間',
            '稼働率',
        ],
        onParse: (text: string) =>
            console.log('Template: Production log parsed', text.slice(0, 100)),
    },
    // payable: {
    //     type: 'payable',
    //     label: '支払一覧',
    //     expectedHeaders: ['支払先', '金額', '期日'],
    //     onParse: () => {}, // placeholder
    // },
    // sales_summary: {
    //     type: 'sales_summary',
    //     label: '売上サマリー',
    //     expectedHeaders: ['項目', '金額'],
    //     onParse: () => {}, // placeholder
    // },
};
