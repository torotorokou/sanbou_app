import React from 'react';
import { Modal, Button, Steps } from 'antd';
import type { InteractiveWorkflowProps } from '../../../types/interactiveWorkflow';
import { useWorkflow } from '../context/WorkflowContext';
import CsvUploadService from '../services/CsvUploadService';
import './BlockUnitPriceWorkflow.css';

// 自己完結型インタラクティブワークフローのprops
interface SelfContainedWorkflowProps extends Omit<InteractiveWorkflowProps, 'currentStep'> {
    visible?: boolean;
    onClose?: () => void;
    onComplete?: (result: any) => void;
    csvFile?: File;
}

// 検証結果の型定義
interface WorkflowValidation {
    canProceed: boolean;
    currentStep: number;
    isAllSelected: boolean;
}

// Window拡張の型定義
declare global {
    interface Window {
        blockUnitPriceWorkflowValidation?: WorkflowValidation;
    }
}
type TransporterRecord = {
    id: string;
    vendor_code: number;
    vendor_name: string;
    item_name: string;
    detail_note: string;
    transporters: string[];
};

type BackendResponse = {
    status: string;
    code: string;
    detail: string;
    result: TransporterRecord[];
};

// 運搬業者選択テーブルコンポーネントのプロパティ
interface TransporterSelectionTableProps {
    data: BackendResponse;
    onSelectionChange: (selections: Record<string, string>) => void;
    currentSelections: Record<string, string>;
}

// 運搬業者選択テーブルコンポーネント
/**
 * 運搬業者選択テーブル（Props-driven, 状態管理なし）
 * 
 * 🎯 設計原則:
 * - 内部状態を持たず、Propsでのみ制御される
 * - 全選択必須のバリデーション機能
 * - 進むボタンの状態制御
 * 
 * 💡 パフォーマンス最適化:
 * - React.useStateとuseEffectを削除し、Props-drivenに変更
 * - 依存配列を最小限に抑制したuseCallback
 */
