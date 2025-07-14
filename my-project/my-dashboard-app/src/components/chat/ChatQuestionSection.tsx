// ChatQuestionSection.tsx
import React from 'react';
import QuestionPanel from '@/components/chat/QuestionPanel';
import PdfCardList from '@/components/chat/PdfCardList';
import { Typography, Card } from 'antd';

type Props = {
    category: string;
    setCategory: (val: string) => void;
    tag: string;
    setTag: (val: string) => void;
    template: string;
    setTemplate: (val: string) => void;
    question: string;
    setQuestion: (val: string) => void;
    sources: any[];
    onOpenPdf: (path: string) => void;
    cardStyle?: React.CSSProperties;
};

const defaultCardStyle: React.CSSProperties = {
    borderRadius: 16,
    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
    padding: 0, // パディングを小さくして縦をコンパクトに
    marginBottom: 0,
    background: '#fff',
};

const ChatQuestionSection: React.FC<Props> = ({
    category,
    setCategory,
    tag,
    setTag,
    template,
    setTemplate,
    question,
    setQuestion,
    sources,
    onOpenPdf,
    cardStyle,
}) => (
    <div
        style={{
            width: 420,
            padding: 24,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
        }}
    >
        {/* QuestionPanelをそのまま使う */}
        <QuestionPanel
            category={category}
            setCategory={setCategory}
            tag={tag}
            setTag={setTag}
            template={template}
            setTemplate={setTemplate}
            question={question}
            setQuestion={setQuestion}
        />
        <Typography.Title level={5} style={{ marginBottom: 1 }}>
            📄 関連PDF
        </Typography.Title>
        <Card
            variant='borderless'
            style={{ ...cardStyle, padding: 10 }}
            bodyStyle={{ padding: 10 }}
        >
            <PdfCardList sources={sources} onOpen={onOpenPdf} />
        </Card>
    </div>
);

export default ChatQuestionSection;
