/**
 * CSV Export - Pure Functions
 *
 * CSV生成とダウンロード機能
 */

import type { CustomerData } from "../../shared/domain/types";

/**
 * 文字列をCSVセル用にエスケープする
 */
function escapeCsvCell(value: string | number): string {
  const str = String(value);
  if (str.includes('"') || str.includes(",") || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

/**
 * 顧客データからCSV文字列を生成する
 *
 * @param customers - CustomerData配列
 * @returns UTF-8 BOM付きCSV文字列
 */
export function buildCustomerCsv(customers: CustomerData[]): string {
  const BOM = "\uFEFF";
  const headers = [
    "顧客コード",
    "顧客名",
    "合計重量(kg)",
    "合計金額(円)",
    "担当営業者",
  ];
  const headerLine = headers.map(escapeCsvCell).join(",");

  const dataLines = customers.map((customer) => {
    const row = [
      customer.key,
      customer.name,
      customer.weight,
      customer.amount,
      customer.sales,
    ];
    return row.map(escapeCsvCell).join(",");
  });

  return BOM + [headerLine, ...dataLines].join("\n");
}

/**
 * CSV文字列からBlobを生成してダウンロードする
 *
 * @param csvContent - CSV文字列
 * @param filename - ダウンロードファイル名
 */
export function downloadCsv(csvContent: string, filename: string): void {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();

  link.parentNode?.removeChild(link);
  window.URL.revokeObjectURL(url);
}
