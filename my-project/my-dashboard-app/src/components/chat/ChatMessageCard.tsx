import React from 'react';
import { Card, Typography, Button, Tag } from 'antd';
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

const ChatMessageCard: React.FC<Props> = ({
    msg,
    index,
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
            background: msg.role === 'user' ? '#f6ffed' : '#e6f7ff',
        };
    };

    return (
        <Card
            size='small'
            title={msg.role === 'user' ? '👤 あなた' : '🤖 AI'}
            style={getCardStyle()}
        >
            <Typography.Paragraph>
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

            {msg.type === 'category-buttons' && (
                <div style={{ marginTop: 8 }}>
                    <Typography.Text
                        strong
                        style={{ display: 'block', marginBottom: 8 }}
                    >
                        📚 カテゴリ一覧
                    </Typography.Text>
                    {['処理', '設備', '法令', '運搬', '分析'].map((cat) => (
                        <Button
                            key={cat}
                            onClick={() => onSelectCategory?.(cat)}
                            style={{ marginRight: 8, marginBottom: 8 }}
                        >
                            {cat}
                        </Button>
                    ))}
                </div>
            )}

            {msg.sources?.map((src, i) => (
                <div key={i} style={{ marginTop: 8 }}>
                    <Tag color='blue'>{src.pdf}</Tag>
                    <Tag color='purple'>{src.section_title}</Tag>
                    <Typography.Text type='secondary'>
                        {src.highlight}
                    </Typography.Text>
                    <br />
                    <Button
                        type='link'
                        size='small'
                        onClick={() => onOpenPdf?.(src.pdf)}
                    >
                        📖 PDFを開く
                    </Button>
                </div>
            ))}
        </Card>
    );
};

export default ChatMessageCard;