const TransporterSelectionTable: React.FC<TransporterSelectionTableProps> = ({
    data,
    onSelectionChange,
    currentSelections
}) => {
    const handleSelectionChange = React.useCallback((itemId: string, transporter: string) => {
        const newSelections = { ...currentSelections, [itemId]: transporter };
        onSelectionChange(newSelections);
    }, [currentSelections, onSelectionChange]);

    // 全選択完了チェック
    const totalItems = data.result.length;
    const selectedItems = Object.keys(currentSelections).filter(key => currentSelections[key]).length;
    const isAllSelected = selectedItems === totalItems && totalItems > 0;

    return (
        <div className="transporter-selection-table">
            <h4>運搬業者選択</h4>
            <div className="selection-progress">
                <div className={`progress-indicator ${isAllSelected ? 'complete' : 'incomplete'}`}>
                    {isAllSelected ? '✅' : '⚠️'} 選択状況: {selectedItems} / {totalItems} 件
                    {!isAllSelected && <span className="warning-text"> - すべて選択してください</span>}
                </div>
            </div>

            <div className="table-container">
                <table className="selection-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>業者名</th>
                            <th>品目名</th>
                            <th>詳細</th>
                            <th>運搬業者選択</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.result.map((item) => (
                            <tr key={item.id} className={currentSelections[item.id] ? 'selected' : 'unselected'}>
                                <td>{item.id}</td>
                                <td>{item.vendor_name}</td>
                                <td>{item.item_name}</td>
                                <td>{item.detail_note}</td>
                                <td>
                                    <select
                                        value={currentSelections[item.id] || ''}
                                        onChange={(e) => handleSelectionChange(item.id, e.target.value)}
                                        className="transporter-select"
                                        required
                                    >
                                        <option value="">選択してください</option>
                                        {item.transporters.map((transporter, index) => (
                                            <option key={index} value={transporter}>
                                                {transporter}
                                            </option>
                                        ))}
                                    </select>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

/**
 * ブロック単価表専用ワークフローコンポーネント（無限ループ最適化済み）
 * 外部モーダルと統合されたシンプルな単一フロー設計
 * 
 * 🎯 責任：
 * - バックエンドデータの表示とユーザー入力の管理
 * - 外部モーダルのステップ制御との連携
 * - 複雑な入れ子モーダルを排除した直感的なUX
 * 
 * 🚀 パフォーマンス最適化:
 * - useRef による実行フラグ管理（useState回避）
 * - useCallback による関数の安定化
 * - 最小限の依存配列でuseEffect制御
 * - Props-drivenな子コンポーネント設計
 * 
 * 🔧 保守性向上:
 * - 専用ハンドラー関数で責任分離
 * - 型安全なデータフロー
 * - デバッグ情報の最小化
 */
const BlockUnitPriceWorkflow: React.FC<InteractiveWorkflowProps> = (props) => {
    const { currentStep, reportKey } = props;
    const { state, actions } = useWorkflow();

    // アクション関数を直接分割代入（useMemoで安定化済み）
    const { setLoading, setError, setBackendData, updateUserInputData, setCurrentStep } = actions;

    // 運搬業者選択変更時の専用ハンドラー（単純な関数参照）
    const handleTransporterSelection = React.useCallback((selections: Record<string, string>) => {
        updateUserInputData('transporterSelections', selections);
    }, [updateUserInputData]);

    // 全選択完了チェック関数
    const isAllTransportersSelected = React.useCallback(() => {
        if (!state.backendData) return false;

        const backendResponse = state.backendData as BackendResponse;
        const totalItems = backendResponse.result?.length || 0;
        const selections = state.userInputData.transporterSelections as Record<string, string> || {};
        const selectedItems = Object.keys(selections).filter(key => selections[key]).length;

        return totalItems > 0 && selectedItems === totalItems;
    }, [state.backendData, state.userInputData.transporterSelections]);

    // 現在のステップで次に進めるかどうかの検証（外部から参照可能）
    const canProceedToNextStep = React.useMemo(() => {
        switch (currentStep) {
            case 0:
                return !!state.backendData && !state.loading && !state.error;
            case 1:
                return isAllTransportersSelected() && !state.loading && !state.error;
            case 2:
                return !state.loading && !state.error; // 確認ステップ：常に進める
            case 3:
                return !state.loading && !state.error;
            default:
                return false;
        }
    }, [currentStep, state.backendData, state.loading, state.error, isAllTransportersSelected]);

    // 外部コンポーネントで使用可能なように、windowオブジェクトに検証関数を設定
    React.useEffect(() => {
        window.blockUnitPriceWorkflowValidation = {
            canProceed: canProceedToNextStep,
            currentStep,
            isAllSelected: isAllTransportersSelected()
        };

        return () => {
            delete window.blockUnitPriceWorkflowValidation;
        };
    }, [canProceedToNextStep, currentStep, isAllTransportersSelected]);

    // エラー時のリセット処理（ステップ1に戻る）
    const handleErrorReset = React.useCallback(() => {
        setError(null);
        setCurrentStep(1); // 運搬業者選択ステップに戻る
        // ユーザー入力データはクリアしない（既に選択した内容を保持）
    }, [setError, setCurrentStep]);

    // 最終データ送信のRef（状態の循環参照を避ける）
    const submitFinalDataRef = React.useRef<() => Promise<void>>();

    // 最終データ送信関数（状態を実行時に取得）
    submitFinalDataRef.current = async () => {
        setLoading(true);
        setError(null);

        try {
            const requestData = {
                originalData: state.backendData,
                userSelections: state.userInputData,
            };

            const result = await CsvUploadService.submitFinalData(
                reportKey,
                requestData,
                {
                    onStart: () => {
                        console.log('[BlockUnitPriceWorkflow] Starting final data submission');
                    },
                    onSuccess: (data) => {
                        console.log('[BlockUnitPriceWorkflow] Final calculation completed:', data);
                        setBackendData(data as Record<string, unknown>);
                    },
                    onError: (error) => {
                        console.error('[BlockUnitPriceWorkflow] Final submit error:', error);
                        setError(error);
                    },
                    onComplete: () => {
                        setLoading(false);
                    }
                }
            );

            if (!result.success) {
                throw new Error(result.error || 'Final submission failed');
            }

        } catch (error) {
            console.error('[BlockUnitPriceWorkflow] Final submit error:', error);
            setError(error instanceof Error ? error.message : 'Unknown error');
            setLoading(false);
        }
    };

    // ステップ3での自動実行用のRef（useEffectを使わないアプローチ）
    const step3ExecutedRef = React.useRef(false);

    // ステップ3での自動実行判定（useEffectを使わない、より安全なアプローチ）
    React.useMemo(() => {
        if (currentStep === 3 && !state.loading && !state.error && !step3ExecutedRef.current) {
            console.log('[BlockUnitPriceWorkflow] Triggering final data submission for step 3');
            step3ExecutedRef.current = true;

            // 非同期実行を次のイベントループで実行（レンダリングサイクルから分離）
            const timeoutId = setTimeout(() => {
                submitFinalDataRef.current?.();
            }, 0);

            // クリーンアップのためのrefを設定
            return () => clearTimeout(timeoutId);
        }

        // ステップが変わった場合、実行フラグをリセット
        if (currentStep !== 3) {
            step3ExecutedRef.current = false;
        }

        return null;
    }, [currentStep, state.loading, state.error]);

    // ステップ別のコンテンツレンダリング（外部モーダルのコンテンツエリア）
    const renderStepContent = () => {
        // 共通ローディング表示
        if (state.loading) {
            return (
                <div className="workflow-loading">
                    <div className="loading-spinner">⏳</div>
                    <h4>処理中...</h4>
                    <p>バックエンドで処理しています。しばらくお待ちください。</p>
                </div>
            );
        }

        // 共通エラー表示
        if (state.error) {
            return (
                <div className="workflow-error">
                    <div className="error-icon">❌</div>
                    <h4>エラーが発生しました</h4>
                    <p>{state.error}</p>
                    <button
                        onClick={handleErrorReset}
                        className="btn-retry"
                    >
                        ステップ1からやり直す
                    </button>
                </div>
            );
        }

        switch (currentStep) {
            case 0: // バックエンド処理待ち
                return (
                    <div className="workflow-step">
                        <div className="step-header">
                            <h4>データ処理中</h4>
                            <p>CSVファイルを解析しています...</p>
                        </div>

                        {state.backendData ? (
                            <div className="step-ready">
                                <div className="ready-icon">✅</div>
                                <p><strong>データ処理完了</strong></p>
                                <p>運搬業者の選択に進んでください。</p>
                            </div>
                        ) : (
                            <div className="step-processing">
                                <div className="processing-indicator">
                                    <div className="spinner">🔄</div>
                                    <span>処理中...</span>
                                </div>
                            </div>
                        )}
                    </div>
                );

            case 1: // 運搬業者選択
                return (
                    <div className="workflow-step">
                        <div className="step-header">
                            <h4>運搬業者選択</h4>
                            <p>各項目の運搬業者を選択してください</p>
                        </div>

                        {state.backendData && (
                            <TransporterSelectionTable
                                data={state.backendData as BackendResponse}
                                onSelectionChange={handleTransporterSelection}
                                currentSelections={state.userInputData.transporterSelections as Record<string, string> || {}}
                            />
                        )}
                    </div>
                );

            case 2: // 選択内容確認（バックエンド通信前）
                const selections = state.userInputData.transporterSelections as Record<string, string> || {};
                const backendResponse = state.backendData as BackendResponse;

                // 選択内容の詳細データを作成
                const selectionDetails = Object.entries(selections).map(([id, transporter]) => {
                    const record = backendResponse.result.find(rec => rec.id === id);
                    return {
                        id,
                        transporter,
                        vendorName: record?.vendor_name || 'Unknown',
                        itemName: record?.item_name || 'Unknown',
                        detailNote: record?.detail_note || ''
                    };
                });

                return (
                    <div className="workflow-step">
                        <div className="step-header">
                            <h4>選択内容の確認</h4>
                            <p>運搬業者の選択内容を確認してください。問題がなければ「次へ」、修正が必要であれば「前へ」を選択してください。</p>
                        </div>

                        <div className="confirmation-summary">
                            <h5>選択された運搬業者一覧：</h5>
                            <div className="selections-confirmation-table">
                                <table className="confirmation-table">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>業者名</th>
                                            <th>品目名</th>
                                            <th>詳細</th>
                                            <th>選択した運搬業者</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {selectionDetails.map(({ id, transporter, vendorName, itemName, detailNote }) => (
                                            <tr key={id} className="confirmation-row">
                                                <td>{id}</td>
                                                <td>{vendorName}</td>
                                                <td>{itemName}</td>
                                                <td>{detailNote}</td>
                                                <td className="selected-transporter-cell">
                                                    <span className="transporter-badge">{transporter}</span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            <div className="confirmation-summary-stats">
                                <div className="stats-item">
                                    <span className="stats-label">選択完了件数:</span>
                                    <span className="stats-value">{selectionDetails.length} 件</span>
                                </div>
                                <div className="confirmation-actions-hint">
                                    <p>✅ すべての選択が完了しています</p>
                                    <p>「次へ」をクリックしてバックエンド処理を開始するか、「戻る」で選択を変更できます。</p>
                                </div>
                            </div>
                        </div>
                    </div>
                );

            case 3: // バックエンド処理・計算実行
                return (
                    <div className="workflow-step">
                        <div className="step-header">
                            <h4>ブロック単価計算実行</h4>
                            <p>選択内容をもとにブロック単価の計算を実行しています</p>
                        </div>

                        <div className="calculation-status">
                            <div className="status-icon">⚙️</div>
                            <p>バックエンドで計算処理中...</p>
                            <div className="processing-indicator">
                                <div className="spinner">🔄</div>
                                <span>しばらくお待ちください</span>
                            </div>
                        </div>
                    </div>
                );

            case 4: // 完了
                return (
                    <div className="workflow-step">
                        <div className="step-header">
                            <h4>処理完了</h4>
                            <p>ブロック単価表の生成が完了しました</p>
                        </div>

                        <div className="completion-message">
                            <div className="success-icon">🎉</div>
                            <h5>✅ 生成完了</h5>
                            <p>PDFプレビューで結果をご確認ください。</p>
                            <p>ダウンロードボタンからファイルを取得できます。</p>
                        </div>
                    </div>
                );

            default:
                return (
                    <div className="workflow-step">
                        <div className="step-error">
                            <h4>不明なステップ</h4>
                            <p>予期しないステップです。ページをリロードしてください。</p>
                        </div>
                    </div>
                );
        }
    };

    return (
        <div className="block-unit-price-workflow">
            {renderStepContent()}
        </div>
    );
};

export default BlockUnitPriceWorkflow;