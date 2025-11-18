// moved from ../individual_process/BlockUnitPriceInteractive.tsx
import React, { useState } from 'react';
import { legacyApiPost as apiPost } from '@features/report/shared/api/http.adapter';

interface TransportOption {
    vendor_code: string;
    vendor_name: string;
    transport_fee: number;
    weight_unit_price: number;
}

interface SessionData {
    df_shipment_json: string;
    master_csv_json: string;
    df_transport_cost_json: string;
    selections?: Record<string, string>;
}

interface ShipmentSummaryInfo {
    vendors: string[];
}


interface SelectionSummaryInfo {
    affected_records: Record<string, { transport_vendor: string; record_count: number }>;
}

interface ApiDataShape {
    message?: string;
    shipment_summary?: ShipmentSummaryInfo;
    transport_options?: TransportOption[];
    selection_summary?: SelectionSummaryInfo;
    summary?: {
        processed_records?: number;
        total_amount?: number;
        total_transport_fee?: number;
    };
    session_data?: SessionData;
}

interface ProcessState {
    step: number; // -1: 未開始 0: 運搬業者選択 1: 確認 2: 完了
    data?: ApiDataShape;
    sessionData?: SessionData;
    loading: boolean;
    error?: string;
}

type StartResponse =
    | { status: 'success'; data: ApiDataShape }
    | { status: 'error'; detail?: string };

type SelectResponse =
    | { status: 'success'; data: ApiDataShape }
    | { status: 'error'; detail?: string };

type FinalizeResponse =
    | { status: 'completed'; data: ApiDataShape }
    | { status: 'cancelled'; data?: ApiDataShape }
    | { status: 'error'; detail?: string };

