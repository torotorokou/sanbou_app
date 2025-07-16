export type CsvType =
    | 'shipment'
    | 'receive'
    | 'yard'
    | 'payable'
    | 'sales_summary';

export type CsvDefinition = {
    type: CsvType;
    label: string;
    onParse: (text: string) => void;
    expectedHeaders: string[];
};

import {
    parseShipmentCSV,
    parseReceiveCSV,
    parseYardCSV,
    // parsePayableCSV,
    // parseSalesSummaryCSV,
} from '@/parsers/csvParsers';

export const CSV_DEFINITIONS: Record<CsvType, CsvDefinition> = {
    shipment: {
        type: 'shipment',
        label: '出荷一覧',
        onParse: parseShipmentCSV,
        expectedHeaders: [
            '伝票日付',
            '出荷番号',
            '取引先名',
            '業者CD',
            '業者名',
        ],
    },
    receive: {
        type: 'receive',
        label: '受入一覧',
        onParse: parseReceiveCSV,
        expectedHeaders: [
            '伝票日付',
            '売上日付',
            '支払日付',
            '業者CD',
            '業者名',
        ],
    },
    yard: {
        type: 'yard',
        label: 'ヤード一覧',
        onParse: parseYardCSV,
        expectedHeaders: ['伝票日付', '取引先名', '品名', '正味重量', '数量'],
    },
    payable: {
        type: 'payable',
        label: '買掛一覧表',
        // onParse: parsePayableCSV,
        expectedHeaders: [
            '取引先CD',
            '取引先名',
            '繰越残高',
            '出金額',
            '税抜支払金額',
        ],
    },
    sales_summary: {
        type: 'sales_summary',
        label: '売上集計表',
        // onParse: parseSalesSummaryCSV,
        expectedHeaders: ['取引先CD', '取引先名', '金額'],
    },
};
