export type CsvType = 'shipment' | 'receive' | 'yard';

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
} from '@/parsers/csvParsers';

export const CSV_DEFINITIONS: Record<CsvType, CsvDefinition> = {
    shipment: {
        type: 'shipment',
        label: '出荷一覧',
        onParse: parseShipmentCSV,
        expectedHeaders: ['日付', '出荷先', '品名', '数量', '金額'],
    },
    receive: {
        type: 'receive',
        label: '受入一覧',
        onParse: parseReceiveCSV,
        expectedHeaders: ['受入日', '現場名', '品名', '重量', '単価'],
    },
    yard: {
        type: 'yard',
        label: 'ヤード一覧',
        onParse: parseYardCSV,
        expectedHeaders: ['日付', 'ヤード名', '荷姿', '数量'],
    },
};
