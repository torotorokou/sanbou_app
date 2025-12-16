/**
 * CSV解析ユーティリティ
 * シンプルなヘッダー解析（先頭行のみ使用）
 */

export function parseHeader(csvText: string): string[] {
  const firstLine = (csvText.split(/\r?\n/)[0] ?? '').trim();
  return firstLine ? firstLine.split(',').map(s => s.trim()) : [];
}

/**
 * CSVテキストをパースして簡易的なプレビューデータを生成
 */
export function parseCsvPreview(csvText: string, maxRows: number = 100): {
  columns: string[];
  rows: string[][];
} {
  const lines = csvText.split(/\r?\n/).filter(line => line.trim().length > 0);
  
  if (lines.length === 0) {
    return { columns: [], rows: [] };
  }

  const columns = lines[0].split(',').map(s => s.trim());
  const rows = lines.slice(1, maxRows + 1).map(line =>
    line.split(',').map(s => s.trim())
  );

  return { columns, rows };
}
