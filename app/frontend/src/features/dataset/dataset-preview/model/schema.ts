/**
 * CSV スキーマ定義（ヘッダー）
 *
 * 各 CSV タイプのヘッダー（列名）を定義
 */

export const CSV_SCHEMAS: Record<string, string[]> = {
  // 将軍_速報版
  shogun_flash_ship: [
    "伝票日付",
    "伝票番号",
    "荷主",
    "荷受人",
    "品名",
    "数量",
    "単位",
    "備考",
  ],
  shogun_flash_receive: [
    "入荷日",
    "伝票番号",
    "荷主",
    "品名",
    "数量",
    "単位",
    "保管場所",
  ],
  shogun_flash_yard: ["ヤード名", "保管品名", "在庫数量", "単位", "最終更新日"],

  // 将軍_最終版
  shogun_final_ship: [
    "伝票日付",
    "伝票番号",
    "荷主",
    "荷受人",
    "品名",
    "数量",
    "単位",
    "備考",
  ],
  shogun_final_receive: [
    "入荷日",
    "伝票番号",
    "荷主",
    "品名",
    "数量",
    "単位",
    "保管場所",
  ],
  shogun_final_yard: ["ヤード名", "保管品名", "在庫数量", "単位", "最終更新日"],

  // マニフェスト
  manifest_primary: [
    "交付番号",
    "交付年月日",
    "排出事業者名",
    "廃棄物名称",
    "数量",
    "運搬受託者名",
  ],
  manifest_secondary: [
    "交付番号",
    "処分受託者名",
    "処分方法",
    "処分終了日",
    "最終処分場所",
  ],
};

/**
 * typeKey からヘッダーを取得
 */
export function getHeadersByType(typeKey: string): string[] {
  return CSV_SCHEMAS[typeKey] ?? ["列1", "列2", "列3"];
}
