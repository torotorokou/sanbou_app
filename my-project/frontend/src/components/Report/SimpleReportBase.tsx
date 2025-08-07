import React from 'react';
import BaseReportComponent from './BaseReportComponent';
import type { ReportBaseProps } from '../../types/reportBase';

// 拡張されたprops型（getValidationResultを含む）
interface ExtendedReportBaseProps extends ReportBaseProps {
    getValidationResult?: (label: string) => 'valid' | 'invalid' | 'unknown';
}

/**
 * シンプルレポートベースコンポーネント
 * BaseReportComponentのデフォルト機能をそのまま使用
 */
const SimpleReportBase: React.FC<ExtendedReportBaseProps> = (props) => {
    console.log('[SimpleReportBase] called, reportKey:', props.reportKey);

    // BaseReportComponentにそのまま委譲（カスタム処理なし）
    return <BaseReportComponent {...props} />;
};

export default SimpleReportBase;
