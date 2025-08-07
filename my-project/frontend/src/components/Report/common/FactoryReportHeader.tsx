// /app/src/components/Report/common/FactoryReportHeader.tsx
import React from 'react';
import { Tabs, Steps, Row, Col, Card } from 'antd';
import type { FactoryReportKey } from '../../../constants/reportConfig/factoryReportConfig';
import { FACTORY_REPORT_KEYS } from '../../../constants/reportConfig/factoryReportConfig';

interface FactoryReportHeaderProps {
    reportKey: FactoryReportKey;
    onChangeReportKey: (key: FactoryReportKey) => void;
    currentStep: number;
}

/**
 * 工場帳簿専用ヘッダーコンポーネント
 * 
 * 🎯 機能：
 * - 左上: 工場帳簿選択タブ
 * - 右上: ステッパー表示
 * - 管理帳簿とは独立した設計
 */
const FactoryReportHeader: React.FC<FactoryReportHeaderProps> = ({
    reportKey,
    onChangeReportKey,
    currentStep,
}) => {
    // タブアイテム作成
    const tabItems = Object.entries(FACTORY_REPORT_KEYS).map(([key, config]) => ({
        key: key as FactoryReportKey,
        label: (
            <span>
                {config.label}
                <span style={{
                    marginLeft: 8,
                    fontSize: '12px',
                    color: config.type === 'interactive' ? '#1890ff' : '#52c41a'
                }}>
                    {config.type === 'interactive' ? 'Interactive' : 'Auto'}
                </span>
            </span>
        ),
    }));

    // ステップ項目（仮の項目、実際は設定から取得）
    const stepItems = [
        { title: 'CSVアップロード' },
        { title: 'データ処理' },
        { title: '帳簿生成' },
        { title: '完了' },
    ];

    return (
        <Card
            size="small"
            style={{ marginBottom: 16 }}
            bodyStyle={{ padding: '12px 16px' }}
        >
            <Row justify="space-between" align="middle">
                {/* 左側: 工場帳簿選択タブ */}
                <Col flex="auto">
                    <div style={{ marginBottom: 8 }}>
                        <strong style={{ fontSize: '16px', color: '#1890ff' }}>
                            🏭 工場帳簿システム
                        </strong>
                    </div>
                    <Tabs
                        activeKey={reportKey}
                        onChange={(key) => onChangeReportKey(key as FactoryReportKey)}
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

export default FactoryReportHeader;
