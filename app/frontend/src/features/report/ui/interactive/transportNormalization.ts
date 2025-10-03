import type { TransportCandidateRow, TransportVendor, InteractiveItem } from './types';

const clampIndex = (value: number, length: number): number => {
    if (length <= 0) return 0;
    if (!Number.isFinite(value)) return 0;
    const normalized = Math.trunc(value);
    if (normalized < 0) return 0;
    if (normalized >= length) return length - 1;
    return normalized;
};

export const isRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === 'object' && value !== null;

export const normalizeRow = (value: unknown): TransportCandidateRow | null => {
    if (!isRecord(value)) return null;

    const rawOptions = Array.isArray(value['options']) ? value['options'] : [];
    const options = rawOptions
        .map((opt) => (typeof opt === 'string' ? opt.trim() : String(opt ?? '')).trim())
        .filter((label) => label.length > 0);

    const initialIndexRaw = value['initial_index'];
    let initial_index = 0;
    if (typeof initialIndexRaw === 'number' && Number.isFinite(initialIndexRaw)) {
        initial_index = initialIndexRaw;
    } else if (typeof initialIndexRaw === 'string') {
        const parsed = Number.parseInt(initialIndexRaw, 10);
        if (Number.isFinite(parsed)) {
            initial_index = parsed;
        }
    }
    initial_index = Math.max(0, Math.trunc(initial_index));

    const detailValue = value['detail'];
    let detail: string | undefined;
    if (typeof detailValue === 'string') {
        detail = detailValue;
    } else if (detailValue != null) {
        detail = String(detailValue);
    }

    const entryIdCandidate = value['entry_id'];
    const vendorCodeCandidate = value['vendor_code'] ?? value['vendorId'];
    const vendorNameCandidate = value['vendor_name'] ?? value['processor_name'];
    const itemNameCandidate = value['item_name'] ?? value['product_name'];

    if (typeof entryIdCandidate !== 'string' && typeof entryIdCandidate !== 'number') {
        console.warn('normalizeRow: invalid entry_id type, skipping row:', typeof entryIdCandidate, entryIdCandidate);
        return null;
    }
    const entry_id = String(entryIdCandidate);

    return {
        entry_id,
        vendor_code: typeof vendorCodeCandidate === 'number' || typeof vendorCodeCandidate === 'string'
            ? vendorCodeCandidate
            : '',
        vendor_name: typeof vendorNameCandidate === 'string' ? vendorNameCandidate : String(vendorNameCandidate ?? ''),
        item_name: typeof itemNameCandidate === 'string' ? itemNameCandidate : String(itemNameCandidate ?? ''),
        detail,
        options,
        initial_index,
    } satisfies TransportCandidateRow;
};

export const createInteractiveItemFromRow = (row: TransportCandidateRow): InteractiveItem => {
    const optionLabels = Array.isArray(row.options)
        ? row.options
            .map((opt) => (typeof opt === 'string' ? opt.trim() : String(opt ?? '')).trim())
            .filter((label) => label.length > 0)
        : [];
    const transport_options: TransportVendor[] = optionLabels.map((label) => ({ code: label, name: label }));

    const rawInitialIsZero =
        (typeof row.initial_index === 'number' && Math.trunc(row.initial_index) === 0) ||
        (typeof row.initial_index === 'string' && Number.parseInt(row.initial_index, 10) === 0);

    let initialSelectionIndex = clampIndex(
        typeof row.initial_index === 'number' && Number.isFinite(row.initial_index)
            ? row.initial_index
            : typeof row.initial_index === 'string'
                ? Number.parseInt(row.initial_index, 10)
                : Number(row.initial_index ?? 0),
        transport_options.length,
    );

    if (rawInitialIsZero && initialSelectionIndex === 0 && transport_options.length > 0) {
        const honestIndex = transport_options.findIndex((option) => option.name === 'オネスト');
        if (honestIndex >= 0) {
            initialSelectionIndex = honestIndex;
        }
    }

    return {
        id: String(row.entry_id ?? ''),
        vendor_code: String(row.vendor_code ?? ''),
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

export { clampIndex };
