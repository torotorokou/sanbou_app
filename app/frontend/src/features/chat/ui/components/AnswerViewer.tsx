import React from 'react';
import { Card, Typography } from 'antd';

type Props = {
    answer: string;
};

const AnswerViewer: React.FC<Props> = ({ answer }) => {
    return (
        <Card
            className="no-hover"
            style={{
                overflowY: 'auto',
                maxWidth: '100%',
                width: '100%',
                boxSizing: 'border-box',
                overflow: 'hidden',
            }}
        >
            <Typography.Paragraph
                style={{
                    marginBottom: 0,
                    color: '#333',
                    fontSize: '1rem',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    overflowWrap: 'anywhere',
                    maxWidth: '100%',
                }}
            >
                {answer && answer.trim()
                    ? answer
                    : 'ここに回答が表示されます'}
            </Typography.Paragraph>
        </Card>
    );
};

export { AnswerViewer };
