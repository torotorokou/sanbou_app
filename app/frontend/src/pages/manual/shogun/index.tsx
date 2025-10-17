/**
 * 将軍マニュアル一覧ページ
 * FSD: ページ層は組み立てのみ
 */
import React from "react";
import styles from "./ShogunPage.module.css";
import ShogunManualList from "@/features/manual/shogun/ui/ShogunManualList";

const ShogunManualListPage: React.FC = () => {
  return (
    <div className={styles.pageContainer}>
      <ShogunManualList />
    </div>
  );
};

export default ShogunManualListPage;
