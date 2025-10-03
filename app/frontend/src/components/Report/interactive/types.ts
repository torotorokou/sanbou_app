// Common types for interactive report flows (shared across interactive components)

export interface TransportCandidateRow {
    entry_id: string; // unified identifier from backend (previously row_index)
    vendor_code: number | string;
    vendor_name: string;
    item_name: string;
    detail?: string | null;
    options: string[];
    initial_index: number;
}

export interface TransportVendor {
    code: string;
    name: string;
}

export interface InteractiveItem {
    id: string; // 対象ID (row_index を文字列化)
    vendor_code: string;
    processor_name: string; // 処理業者名
    product_name: string; // 商品名
    note?: string; // 備考
    transport_options: TransportVendor[]; // 選択肢
    initial_selection_index: number;
    rawRow: TransportCandidateRow;
}

export interface InitialApiResponse {
    session_id: string;
    rows: TransportCandidateRow[];
}

// サーバーから往復するセッションデータ（session_id のみ保持）
export interface SessionData {
    session_id: string;
}

// no default export — consumers should import named types
