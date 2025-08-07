// /app/src/components/Report/ReportTabs.tsx
import React from 'react';
import { REPORT_KEYS } from '../../constants/reportConfig/managementReportConfig';
import type { ReportKey } from '../../constants/reportConfig/managementReportConfig';

interface ReportTabsProps {
    selectedReport: ReportKey;
    onChangeReport: (reportKey: ReportKey) => void;
    currentStep: number;
    title: string;
}

/**
 * レポートタブコンポーネント
 * 
 * 🎯 責任：
 * - 帳簿選択タブの表示
 * - ステッパー表示
 * - タイトル表示
 */
const ReportTabs: React.FC<ReportTabsProps> = ({
    selectedReport,
    onChangeReport,
    currentStep,
    title,
}) => {
    return (
        <div style={{ marginBottom: 16 }}>
            {/* タイトル部分 */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 12
            }}>
                <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>
                    {title}
                </h2>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    fontSize: 14,
                    color: '#666'
                }}>
                    <span>ステップ {currentStep}/3</span>
                    <span style={{
                        padding: '4px 8px',
                        backgroundColor: '#f0f0f0',
                        borderRadius: 4,
                        fontWeight: 500
                    }}>
                        {currentStep === 1 ? 'CSVアップロード' : currentStep === 2 ? '帳簿生成' : '結果確認'}
                    </span>
                </div>
            </div>

            {/* レポートタブ */}
            <div style={{
                display: 'flex',
                gap: 8,
                flexWrap: 'wrap',
                borderBottom: '1px solid #d9d9d9',
                paddingBottom: 8
            }}>
                {Object.entries(REPORT_KEYS).map(([key, config]) => (
                    <button
                        key={key}
                        onClick={() => onChangeReport(key as ReportKey)}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 4,
                            padding: '8px 16px',
                            border: '1px solid #d9d9d9',
                            borderRadius: 6,
                            backgroundColor: selectedReport === key ? '#1890ff' : '#fff',
                            color: selectedReport === key ? '#fff' : '#333',
                            cursor: 'pointer',
                            fontSize: 14,
                            fontWeight: selectedReport === key ? 600 : 400,
                            transition: 'all 0.2s',
                        }}
                    >
                        📊 {config.label}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default ReportTabs;
