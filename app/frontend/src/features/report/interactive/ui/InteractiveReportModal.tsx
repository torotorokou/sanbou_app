import React from 'react';
import { Modal, Steps } from 'antd';
import { modalStepsMap, isInteractiveReport } from '@features/report/shared/config';
import type { ReportKey } from '@features/report/shared/config';

/**
 * インタラクティブ帳簿専用モーダルコンポーネント
 *
 * 🎯 目的：
 * - 通常の帳簿作成と異なるUI/ロジックが必要な帳簿の専用モーダル
 * - 帳簿種別に応じた適切なインタラクティブコンポーネントの表示
 * - 既存の共通モーダル構造との分岐管理
 *
 * ⚠️ 注意：
 * このモーダルは旧実装で、現在は BlockUnitPriceInteractiveModal が直接使用されています。
 * 将来的に複数のインタラクティブ帳簿が追加される場合に備えて保持しています。
 */

export interface InteractiveReportModalProps {
  open: boolean;
  onCancel: () => void;
  reportKey: ReportKey;
  currentStep: number;
}

const InteractiveReportModal: React.FC<InteractiveReportModalProps> = ({
  open,
  onCancel,
  reportKey,
  currentStep,
}) => {
  // インタラクティブ帳簿でない場合は何も表示しない
  if (!isInteractiveReport(reportKey)) {
    return null;
  }

  const steps = modalStepsMap[reportKey] || [];

  /**
   * 帳簿種別に応じたインタラクティブコンポーネントを返す
   *
   * @deprecated このモーダルは現在使用されていません。
   * BlockUnitPriceInteractiveModal が直接使用されています。
   */
  const renderInteractiveComponent = () => {
    // 帳簿キーの文字列比較で分岐
    if (reportKey.includes('block_unit_price')) {
      return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <h3>ブロック単価表</h3>
          <p>BlockUnitPriceInteractiveModal を直接使用してください</p>
        </div>
      );
    }

    if (reportKey.includes('transport_cost')) {
      // 将来的に追加される運送費用インタラクティブコンポーネント
      return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <h3>運送費用インタラクティブ帳簿</h3>
          <p>準備中...</p>
        </div>
      );
    }

    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>サポートされていないインタラクティブ帳簿: {reportKey}</p>
      </div>
    );
  };

  return (
    <Modal
      title={`インタラクティブ帳簿作成 - ${reportKey}`}
      open={open}
      onCancel={onCancel}
      footer={null}
      width={800}
      style={{ top: 20 }}
      destroyOnHidden
    >
      {/* ステップインジケーター */}
      {steps.length > 1 && (
        <div style={{ marginBottom: 24 }}>
          <Steps
            current={currentStep}
            size="small"
            items={steps.map((step) => ({
              title: step.label,
              description: step.content ? 'インタラクティブ処理' : '',
            }))}
          />
        </div>
      )}

      {/* インタラクティブコンポーネント */}
      <div style={{ minHeight: '400px' }}>{renderInteractiveComponent()}</div>
    </Modal>
  );
};

export default InteractiveReportModal;
