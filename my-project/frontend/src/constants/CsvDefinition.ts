import type { CsvType, CsvDefinition } from './types'; // 型定義は共通
import csvDefinitionsRaw from '@/config/csv_config/syogun_csv_masters.yaml';

import {
    parseShipmentCSV,
    parseReceiveCSV,
    parseYardCSV,
    // parsePayableCSV,
    // parseSalesSummaryCSV,
} from '@/parsers/csvParsers';

// onParse関数をCSVタイプごとにマッピング
const onParseMap: Partial<Record<CsvType, (text: string) => void>> = {
    shipment: parseShipmentCSV,
    receive: parseReceiveCSV,
    yard: parseYardCSV,
    // payable: parsePayableCSV,
    // sales_summary: parseSalesSummaryCSV,
};

// YAMLから各CsvDefinitionを生成
export const CSV_DEFINITIONS: Record<CsvType, CsvDefinition> =
    Object.fromEntries(
        Object.entries(csvDefinitionsRaw).map(([type, def]) => [
            type,
            {
                type: type as CsvType,
                label: def.label,
                expectedHeaders: def.expected_headers,
                onParse: onParseMap[type as CsvType]!,
            },
        ])
    ) as Record<CsvType, CsvDefinition>;