const BlockUnitPriceInteractive: React.FC = () => {
    const [state, setState] = useState<ProcessState>({
        step: -1, // 未開始
        loading: false
    });

    const [files] = useState<Record<string, File>>({});
    const [transportSelections, setTransportSelections] = useState<Record<string, string>>({});

    // Step 0: 処理開始
    const startProcess = async () => {
        setState(prev => ({ ...prev, loading: true, error: undefined }));

        try {
            const response = await apiPost<StartResponse, { files: Record<string, File> }>(
                '/core_api/block_unit_price_interactive/start',
                { files }
            );

            if (response.status === 'success') {
                setState({
                    step: 0,
                    data: response.data,
                    sessionData: response.data.session_data,
                    loading: false
                });

                // 初期選択値を設定（デフォルトで最初の運搬業者を選択）
                const initialSelections: Record<string, string> = {};
                response.data.shipment_summary?.vendors?.forEach((vendor: string) => {
                    if (response.data.transport_options && response.data.transport_options.length > 0) {
                        initialSelections[vendor] = response.data.transport_options[0].vendor_code;
                    }
                });
                setTransportSelections(initialSelections);
            } else {
                setState(prev => ({ ...prev, loading: false, error: response.detail || 'エラー' }));
            }
    } catch {
            setState(prev => ({
                ...prev,
                loading: false,
                error: '処理開始中にエラーが発生しました'
            }));
        }
    };

    // Step 1: 運搬業者選択
    const selectTransportVendors = async () => {
        if (!state.sessionData) return;

        setState(prev => ({ ...prev, loading: true }));

        try {
            const response = await apiPost<SelectResponse, { session_data: SessionData; selections: Record<string, string> }>(
                '/core_api/block_unit_price_interactive/select-transport',
                { session_data: state.sessionData, selections: transportSelections }
            );

            if (response.status === 'success') {
                setState(prev => ({
                    ...prev,
                    step: 1,
                    data: response.data,
                    sessionData: response.data.session_data,
                    loading: false
                }));
            } else {
                setState(prev => ({ ...prev, loading: false, error: response.detail || 'エラー' }));
            }
    } catch {
            setState(prev => ({
                ...prev,
                loading: false,
                error: '運搬業者選択中にエラーが発生しました'
            }));
        }
    };

    // Step 2: 最終計算
    const finalizeCalculation = async (confirmed: boolean = true) => {
        if (!state.sessionData) return;

        setState(prev => ({ ...prev, loading: true }));

        try {
            const response = await apiPost<FinalizeResponse, { session_data: SessionData; confirmed: boolean }>(
                '/core_api/block_unit_price_interactive/finalize',
                { session_data: state.sessionData, confirmed }
            );

            if (response.status === 'completed') {
                setState(prev => ({
                    ...prev,
                    step: 2,
                    data: response.data,
                    loading: false
                }));
            } else if (response.status === 'cancelled') {
                // Step 1に戻る
                setState(prev => ({ ...prev, step: 0, loading: false }));
            } else {
                setState(prev => ({ ...prev, loading: false, error: response.detail || 'エラー' }));
            }
    } catch {
            setState(prev => ({
                ...prev,
                loading: false,
                error: '最終計算中にエラーが発生しました'
            }));
        }
    };

    // 運搬業者選択の変更
    const handleTransportSelection = (vendorName: string, transportVendorCode: string) => {
        setTransportSelections(prev => ({
            ...prev,
            [vendorName]: transportVendorCode
        }));
    };

    // ステップに応じたコンテンツをレンダリング
    const renderStepContent = () => {
        switch (state.step) {
            case -1:
                return (
                    <div className="step-content">
                        <h2>ブロック単価計算</h2>
                        <p>ファイルをアップロードして処理を開始してください。</p>
                        {/* ファイルアップロード コンポーネント */}
                        <button
                            onClick={startProcess}
                            disabled={state.loading || Object.keys(files).length === 0}
                            className="btn-primary"
                        >
                            {state.loading ? '処理中...' : '処理開始'}
                        </button>
                    </div>
                );

            case 0:
                return (
                    <div className="step-content">
                        <h2>Step 1: 運搬業者選択</h2>
                        <p>{state.data?.message}</p>

                        <div className="transport-selection">
                            <h3>運搬業者を選択してください：</h3>
                            {state.data?.shipment_summary?.vendors?.map((vendor: string) => (
                                <div key={vendor} className="vendor-selection">
                                    <label>{vendor}</label>
                                    <select
                                        value={transportSelections[vendor] || ''}
                                        onChange={(e) => handleTransportSelection(vendor, e.target.value)}
                                    >
                                        {state.data?.transport_options?.map((option: TransportOption) => (
                                            <option key={option.vendor_code} value={option.vendor_code}>
                                                {option.vendor_name} (運搬費: ¥{option.transport_fee.toLocaleString()})
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={selectTransportVendors}
                            disabled={state.loading}
                            className="btn-primary"
                        >
                            {state.loading ? '処理中...' : '選択を適用'}
                        </button>
                    </div>
                );

            case 1:
                return (
                    <div className="step-content">
                        <h2>Step 2: 選択内容確認</h2>
                        <p>{state.data?.message}</p>

                        <div className="selection-summary">
                            <h3>選択内容：</h3>
                            {Object.entries(state.data?.selection_summary?.affected_records || {}).map(([vendor, info]) => (
                                <div key={vendor} className="summary-row">
                                    <span>{vendor}</span>
                                    <span>→ {info.transport_vendor}</span>
                                    <span>({info.record_count}件)</span>
                                </div>
                            ))}
                        </div>

                        <div className="step-actions">
                            <button
                                onClick={() => setState(prev => ({ ...prev, step: 0 }))}
                                className="btn-secondary"
                            >
                                やり直す
                            </button>
                            <button
                                onClick={() => finalizeCalculation(true)}
                                disabled={state.loading}
                                className="btn-primary"
                            >
                                {state.loading ? '計算中...' : '確定して計算実行'}
                            </button>
                        </div>
                    </div>
                );

            case 2:
                return (
                    <div className="step-content">
                        <h2>Step 3: 計算完了</h2>
                        <p>{state.data?.message}</p>

                        <div className="calculation-results">
                            <div className="result-summary">
                                <p>処理済みレコード数: {state.data?.summary?.processed_records}</p>
                                <p>合計金額: ¥{state.data?.summary?.total_amount?.toLocaleString()}</p>
                                <p>運搬費合計: ¥{state.data?.summary?.total_transport_fee?.toLocaleString()}</p>
                            </div>

                            {/* 結果のテーブル表示やダウンロードボタンなど */}
                            <button className="btn-success">
                                結果をダウンロード
                            </button>
                        </div>

                        <button
                            onClick={() => setState({ step: -1, loading: false })}
                            className="btn-secondary"
                        >
                            新しい処理を開始
                        </button>
                    </div>
                );

            default:
                return <div>不明なステップです</div>;
        }
    };

    return (
        <div className="block-unit-price-interactive">
            {/* プログレスバー */}
            <div className="progress-bar">
                <div className={`step ${state.step >= 0 ? 'completed' : ''}`}>1. 初期処理</div>
                <div className={`step ${state.step >= 1 ? 'completed' : ''}`}>2. 運搬業者選択</div>
                <div className={`step ${state.step >= 2 ? 'completed' : ''}`}>3. 最終計算</div>
            </div>

            {/* エラー表示 */}
            {state.error && (
                <div className="error-message">
                    <p>エラー: {state.error}</p>
                </div>
            )}

            {/* メインコンテンツ */}
            {renderStepContent()}
        </div>
    );
};

export default BlockUnitPriceInteractive;
