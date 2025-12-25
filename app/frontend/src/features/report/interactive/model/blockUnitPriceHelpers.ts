// Business logic for block unit price interactive flow
import type {
  TransportCandidateRow,
  InteractiveItem,
  TransportVendor,
} from "@features/report/shared/types/interactive.types";

/**
 * 数値を配列の有効なインデックス範囲にクランプする
 */
export const clampIndex = (value: number, length: number): number => {
  if (length <= 0) return 0;
  if (!Number.isFinite(value)) return 0;
  const normalized = Math.trunc(value);
  if (normalized < 0) return 0;
  if (normalized >= length) return length - 1;
  return normalized;
};

/**
 * バックエンドから受け取った運搬候補行データを、UI用の InteractiveItem に変換する
 *
 * @remarks
 * - オプション配列を正規化（trim、空文字除去）
 * - initial_index が 0 の場合、「オネスト」があれば優先的に選択
 * - 不正な initial_index は clamp して範囲内に収める
 */
export const createInteractiveItemFromRow = (
  row: TransportCandidateRow,
): InteractiveItem => {
  const optionLabels = Array.isArray(row.options)
    ? row.options
        .map((opt) =>
          (typeof opt === "string" ? opt.trim() : String(opt ?? "")).trim(),
        )
        .filter((label) => label.length > 0)
    : [];
  const transport_options: TransportVendor[] = optionLabels.map((label) => ({
    code: label,
    name: label,
  }));

  const rawInitialIsZero =
    (typeof row.initial_index === "number" &&
      Math.trunc(row.initial_index) === 0) ||
    (typeof row.initial_index === "string" &&
      Number.parseInt(row.initial_index, 10) === 0);

  let initialSelectionIndex = clampIndex(
    typeof row.initial_index === "number" && Number.isFinite(row.initial_index)
      ? row.initial_index
      : typeof row.initial_index === "string"
        ? Number.parseInt(row.initial_index, 10)
        : Number(row.initial_index ?? 0),
    transport_options.length,
  );

  // initial_index が 0 でオネストが選択肢にあれば優先
  if (
    rawInitialIsZero &&
    initialSelectionIndex === 0 &&
    transport_options.length > 0
  ) {
    const honestIndex = transport_options.findIndex(
      (option) => option.name === "オネスト",
    );
    if (honestIndex >= 0) {
      initialSelectionIndex = honestIndex;
    }
  }

  return {
    id: String(row.entry_id ?? ""),
    vendor_code: String(row.vendor_code ?? ""),
    processor_name: row.vendor_name,
    product_name: row.item_name,
    note: row.detail ?? undefined,
    transport_options,
    initial_selection_index: initialSelectionIndex,
    rawRow: {
      ...row,
      options: optionLabels,
      initial_index: initialSelectionIndex,
    },
  } satisfies InteractiveItem;
};

/**
 * 選択状態から送信用ペイロードを構築する
 *
 * @param items - 全アイテムリスト
 * @param selections - ユーザーの選択状態（id => {index, label}）
 * @returns entry_id と transport_vendor のマップ
 */
export const buildSelectionPayload = (
  items: InteractiveItem[],
  selections: Record<string, { index: number; label: string }>,
): Record<string, string> => {
  const payload: Record<string, string> = {};

  items.forEach((item) => {
    const selection = selections[item.id];
    if (!selection) return;

    const transport_vendor =
      item.transport_options[selection.index]?.name ?? selection.label ?? "";
    const entry_id = String(item.rawRow?.entry_id ?? item.id ?? "");

    if (entry_id && transport_vendor) {
      payload[entry_id] = transport_vendor;
    }
  });

  return payload;
};
