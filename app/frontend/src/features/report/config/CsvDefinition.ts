// 型定義を直接定義
export type CsvType = 'shipment' | 'receive' | 'yard';
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
} from '@features/csv/model/csvParsers';

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
