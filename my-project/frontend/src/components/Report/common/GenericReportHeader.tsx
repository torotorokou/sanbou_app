// /app/src/components/Report/common/GenericReportHeader.tsx
import React from 'react';
import { Tabs, Steps, Row, Col, Card } from 'antd';

interface ReportOption {
    key: string;
    label: string;
    type: 'auto' | 'interactive';
}

interface GenericReportHeaderProps {
    title: string;
    icon: string;
    reportKey: string;
    reportOptions: ReportOption[];
    onChangeReportKey: (key: string) => void;
    currentStep: number;
    stepItems?: Array<{ title: string }>;
}

/**
 * 汎用レポートヘッダーコンポーネント
 * 
 * 🎯 責任：
 * - 左上: 帳簿選択タブ（汎用）
 * - 右上: ステッパー表示（汎用）
 * - タイトルとアイコンのカスタマイズ対応
 * 
 * 📝 使用例：
 * <GenericReportHeader
 *   title="管理帳簿システム"
 *   icon="📊"
 *   reportKey={reportKey}
 *   reportOptions={REPORT_OPTIONS}
 *   onChangeReportKey={changeReport}
 *   currentStep={currentStep}
 * />
 */
const GenericReportHeader: React.FC<GenericReportHeaderProps> = ({
    title,
    icon,
    reportKey,
    reportOptions,
    onChangeReportKey,
    currentStep,
    stepItems = [
        { title: 'CSVアップロード' },
        { title: 'データ処理' },
        { title: '帳簿生成' },
        { title: '完了' },
    ],
}) => {
    // タブアイテム作成
    const tabItems = reportOptions.map((option) => ({
        key: option.key,
        label: (
            <span>
                {option.label}
                <span style={{
                    marginLeft: 8,
                    fontSize: '12px',
                    color: option.type === 'interactive' ? '#1890ff' : '#52c41a'
                }}>
                    {option.type === 'interactive' ? 'Interactive' : 'Auto'}
                </span>
            </span>
        ),
    }));

    return (
        <Card
            size="small"
            style={{ marginBottom: 16 }}
            bodyStyle={{ padding: '12px 16px' }}
        >
            <Row justify="space-between" align="middle">
                {/* 左側: 帳簿選択タブ */}
                <Col flex="auto">
                    <div style={{ marginBottom: 8 }}>
                        <strong style={{ fontSize: '16px', color: '#1890ff' }}>
                            {icon} {title}
                        </strong>
                    </div>
                    <Tabs
                        activeKey={reportKey}
                        onChange={onChangeReportKey}
                        items={tabItems}
                        size="small"
                        type="card"
                    />
                </Col>

                {/* 右側: ステッパー */}
                <Col flex="300px">
                    <div style={{ textAlign: 'right' }}>
                        <div style={{ marginBottom: 8, fontSize: '12px', color: '#666' }}>
                            進捗状況
                        </div>
                        <Steps
                            current={currentStep}
                            items={stepItems}
                            size="small"
                            direction="horizontal"
                            style={{ maxWidth: 300 }}
                        />
                    </div>
                </Col>
            </Row>
        </Card>
    );
};

export default GenericReportHeader;
