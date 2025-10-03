// /app/src/utils/validators/csvValidator.ts

// CSVのヘッダを見て、正しいCSVかどうか判定するための関数

// CSV_DEFINITIONS から expectedHeaders を取得して
// text（CSVの中身）の1行目と比較することで、どのCSVテンプレートに当てはまるか判定する

import { CSV_DEFINITIONS } from '@shared/constants/CsvDefinition';

/**
 * CSVの先頭行（ヘッダー）を抽出
 */
function extractCsvHeader(csvText: string): string[] {
    const lines = csvText.trim().split(/\r?\n/);
    return lines.length > 0 ? lines[0].split(',').map((h) => h.trim()) : [];
}

/**
 * expectedHeaders と actualHeaders を先頭から順に比較
 */
function matchCsvHeaders(
    actual: string[],
    expected: string[],
    maxColumnsToCheck: number = expected.length
): boolean {
    for (let i = 0; i < maxColumnsToCheck; i++) {
        if (actual[i] !== expected[i]) return false;
    }
    return true;
}

/**
 * アップロードされたCSVがどの定義に一致するかを特定
 */
export function identifyCsvType(csvText: string): {
    type: string | null;
    matched: boolean;
    matchedType?: string;
    expectedHeaders?: string[];
} {
    const header = extractCsvHeader(csvText);

    for (const def of Object.values(CSV_DEFINITIONS)) {
        if (matchCsvHeaders(header, def.expectedHeaders)) {
            return {
                type: def.type,
                matched: true,
                matchedType: def.label,
                expectedHeaders: def.expectedHeaders,
            };
        }
    }

    return {
        type: null,
        matched: false,
    };
}

/**
 * 判定結果と期待されるラベルが一致するかどうかを確認
 */
export function isCsvMatch(
    result: ReturnType<typeof identifyCsvType>,
    expectedLabel: string
): boolean {
    return result.matched && result.matchedType === expectedLabel;
}
