import React from "react";
import { Row, Col } from "antd";
import { RepFilterSelector } from "../RepFilterSelector";
import type { Mode, ID, SalesRep } from "../../../../shared/model/types";

interface RepFilterSectionProps {
  gutter: [number, number];

  mode: Mode;
  repIds: ID[];
  filterIds: ID[];
  reps: SalesRep[];
  repOptions: Array<{ label: string; value: ID }>;
  filterOptions: Array<{ label: string; value: ID }>;
  onRepIdsChange: (ids: ID[]) => void;
  onFilterIdsChange: (ids: ID[]) => void;
}

/**
 * 営業・絞り込みセクション
 *
 * 営業選択と顧客/品名/日付による絞り込みを行う
 */
export const RepFilterSection: React.FC<RepFilterSectionProps> = ({
  gutter,
  mode,
  repIds,
  filterIds,
  reps,
  repOptions,
  filterOptions,
  onRepIdsChange,
  onFilterIdsChange,
}) => {
  return (
    <Row gutter={gutter}>
      <Col xs={24}>
        <RepFilterSelector
          mode={mode}
          repIds={repIds}
          filterIds={filterIds}
          reps={reps}
          repOptions={repOptions}
          filterOptions={filterOptions}
          onRepIdsChange={onRepIdsChange}
          onFilterIdsChange={onFilterIdsChange}
        />
      </Col>
    </Row>
  );
};
