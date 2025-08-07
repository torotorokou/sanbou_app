// /app/src/components/Report/common/ReportPageBase.tsx
import React from 'react';

interface ReportPageBaseProps {
    header: React.ReactNode;
    factory: React.ReactNode;
    debugInfo?: React.ReactNode;
}

/**
 * レポートページの共通ベースレイアウト
 * 
 * 🎯 責任：
 * - 全レポートページ共通のレイアウト構造
 * - ヘッダー + ファクトリーの統一配置
 * - デバッグ情報の条件表示
 * 
 * 📝 使用例：
 * <ReportPageBase
 *   header={<ReportHeader />}
 *   factory={<ReportFactory />}
 *   debugInfo={<ResponsiveDebugInfo />}
 * />
 */
const ReportPageBase: React.FC<ReportPageBaseProps> = ({
    header,
    factory,
    debugInfo,
}) => {
    return (
        <>
            {/* デバッグ情報（条件表示） */}
            {debugInfo}

            {/* 左上: 帳簿選択タブ、右上: ステッパー一覧 */}
            {header}

            {/* メインのレポートファクトリー */}
            {factory}
        </>
    );
};

export default ReportPageBase;
