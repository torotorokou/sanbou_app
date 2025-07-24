import React from 'react';
import { Card, Typography, Row, Col } from 'antd';
import { customTokens } from '@/theme/tokens';

// トークンの説明を付与（手動マッピング）
const tokenDescriptions: Record<string, string> = {
    colorPrimary: 'ブランドメイン色（主ボタン、強調）',
    colorSuccess: '成功状態（チェックマーク、通知）',
    colorError: 'エラー状態（バリデーション、削除）',
    colorWarning: '警告状態（注意喚起）',
    colorInfo: '情報表示（補助的な情報）',
    colorBgBase: '全体背景（最も薄いグレー）',
    colorBgLayout: 'レイアウト背景（中間の灰色）',
    colorBgContainer: 'コンテンツ背景（白）',
    colorBgElevated: '浮き上がり用背景（白）',
    colorSiderBg: 'サイドバー背景（濃色）',
    colorSiderText: 'サイドバーの文字色（白）',
    colorSiderHover: 'サイドバーのホバー背景',
    colorText: '基本の文字色',
    colorTextSecondary: 'サブの文字色',
    colorBorderSecondary: '補助的なボーダー色',
};

const TokenPreview: React.FC = () => {
    return (
        <div style={{ padding: 24 }}>
            <Typography.Title level={3}>
                🎨 カラートークンプレビュー
            </Typography.Title>
            <Row gutter={[16, 16]}>
                {Object.entries(customTokens).map(([key, value]) => (
                    <Col xs={24} sm={12} md={8} lg={6} key={key}>
                        <Card
                            bordered
                            styles={{ body: { padding: 16 } }}
                            variant='outlined'
                            style={{
                                backgroundColor: '#fff',
                                borderColor: '#e5e7eb',
                            }}
                        >
                            <div
                                style={{
                                    backgroundColor: value,
                                    height: 64,
                                    borderRadius: 8,
                                    border: '1px solid #ccc',
                                }}
                            />
                            <div style={{ marginTop: 12 }}>
                                <Typography.Text code>{key}</Typography.Text>
                                <br />
                                <Typography.Text type='secondary'>
                                    {value}
                                </Typography.Text>
                                <br />
                                <Typography.Text>
                                    {tokenDescriptions[key] || '説明なし'}
                                </Typography.Text>
                            </div>
                        </Card>
                    </Col>
                ))}
            </Row>
        </div>
    );
};

export default TokenPreview;
