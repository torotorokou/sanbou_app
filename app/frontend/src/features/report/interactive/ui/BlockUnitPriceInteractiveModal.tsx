import React, { useState, useCallback } from 'react';
import { Modal, Button, Steps, Spin } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import { notifyError, notifySuccess } from '@features/notification';
import { getApiEndpoint } from '@features/report/shared/config';
import type { ReportKey } from '@features/report/shared/config';
import type { ReportArtifactResponse } from '@features/report/preview/model/useReportArtifact';
import { coreApi } from '@features/report/shared/infrastructure/http.adapter';
import type {
  InteractiveItem,
  InitialApiResponse,
  SessionData,
} from '@features/report/shared/types/interactive.types';
import {
  createInteractiveItemFromRow,
  buildSelectionPayload,
} from '../model/blockUnitPriceHelpers';
import { TransportSelectionList } from './TransportSelectionList';
import { TransportConfirmationTable } from './TransportConfirmationTable';

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
 * ブロック単価表専用インタラクティブモーダル
 */
const BlockUnitPriceInteractiveModal: React.FC<BlockUnitPriceInteractiveModalProps> = ({
  open,
  onClose,
  reportKey,
  onSuccess,
  initialApiResponse,
  initialSessionData,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [initialData, setInitialData] = useState<InitialApiResponse | null>(null);
  const [items, setItems] = useState<InteractiveItem[]>([]);
  const [selections, setSelections] = useState<SelectionMap>({});
  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [selectionPreview, setSelectionPreview] = useState<SelectionPreviewResponse | null>(null);

  const steps = [
    { title: '選択', description: '処理業者ごとに運搬業者を選択' },
    { title: '確認', description: '選択内容を確認' },
    { title: '生成', description: '帳簿を生成中' },
    { title: '完了', description: '処理が完了しました' },
  ];

  const buildLocalSelectionPreview = useCallback((): SelectionPreviewResponse => {
    const selection_summary: Record<
      string,
      {
        id?: string;
        entry_id?: string;
        processor_name?: string;
        vendor_code?: string;
        transport_vendor?: string;
        selected_index?: number;
      }
    > = {};
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

    return {
      session_id: sessionData?.session_id ?? '',
      selections_by_id: selectionsById,
    } as Record<string, unknown>;
  }, [selections, sessionData, items]);

  const handleApplySelectionsAndFinalize = useCallback(async () => {
    const sessionId = sessionData?.session_id;
    if (!sessionId) {
      notifyError('エラー', 'セッション情報が見つかりません。');
      return;
    }

    const selectionPayloadMap = buildSelectionPayload(items, selections);

    // 選択肢がない場合（items.length === 0）は空の選択で処理を進める
    if (Object.keys(selectionPayloadMap).length === 0 && items.length > 0) {
      notifyError('エラー', '選択内容がありません。');
      setCurrentStep(1);
      return;
    }

    setCurrentStep(2);
    setProcessing(true);
    try {
      const apiEndpoint = getApiEndpoint(reportKey);
      const baseEndpoint =
        apiEndpoint.replace(/\/initial$/, '') || apiEndpoint.replace(/\/initial/, '');

      console.log('[BlockUnitPrice] apply payload (map):', {
        session_id: sessionId,
        selections: selectionPayloadMap,
      });
      const applyJson = await coreApi.post<Record<string, unknown>>(`${baseEndpoint}/apply`, {
        session_id: sessionId,
        selections: selectionPayloadMap,
      });

      if (applyJson && typeof applyJson === 'object' && 'selection_summary' in applyJson) {
        setSelectionPreview({
          selection_summary: applyJson.selection_summary as Record<string, unknown>,
        });
      }

      console.log('[BlockUnitPrice] finalize payload (session_id only):', {
        session_id: sessionId,
      });
      const finalizeJson = await coreApi.post<ReportArtifactResponse>(`${baseEndpoint}/finalize`, {
        session_id: sessionId,
      });
      console.log('[BlockUnitPrice] finalize response (artifact):', finalizeJson);

      setCurrentStep(3);
      notifySuccess('生成完了', '帳簿生成が完了しました');
      onSuccess(finalizeJson);

      setTimeout(() => {
        onClose();
      }, 1200);
    } catch (error) {
      console.error('Finalize flow failed:', error);
      notifyError('エラー', '帳簿生成に失敗しました');
      setCurrentStep(1);
    } finally {
      setProcessing(false);
    }
  }, [sessionData, items, selections, onSuccess, onClose, reportKey]);

  const handleSelectionChange = useCallback((id: string, selection: SelectionState) => {
    setSelections((prev) => ({ ...prev, [id]: selection }));
  }, []);

  const handleNext = useCallback(() => {
    if (currentStep === 0) {
      // 選択肢がない場合は確認ステップをスキップして直接最終処理へ
      if (items.length === 0) {
        handleApplySelectionsAndFinalize();
      } else {
        const preview = buildLocalSelectionPreview();
        setSelectionPreview(preview);
        setCurrentStep(1);
      }
    } else if (currentStep === 1) {
      handleApplySelectionsAndFinalize();
    }
  }, [currentStep, items.length, buildLocalSelectionPreview, handleApplySelectionsAndFinalize]);

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
    try {
      console.log('[BlockUnitPrice] initialApiResponse:', initialApiResponse);
      console.log(
        '[BlockUnitPrice] initialSessionData:',
        initialSessionData ??
          (initialApiResponse?.session_id ? { session_id: initialApiResponse.session_id } : null)
      );
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
      maskClosable={false}
      styles={{
        body: {
          maxHeight: '70vh',
          padding: '20px 24px 24px',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      <Steps current={currentStep} style={{ marginBottom: 24 }}>
        {steps.map((step) => (
          <Steps.Step key={step.title} title={step.title} description={step.description} />
        ))}
      </Steps>

      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          minHeight: 0,
        }}
      >
        {processing && currentStep !== 3 && (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" />
          </div>
        )}
        {currentStep === 0 && !processing && initialData && items.length === 0 && (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <p>運搬業者の選択が必要な行はありません。</p>
          </div>
        )}

        {currentStep === 0 && !processing && items.length > 0 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              flex: 1,
              minHeight: 0,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-start',
                alignItems: 'center',
                marginBottom: 12,
              }}
            >
              <h4
                style={{
                  margin: 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span>処分業者ごとに運搬業者を選択してください</span>
                <span style={{ fontSize: 13, color: '#666' }}>（{items.length}行）</span>
              </h4>
            </div>
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: '0 8px 12px 0',
              }}
            >
              <TransportSelectionList
                items={items}
                selections={selections}
                onChange={handleSelectionChange}
              />
            </div>
          </div>
        )}

        {currentStep === 1 && !processing && items.length > 0 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              flex: 1,
              minHeight: 0,
            }}
          >
            <h4 style={{ marginBottom: 12 }}>選択内容の確認</h4>
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: '0 8px 12px 0',
              }}
            >
              <TransportConfirmationTable items={items} selections={selections} />
            </div>
            <p style={{ marginTop: 12, color: '#666' }}>
              詳細なサマリーと送信内容はコンソールで確認できます。
            </p>
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

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          marginTop: 24,
        }}
      >
        <div
          style={{
            flex: 1,
            display: 'flex',
            justifyContent: 'flex-start',
          }}
        >
          {currentStep === 1 && !processing && (
            <Button onClick={() => setCurrentStep(0)}>戻る</Button>
          )}
        </div>

        <div
          style={{
            flex: 1,
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <Button onClick={handleClose}>{currentStep >= 3 ? '閉じる' : 'キャンセル'}</Button>
        </div>

        <div
          style={{
            flex: 1,
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 8,
          }}
        >
          {currentStep === 0 && !processing && items.length > 0 && (
            <Button
              type="primary"
              onClick={handleNext}
              disabled={items.some((item) => !selections[item.id])}
            >
              確認へ
            </Button>
          )}

          {currentStep === 0 && !processing && items.length === 0 && (
            <Button type="primary" onClick={handleNext}>
              次へ進む
            </Button>
          )}

          {currentStep === 1 && !processing && (
            <Button type="primary" onClick={handleNext}>
              進む
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
};

export default BlockUnitPriceInteractiveModal;
