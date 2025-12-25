// features/csv/config/CsvDefinition.ts
export type CsvType = "shipment" | "receive" | "yard";

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
} from "@/features/csv-schemas/domain/services/csvParserService";

export const CSV_DEFINITIONS: Record<CsvType, CsvDefinition> = {
  shipment: {
    type: "shipment",
    label: "出荷一覧",
    expectedHeaders: ["伝票日付", "出荷番号", "取引先名", "業者CD", "業者名"],
    onParse: parseShipmentCSV,
  },
  receive: {
    type: "receive",
    label: "受入一覧",
    expectedHeaders: ["伝票日付", "売上日付", "支払日付", "業者CD", "業者名"],
    onParse: parseReceiveCSV,
  },
  yard: {
    type: "yard",
    label: "ヤード一覧",
    expectedHeaders: ["伝票日付", "取引先名", "品名", "正味重量", "数量"],
    onParse: parseYardCSV,
  },
};
