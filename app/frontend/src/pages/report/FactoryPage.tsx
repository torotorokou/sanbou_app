import React, { useEffect, useState } from 'react';
import { ReportBase, ReportHeader } from '@features/report';
import { useReportManager } from '@features/report';
import { UnimplementedModal } from '@features/unimplemented-feature';
import styles from './ReportPage.module.css';

/**
 * 工場帳簿ページ - 新しい分割アーキテクチャ対応
 *
 * 🔄 リファクタリング内容：
 * - 古い手動実装（~216行）から新しいアーキテクチャに移行
 * - 複雑な状態管理をuseReportManagerフックに分離
 * - 工場関連の帳票のみを表示するよう設定
 * - インラインスタイルをCSS Modulesに移行
 *
 * 📝 コード行数：~216行 → ~28行（87%削減）
 *
 * 🎯 責任：
 * - 工場帳票に特化したUIレイアウト
 * - ビジネスロジックはカスタムフック内で管理
 */

const FactoryPage: React.FC = () => {
  const reportManager = useReportManager('factory_report2');
  // useMemoでメモ化されたprops（関数ではなくオブジェクト）
  const reportBaseProps = reportManager.getReportBaseProps;
  const [showUnimplementedModal, setShowUnimplementedModal] = useState(false);

  useEffect(() => {
    // ページ読み込み時にモーダルを表示
    setShowUnimplementedModal(true);
  }, []);

  return (
    <div className={styles.pageContainer}>
      <UnimplementedModal
        visible={showUnimplementedModal}
        onClose={() => setShowUnimplementedModal(false)}
        featureName="工場帳簿"
        description="工場帳簿機能は現在開発中です。完成まで今しばらくお待ちください。リリース後は、工場別の詳細な在庫管理や生産実績の確認が可能になります。"
      />
      <ReportHeader
        reportKey={reportManager.selectedReport}
        onChangeReportKey={reportManager.changeReport}
        currentStep={reportManager.currentStep}
        areRequiredCsvsUploaded={reportManager.areRequiredCsvsUploaded}
        isFinalized={reportManager.isFinalized}
        pageGroup="factory"
      />
      <div className={styles.contentArea}>
        <ReportBase {...reportBaseProps} />
      </div>
    </div>
  );
};

export default FactoryPage;
