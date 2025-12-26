import React from "react";
import { Typography } from "antd";
import styles from "./ManagementDashboard.module.css";
import {
  SummaryPanel,
  CustomerAnalysis,
  RevenuePanel,
  BlockCountPanel,
  ProcessVolumePanel,
} from "@features/dashboard";

const { Title } = Typography;
const ManagementDashboard: React.FC = () => {
  return (
    <div className={styles.dashboardRoot}>
      <Title level={3} className={styles.dashboardTitle}>
        2025年6月27日 実績ダッシュボード
      </Title>

      <div className={styles.dashboardMain}>
        {/* left column */}
        <div className={styles.leftColumn}>
          <div className={`${styles.panel} ${styles.cardWrapper}`}>
            <SummaryPanel />
          </div>

          <div className={`${styles.panel} ${styles.cardWrapper}`}>
            <RevenuePanel />
          </div>
        </div>

        {/* right column */}
        <div className={styles.rightColumn}>
          <div className={`${styles.panelTop} ${styles.cardWrapper}`}>
            <CustomerAnalysis />
          </div>

          <div className={`${styles.panelMid} ${styles.cardWrapper}`}>
            <ProcessVolumePanel />
          </div>

          <div className={`${styles.panelBottom} ${styles.cardWrapper}`}>
            <BlockCountPanel />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ManagementDashboard;
