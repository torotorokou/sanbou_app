/**
 * Result Panel Component
 *
 * 分析結果表示パネル
 */

import React from "react";
import { customTokens } from "@/shared";
import type { CustomerData } from "../../shared/domain/types";
import { CustomerComparisonResultCard } from "../../customer-comparison";

type Props = {
  data: CustomerData[];
  isAnalyzing: boolean;
  analysisStarted: boolean;
};

/**
 * 分析結果表示パネル
 *
 * 分析未実行時でも表の外枠とヘッダーを表示
 */
const ResultPanel: React.FC<Props> = ({ data, analysisStarted }) => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
        height: "100%",
        minHeight: 0,
        flex: 1,
      }}
    >
      <CustomerComparisonResultCard
        title={
          analysisStarted
            ? `来なくなった顧客（離脱）: ${data.length} 件`
            : "来なくなった顧客（離脱）"
        }
        data={data}
        cardStyle={{
          backgroundColor: customTokens.colorBgContainer,
        }}
        headerStyle={{
          background:
            "linear-gradient(90deg, rgba(244,63,94,0.4), rgba(244,63,94,0.05))",
          color: "#333",
        }}
        style={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
        }}
      />
    </div>
  );
};

export default ResultPanel;
