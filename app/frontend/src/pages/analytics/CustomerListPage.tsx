/**
 * Customer List Analysis Page
 *
 * FSD + MVVM + Repository パターンに準拠
 *
 * Page層の責務:
 * - レイアウト/ルーティング/配置（骨組み）のみ
 * - ViewModel（useCustomerChurnViewModel）を呼び出し
 * - 純粋なUIコンポーネントにデータを流し込むだけ
 * - ビジネスロジック・状態管理・イベントハンドラは一切書かない
 */

import React from "react";
import { Row, Col } from "antd";
import {
  ConditionPanel,
  AnalysisActionButtons,
  ResultPanel,
  AnalysisProcessingModal,
  useCustomerChurnViewModel,
} from "@features/analytics/customer-list";

const CustomerListAnalysis: React.FC = () => {
  // ViewModel を呼び出し（すべての状態・ロジック・イベントハンドラがここに集約）
  const vm = useCustomerChurnViewModel();

  return (
    <div style={{ height: "100%", minHeight: 0 }}>
      {/* 分析中モーダル */}
      <AnalysisProcessingModal open={vm.isAnalyzing} />

      <Row gutter={24} style={{ height: "100%", minHeight: 0 }}>
        {/* 左カラム: 条件指定・実行ボタン */}
        <Col
          span={7}
          style={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
            padding: "clamp(24px, 2vw, 40px) clamp(16px, 1.5vw, 24px)",
            background: "#f8fcfa",
            overflow: "auto",
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "clamp(20px, 2vw, 32px)",
              height: "100%",
              justifyContent: "flex-start",
              alignItems: "stretch",
            }}
          >
            <ConditionPanel
              currentStart={vm.currentStart}
              currentEnd={vm.currentEnd}
              previousStart={vm.previousStart}
              previousEnd={vm.previousEnd}
              setCurrentStart={vm.setCurrentStart}
              setCurrentEnd={vm.setCurrentEnd}
              setPreviousStart={vm.setPreviousStart}
              setPreviousEnd={vm.setPreviousEnd}
              salesReps={vm.salesReps}
              selectedSalesRepIds={vm.selectedSalesRepIds}
              setSelectedSalesRepIds={vm.setSelectedSalesRepIds}
              analysisStarted={vm.analysisStarted}
              onReset={vm.resetConditions}
            />

            <AnalysisActionButtons
              onAnalyze={vm.handleAnalyze}
              onDownload={vm.handleDownloadLostCustomersCsv}
              isAnalyzeDisabled={vm.isButtonDisabled}
              isDownloadDisabled={!vm.analysisStarted}
            />
          </div>
        </Col>

        {/* 右カラム: 分析結果表示 */}
        <Col
          span={17}
          style={{
            height: "95%",
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
          }}
        >
          <ResultPanel
            data={vm.lostCustomers}
            isAnalyzing={vm.isAnalyzing}
            analysisStarted={vm.analysisStarted}
          />
        </Col>
      </Row>
    </div>
  );
};

export default CustomerListAnalysis;
