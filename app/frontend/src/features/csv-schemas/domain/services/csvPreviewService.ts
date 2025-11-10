// features/csv/model/csvPreview.ts

export function parseCsvPreview(
    text: string,
    maxRows: number = 50
): { columns: string[]; rows: string[][] } {
    // 1. 改行ごとに分割し、空行を除外
    const lines = text.split(/\r?\n/).filter((l) => l.trim() !== '');
    if (lines.length === 0) return { columns: [], rows: [] };

    // 2. 最初の行をカラム名（ヘッダー）とみなす
    const columns = lines[0].split(',');

    // 3. 2行目以降をデータ行とみなして、maxRowsだけ取得
    const rows = lines.slice(1, maxRows + 1).map((row) => row.split(','));

    return { columns, rows };
}
