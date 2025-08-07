// /app/src/components/Report/common/GenericReportSelector.tsx
import React from 'react';
import { Select, Card, Typography, Row, Col, Image } from 'antd';
import type { ReportConfigPackage } from '../../../types/reportConfig';

const { Option } = Select;
const { Title, Text } = Typography;

interface GenericReportSelectorProps {
    config: ReportConfigPackage;
    selectedReportKey: string | undefined;
    onReportChange: (reportKey: string) => void;
    className?: string;
}

/**
 * 汎用的な帳票選択コンポーネント
 * 
 * どの帳票設定パッケージでも使用可能な汎用セレクター
 */
export const GenericReportSelector: React.FC<GenericReportSelectorProps> = ({
    config,
    selectedReportKey,
    onReportChange,
    className = '',
}) => {
    const reportOptions = config.getReportOptions();
    const selectedReport = selectedReportKey ? config.reportKeys[selectedReportKey] : null;
    const previewImage = selectedReportKey ? config.pdfPreviewMap[selectedReportKey] : null;

    return (
        <div className={`generic-report-selector ${className}`}>
            <Card>
                <Row gutter={[16, 16]}>
                    <Col span={24}>
                        <Title level={4}>帳票タイプを選択</Title>
                        <Select
                            placeholder="帳票を選択してください"
                            style={{ width: '100%' }}
                            value={selectedReportKey}
                            onChange={onReportChange}
                        >
                            {reportOptions.map((report) => (
                                <Option key={report.value} value={report.value}>
                                    {report.label}
                                    <Text type="secondary" style={{ marginLeft: 8 }}>
                                        ({report.type === 'auto' ? '自動' : 'インタラクティブ'})
                                    </Text>
                                </Option>
                            ))}
                        </Select>
                    </Col>

                    {selectedReport && (
                        <Col span={24}>
                            <Card size="small" title={`${selectedReport.label} プレビュー`}>
                                <Row gutter={[16, 16]}>
                                    <Col span={12}>
                                        <div>
                                            <Text strong>帳票タイプ: </Text>
                                            <Text>
                                                {selectedReport.type === 'auto' ? '自動生成' : 'インタラクティブ'}
                                            </Text>
                                        </div>
                                        <div style={{ marginTop: 8 }}>
                                            <Text strong>設定セット: </Text>
                                            <Text>{config.name}</Text>
                                        </div>
                                    </Col>
                                    <Col span={12}>
                                        {previewImage && (
                                            <Image
                                                src={previewImage}
                                                alt={`${selectedReport.label} プレビュー`}
                                                style={{ maxHeight: 200, width: '100%', objectFit: 'contain' }}
                                                fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Pu3BUGcPe2fDNfAhuTYhF+Hb2Lrr3HxI7P9TGvZFR/5JjK2fI7YYMqLdXGy5T8WJj8ZnKaL6zyLYKpIOLg/RBOmxCTAYRh5eXs+/dZqpUx5nCBiOREBuWCVhBTVBWDBFKQBESSABCSB8QElAJiCLZG6cNfBKRJqKhJbGkEpbUIQPBEQggA5GNcW0kFGFtHwAJKWDZEQgJTg1CrE4UIVRBERpwABNSdCUqHgW6kzqEKINSDGIQIoAsA"
                                            />
                                        )}
                                    </Col>
                                </Row>
                            </Card>
                        </Col>
                    )}
                </Row>
            </Card>
        </div>
    );
};
