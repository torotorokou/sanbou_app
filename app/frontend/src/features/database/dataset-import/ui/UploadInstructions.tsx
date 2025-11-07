import React from 'react';
import { Collapse, Typography, Tag, List } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';

const { Paragraph, Text } = Typography;

export const UploadInstructions: React.FC = () => (
    <Collapse
        defaultActiveKey={[]}
        style={{
            marginBottom: 16,
            backgroundColor: '#f6ffed',
            border: '1px solid #b7eb8f',
            borderRadius: 6,
        }}
        expandIconPosition="start"
    >
        <Collapse.Panel
            header={
                <span style={{ fontWeight: 'bold' }}>
                    <InfoCircleOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                    アップロード手順・ルール
                </span>
            }
            key="1"
        >
            <Paragraph>
                以下の <Tag color="red">3つのCSVファイル</Tag> をアップロードしてください。
            </Paragraph>
            <List
                size="small"
                bordered={false}
                dataSource={[
                    { name: '受入一覧', required: true },
                    { name: '出荷一覧', required: true },
                    { name: 'ヤード一覧', required: true },
                ]}
                renderItem={(item) => (
                    <List.Item style={{ paddingLeft: 0 }}>
                        <Tag color="blue">{item.name}</Tag>
                        <Text type="secondary">（必須）</Text>
                    </List.Item>
                )}
                style={{ marginBottom: 12 }}
            />
            <Paragraph>
                <Text type="danger">
                    ⚠️ ファイルは「将軍ソフトからダウンロードしたままの状態」でアップロードしてください。
                </Text>
                <br />
                自分で編集・加工・列の並び替え・名前変更をしたファイルは使用できません。
            </Paragraph>
        </Collapse.Panel>
    </Collapse>
);
