import React, { useState, useCallback } from 'react';
import { Modal, Button, Steps, Spin, message, Card, Select } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import { getApiEndpoint } from '@/constants/reportConfig';
import type { ReportKey } from '@/constants/reportConfig';
import type { ReportArtifactResponse } from '@/hooks/data/useReportArtifact';

// 型定義（要件に合わせて整備）
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

// 選択適用のプレビュー応答（最低限 selection_summary を保持）
interface SelectionPreviewResponse {
    selection_summary?: Record<string, unknown>;
    [key: string]: unknown;
}

interface SelectionState {
    index: number;
    label: string;
}

// id => 選択された運搬業者情報
type SelectionMap = Record<string, SelectionState>;

const clampIndex = (value: number, length: number): number => {
    if (length <= 0) return 0;
    if (!Number.isFinite(value)) return 0;
    const normalized = Math.trunc(value);
    if (normalized < 0) return 0;
    if (normalized >= length) return length - 1;
    return normalized;
};

const createInteractiveItemFromRow = (row: TransportCandidateRow): InteractiveItem => {
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

interface BlockUnitPriceInteractiveModalProps {
    open: boolean;
    onClose: () => void;
    csvFiles: { [label: string]: File | null };
    reportKey: ReportKey;
    onSuccess: (response: ReportArtifactResponse) => void;
    // 親コンポーネントが既に initial API の応答を持っている場合、それを直接渡せるようにする
    initialApiResponse?: InitialApiResponse;
    initialSessionData?: SessionData;
}

/**
 * 選択UI：処理業者ごとに運搬業者を選択
 */
const TransportSelectionList: React.FC<{
    items: InteractiveItem[];
    selections: SelectionMap;
    onChange: (id: string, selection: SelectionState) => void;
}> = ({ items, selections, onChange }) => {
    return (
        <div>
            {items.map((item) => (
                <Card key={item.id} size="small" style={{ marginBottom: 8, padding: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ lineHeight: 1.25 }}>
                            {/* ID は表示しない（内部で保持） */}
                            <div style={{ fontSize: 13 }}><strong>処理業者：</strong> {item.processor_name}</div>
                            <div style={{ fontSize: 13 }}><strong>商品名：</strong> {item.product_name}</div>
                            <div style={{ fontSize: 12, color: '#666' }}><strong>備考：</strong> {item.note ?? '（なし）'}</div>
                        </div>
                        <div style={{ minWidth: 220 }}>
                            <div style={{ marginBottom: 4, fontSize: 13 }}>運搬業者を選択</div>
                            <Select
                                style={{ width: 220 }}
                                placeholder="選択してください"
                                value={selections[item.id]?.index}
                                onChange={(selected) => {
                                    const idx = typeof selected === 'number' ? selected : Number(selected);
                                    const clamped = Number.isFinite(idx) ? Math.max(0, Math.min(idx, item.transport_options.length - 1)) : 0;
                                    const label = item.transport_options[clamped]?.name ?? '';
                                    onChange(item.id, { index: clamped, label });
                                }}
                                options={item.transport_options.map((v, optionIndex) => ({ value: optionIndex, label: v.name }))}
                            />
                        </div>
                    </div>
                </Card>
            ))}
        </div>
    );
};

/**
 * ブロック単価表専用インタラクティブモーダル
 * 
 * 🎯 目的：
 * - ブロック単価表専用の複数ステップフロー管理
 * - ユーザー入力を含むAPI複数回やり取り
 * - 共通モーダルと分離したカスタマイズ可能UI
 * 
 * 🔄 フロー：
 * 1. CSVアップロード（完了済み前提）
 * 2. 基本情報API送信 → 選択肢受信
 * 3. ユーザー選択入力
 * 4. 最終API送信 → ZIP受信
 */
const BlockUnitPriceInteractiveModal: React.FC<BlockUnitPriceInteractiveModalProps> = ({
    open,
    onClose,
    reportKey,
    onSuccess,
    initialApiResponse,
    initialSessionData,
}) => {
    // start at selection step (index 0)
    const [currentStep, setCurrentStep] = useState(0);
    const [processing, setProcessing] = useState(false);
    const [initialData, setInitialData] = useState<InitialApiResponse | null>(null);
    const [items, setItems] = useState<InteractiveItem[]>([]);
    const [selections, setSelections] = useState<SelectionMap>({});
    const [sessionData, setSessionData] = useState<SessionData | null>(null);
    const [selectionPreview, setSelectionPreview] = useState<SelectionPreviewResponse | null>(null);

    // ステップ定義
    // removed explicit "準備" step; modal now starts at 選択
    const steps = [
        { title: '選択', description: '処理業者ごとに運搬業者を選択' },
        { title: '確認', description: '選択内容を確認' },
        { title: '生成', description: '帳簿を生成中' },
        { title: '完了', description: '処理が完了しました' },
    ];

    // 初期データは親コンポーネントから渡される想定なので、モーダル内で自動取得は行わない

    /**
     * ローカルで選択のプレビューを作成（バックエンド呼び出しを行わないモード）
     */
    const buildLocalSelectionPreview = useCallback((): SelectionPreviewResponse => {
        const selection_summary: Record<string, {
            id?: string;
            entry_id?: string;
            processor_name?: string;
            vendor_code?: string;
            transport_vendor?: string;
            selected_index?: number;
        }> = {};
        try {
            items.forEach((it) => {
                const sel = selections[it.id];
                if (sel) {
                    const key = it.processor_name || it.id;
                    const optionLabel = it.transport_options[sel.index]?.name ?? sel.label;
                    selection_summary[key] = {
                        id: it.id,
                        entry_id: it.id,
                        processor_name: it.processor_name,
                        vendor_code: it.vendor_code,
                        transport_vendor: optionLabel,
                        selected_index: sel.index,
                    };
                }
            });
        } catch {
            // ignore
        }
        return { selection_summary };
    }, [items, selections]);

    /**
     * 確認画面で表示する、バックエンドに送る最終ペイロードを生成（表示専用）
     */
    const buildFinalizePayload = useCallback(() => {
        const selectionsById = Object.entries(selections).map(([id, selection]) => {
            const item = items.find((it) => it.id === id);
            return {
                id,
                entry_id: item?.id,
                processor_name: item?.processor_name,
                selected_index: selection.index,
                transport_vendor: item?.transport_options[selection.index]?.name ?? selection.label,
            };
        });

        // legacy selections map removed: we send id-based selections_by_id only

        return {
            session_id: sessionData?.session_id ?? '',
            // 明示的IDベースの配列（堅牢化）
            selections_by_id: selectionsById,
        } as Record<string, unknown>;
    }, [selections, sessionData, items]);

    /**
     * Step 3: 最終API呼び出し（アーティファクト生成）
     */
    const buildSelectionRequestPayload = useCallback(() => {
        // 送信フォーマットを縮小：entry_id と transport_vendor の配列にする
        const payload: Array<{ entry_id: string; transport_vendor: string }> = items
            .map((item) => {
                const selection = selections[item.id];
                if (!selection) return null;
                const transport_vendor = item.transport_options[selection.index]?.name ?? selection.label ?? '';
                const entry_id = String(item.rawRow?.entry_id ?? item.id ?? '');
                return { entry_id, transport_vendor };
            })
            .filter((v): v is { entry_id: string; transport_vendor: string } => v !== null && v.entry_id.length > 0);

        return payload;
    }, [items, selections]);

    const handleApplySelectionsAndFinalize = useCallback(async () => {
        const sessionId = sessionData?.session_id;
        if (!sessionId) {
            message.error('セッション情報が見つかりません。');
            return;
        }

        const selectionPayload = buildSelectionRequestPayload();
        if (selectionPayload.length === 0) {
            message.error('選択内容がありません。');
            setCurrentStep(1);
            return;
        }

        setCurrentStep(2);
        setProcessing(true);
        try {
            const apiEndpoint = getApiEndpoint(reportKey);
            const baseEndpoint = apiEndpoint.replace(/\/initial$/, '') || apiEndpoint.replace(/\/initial/, '');

            // 配列 -> { entry_id: transport_vendor } の map に変換して送信（backend が map を期待するため）
            const selectionPayloadMap: Record<string, string | number> = selectionPayload.reduce(
                (acc, cur) => {
                    if (cur && cur.entry_id) {
                        acc[cur.entry_id] = cur.transport_vendor;
                    }
                    return acc;
                },
                {} as Record<string, string | number>,
            );

            console.log('[BlockUnitPrice] apply payload (map):', { session_id: sessionId, selections: selectionPayloadMap });
            const applyResponse = await fetch(`${baseEndpoint}/apply`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    selections: selectionPayloadMap,
                }),
            });

            if (!applyResponse.ok) {
                throw new Error('選択内容の適用に失敗しました');
            }

            const applyJson = (await applyResponse.json()) as Record<string, unknown>;
            if (applyJson && typeof applyJson === 'object' && 'selection_summary' in applyJson) {
                setSelectionPreview({ selection_summary: applyJson.selection_summary as Record<string, unknown> });
            }

            console.log('[BlockUnitPrice] finalize payload (session_id only):', { session_id: sessionId });
            const finalizeResponse = await fetch(`${baseEndpoint}/finalize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                }),
            });

            if (!finalizeResponse.ok) {
                throw new Error('最終処理でエラーが発生しました');
            }

            const finalizeJson = (await finalizeResponse.json()) as ReportArtifactResponse;
            console.log('[BlockUnitPrice] finalize response (artifact):', finalizeJson);

            setCurrentStep(3);
            message.success('帳簿生成が完了しました');
            onSuccess(finalizeJson);

            setTimeout(() => {
                onClose();
            }, 1200);
        } catch (error) {
            console.error('Finalize flow failed:', error);
            message.error('帳簿生成に失敗しました');
            setCurrentStep(1);
        } finally {
            setProcessing(false);
        }
    }, [sessionData, buildSelectionRequestPayload, onSuccess, onClose, reportKey]);

    /**
     * ユーザー選択の更新
     */
    const handleSelectionChange = useCallback((id: string, selection: SelectionState) => {
        setSelections((prev) => ({ ...prev, [id]: selection }));
    }, []);

    /**
     * 次のステップへ進む
     */
    const handleNext = useCallback(() => {
        if (currentStep === 0) {
            // 選択 -> ローカルで確認プレビューを作成して確認ステップへ
            const preview = buildLocalSelectionPreview();
            setSelectionPreview(preview);
            setCurrentStep(1);
        } else if (currentStep === 1) {
            handleApplySelectionsAndFinalize();
        }
    }, [currentStep, buildLocalSelectionPreview, handleApplySelectionsAndFinalize]);

    /**
     * モーダルクローズ時のリセット
     */
    const handleClose = useCallback(() => {
        setCurrentStep(0);
        setInitialData(null);
        setItems([]);
        setSelections({});
        setSelectionPreview(null);
        setSessionData(null);
        setProcessing(false);
        onClose();
    }, [onClose]);

    // モーダルが開いた時、親から initialApiResponse/initialSessionData が渡されていれば
    // それを読み込んで選択UIを直接表示する（CSVのアップロードは親で行われる想定）。
    React.useEffect(() => {
        if (!open || !initialApiResponse) {
            return;
        }

        setInitialData(initialApiResponse);

        if (initialSessionData) {
            setSessionData(initialSessionData);
        } else if (initialApiResponse.session_id) {
            setSessionData({ session_id: initialApiResponse.session_id });
        }

        try {
            const normalizedItems = initialApiResponse.rows.map(createInteractiveItemFromRow);
            setItems(normalizedItems);

            const defaults: SelectionMap = {};
            normalizedItems.forEach((item) => {
                const vendor = item.transport_options[item.initial_selection_index];
                if (vendor) {
                    defaults[item.id] = {
                        index: item.initial_selection_index,
                        label: vendor.name,
                    };
                }
            });
            setSelections(defaults);
            setSelectionPreview(null);
        } catch (error) {
            console.error('Failed to normalize initial interactive rows:', error);
        }
        // 出力はモーダル内ではなくコンソールへ（開発用）
        try {
            console.log('[BlockUnitPrice] initialApiResponse:', initialApiResponse);
            console.log('[BlockUnitPrice] initialSessionData:', initialSessionData ?? (initialApiResponse?.session_id ? { session_id: initialApiResponse.session_id } : null));
        } catch {
            // noop
        }
    }, [open, initialApiResponse, initialSessionData]);

    React.useEffect(() => {
        if (currentStep !== 1) {
            return;
        }
        try {
            const previewData = selectionPreview ?? buildLocalSelectionPreview();
            console.log('[BlockUnitPrice] selection preview (confirm step):', previewData);
            console.log('[BlockUnitPrice] finalize payload (confirm step):', buildFinalizePayload());
        } catch (error) {
            console.error('Failed to build confirmation debug data:', error);
        }
    }, [currentStep, selectionPreview, buildLocalSelectionPreview, buildFinalizePayload]);

    return (
        <Modal
            title="ブロック単価表作成"
            open={open}
            onCancel={handleClose}
            width={800}
            footer={null}
            styles={{ body: { maxHeight: '70vh', padding: '20px 24px 24px', display: 'flex', flexDirection: 'column' } }}
        >
            <Steps current={currentStep} style={{ marginBottom: 24 }}>
                {steps.map((step) => (
                    <Steps.Step key={step.title} title={step.title} description={step.description} />
                ))}
            </Steps>

            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
                    {(processing && currentStep !== 3) && (
                        <div style={{ textAlign: 'center', padding: 40 }}>
                            <Spin size="large" />
                            {/* デバッグ情報はモーダル上に表示せずコンソールへ出力します */}
                        </div>
                    )}
                    {currentStep === 0 && !processing && initialData && items.length === 0 && (
                        <div style={{ textAlign: 'center', padding: 20 }}>
                            <p>運搬業者の選択が必要な行はありません。</p>
                        </div>
                    )}

                    {currentStep === 0 && !processing && items.length > 0 && (
                        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
                            <h4 style={{ marginBottom: 12 }}>処理業者ごとに運搬業者を選択してください</h4>
                            <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px 12px 0' }}>
                                <TransportSelectionList
                                    items={items}
                                    selections={selections}
                                    onChange={handleSelectionChange}
                                />
                            </div>
                        </div>
                    )}

                    {currentStep === 1 && !processing && items.length > 0 && (
                        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
                            <h4 style={{ marginBottom: 12 }}>選択内容の確認</h4>
                            <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px 12px 0' }}>
                                {items.map((item) => (
                                    <Card key={item.id} size="small" style={{ marginBottom: 8 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                                            <div style={{ flex: 1, lineHeight: 1.4 }}>
                                                <div><strong>処分業者：</strong> {item.processor_name}</div>
                                                <div><strong>商品名：</strong> {item.product_name}</div>
                                                <div><strong>備考：</strong> {item.note ?? '（なし）'}</div>
                                            </div>
                                            <div style={{ flex: 1, lineHeight: 1.4 }}>
                                                <div><strong>選択運搬業者：</strong> {selections[item.id]?.label || '未選択'}</div>
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                            </div>
                            <p style={{ marginTop: 12, color: '#666' }}>詳細なサマリーと送信内容はコンソールで確認できます。</p>
                        </div>
                    )}

                    {currentStep === 3 && (
                        <div style={{ textAlign: 'center', padding: 40 }}>
                            <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                            <h3 style={{ marginTop: 16 }}>完了しました！</h3>
                            <p>ブロック単価表が正常に生成されました。</p>
                        </div>
                    )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', marginTop: 24 }}>
                    {/* 左: 戻る */}
                    <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-start' }}>
                        {currentStep === 1 && !processing && (
                            <Button onClick={() => setCurrentStep(0)}>戻る</Button>
                        )}
                    </div>

                    {/* 中央: キャンセル/閉じる */}
                    <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
                        <Button onClick={handleClose}>
                            {currentStep >= 3 ? '閉じる' : 'キャンセル'}
                        </Button>
                    </div>

                    {/* 右: 実行系 */}
                    <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                        {currentStep === 0 && !processing && items.length > 0 && (
                            <Button
                                type="primary"
                                onClick={handleNext}
                                disabled={items.some(item => !selections[item.id])}
                            >
                                確認へ
                            </Button>
                        )}

                        {currentStep === 1 && !processing && (
                            <Button type="primary" onClick={handleNext}>進む</Button>
                        )}
                    </div>
                </div>
        </Modal>
    );
};

export default BlockUnitPriceInteractiveModal;
