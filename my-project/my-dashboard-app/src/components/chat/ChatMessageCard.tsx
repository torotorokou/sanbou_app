import React from 'react';
import { Card, Typography, Button, Tag, Space } from 'antd';
import { UserOutlined, RobotOutlined, BookOutlined } from '@ant-design/icons';
import TypewriterText from '@/components/ui/TypewriterText';
import type { ChatMessage } from '@/types/chat';

type Props = {
    msg: ChatMessage;
    index: number;
    windowWidth: number;
    isLastBotMessage?: boolean;
    onSelectCategory?: (cat: string) => void;
    onOpenPdf?: (pdfName: string) => void;
};

const roleMeta = {
    user: {
        title: (
            <Space>
                <UserOutlined style={{ color: '#52c41a', fontSize: 20 }} />
                <span>あなた</span>
            </Space>
        ),
        color: '#f6ffed',
    },
    bot: {
        title: (
            <Space>
                <RobotOutlined style={{ color: '#1890ff', fontSize: 20 }} />
                <span>AI</span>
            </Space>
        ),
        color: '#e6f7ff',
    },
};

const ChatMessageCard: React.FC<Props> = ({
    msg,
    windowWidth,
    isLastBotMessage,
    onSelectCategory,
    onOpenPdf,
}) => {
    const getCardStyle = () => {
        let width = '100%';
        if (windowWidth >= 1024) {
            width = msg.role === 'user' ? '40%' : '60%';
        } else if (windowWidth >= 768) {
            width = '70%';
        }
        return {
            width,
            alignSelf: msg.role === 'user' ? 'flex-start' : 'flex-end',
            background: roleMeta[msg.role]?.color,
            borderRadius: 16,
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            marginBottom: 16,
            transition: 'background 0.3s, box-shadow 0.3s',
        };
    };

    return (
        <Card
            size='small'
            title={roleMeta[msg.role]?.title}
            style={getCardStyle()}
            bodyStyle={{ padding: 18 }}
            hoverable
        >
            <Typography.Paragraph style={{ fontSize: 15, marginBottom: 4 }}>
                {msg.role === 'bot' && !msg.type && isLastBotMessage ? (
                    <TypewriterText text={msg.content} />
                ) : (
                    msg.content?.split('\n').map((line, i) => (
                        <React.Fragment key={i}>
                            {line}
                            <br />
                        </React.Fragment>
                    ))
                )}
            </Typography.Paragraph>

            {/* カテゴリボタン */}
            {msg.type === 'category-buttons' && (
                <div style={{ marginTop: 12 }}>
                    <Typography.Text
                        strong
                        style={{ marginBottom: 8, display: 'block' }}
                    >
                        📚 カテゴリ一覧
                    </Typography.Text>
                    <Space wrap>
                        {['処理', '設備', '法令', '運搬', '分析'].map((cat) => (
                            <Button
                                key={cat}
                                type='default'
                                size='small'
                                onClick={() => onSelectCategory?.(cat)}
                            >
                                {cat}
                            </Button>
                        ))}
                    </Space>
                </div>
            )}

            {/* PDF・関連情報 */}
            {msg.sources?.length ? (
                <div style={{ marginTop: 16 }}>
                    <Space
                        direction='vertical'
                        size={8}
                        style={{ width: '100%' }}
                    >
                        {msg.sources.map((src, i) => (
                            <Card
                                key={i}
                                type='inner'
                                style={{
                                    borderRadius: 8,
                                    background: '#fafafa',
                                }}
                            >
                                <Space>
                                    <Tag color='blue'>{src.pdf}</Tag>
                                    <Tag color='purple'>
                                        {src.section_title}
                                    </Tag>
                                </Space>
                                <Typography.Text
                                    type='secondary'
                                    style={{ display: 'block' }}
                                >
                                    {src.highlight}
                                </Typography.Text>
                                <Button
                                    type='link'
                                    size='small'
                                    icon={<BookOutlined />}
                                    onClick={() => onOpenPdf?.(src.pdf)}
                                    style={{ padding: 0, marginTop: 2 }}
                                >
                                    PDFを開く
                                </Button>
                            </Card>
                        ))}
                    </Space>
                </div>
            ) : null}
        </Card>
    );
};

export default ChatMessageCard;
