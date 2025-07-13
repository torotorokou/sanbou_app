import React from 'react';
import { Card, Select, Input, Typography } from 'antd';

const { Option } = Select;
const { TextArea } = Input;

type Props = {
    category: string;
    setCategory: (val: string) => void;
    tag: string;
    setTag: (val: string) => void;
    template: string;
    setTemplate: (val: string) => void;
    question: string;
    setQuestion: (val: string) => void;
    // onSubmit, loadingは不要
};

const QuestionPanel: React.FC<Props> = ({
    category,
    setCategory,
    tag,
    setTag,
    template,
    setTemplate,
    question,
    setQuestion,
}) => {
    return (
        <div style={{ marginBottom: 32 }}>
            <Typography.Title level={4} style={{ marginBottom: 24 }}>
                質問を入力
            </Typography.Title>
            <Card
                bordered={false}
                className='no-hover'
                style={{
                    borderRadius: 16,
                    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                    padding: 32,
                    minHeight: 520,
                    display: 'flex',
                    flexDirection: 'column',
                }}
            >
                <div style={{ marginBottom: 32 }}>
                    <Typography.Text strong>カテゴリ</Typography.Text>
                    <Select
                        placeholder='カテゴリを選択'
                        value={category || undefined}
                        onChange={setCategory}
                        style={{ width: '100%', marginTop: 8 }}
                    >
                        {['処理', '設備', '法令', '運搬', '分析'].map((cat) => (
                            <Option key={cat} value={cat}>
                                {cat}
                            </Option>
                        ))}
                    </Select>
                </div>

                <div style={{ marginBottom: 32 }}>
                    <Typography.Text strong>タグ（任意）</Typography.Text>
                    <Select
                        placeholder='タグを選択'
                        value={tag || undefined}
                        onChange={setTag}
                        allowClear
                        style={{ width: '100%', marginTop: 8 }}
                    >
                        {['構造', '機能', '管理', '安全'].map((t) => (
                            <Option key={t} value={t}>
                                {t}
                            </Option>
                        ))}
                    </Select>
                </div>

                <div style={{ marginBottom: 32 }}>
                    <Typography.Text strong>テンプレート</Typography.Text>
                    <Select
                        value={template}
                        onChange={(val) => {
                            setTemplate(val);
                            if (val !== '自由入力') setQuestion(val);
                        }}
                        style={{ width: '100%', marginTop: 8 }}
                    >
                        <Option value='自由入力'>自由入力</Option>
                        <Option value='○○の役割は？'>○○の役割は？</Option>
                        <Option value='○○の構造を説明してください'>
                            ○○の構造を説明してください
                        </Option>
                    </Select>
                </div>

                <div style={{ marginBottom: 32 }}>
                    <Typography.Text strong>質問内容</Typography.Text>
                    <TextArea
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder='質問を入力してください'
                        allowClear
                        autoSize={{ minRows: 6, maxRows: 10 }}
                        style={{ marginTop: 8 }}
                    />
                </div>
                {/* 送信ボタンは完全削除 */}
            </Card>
        </div>
    );
};

export default QuestionPanel;
