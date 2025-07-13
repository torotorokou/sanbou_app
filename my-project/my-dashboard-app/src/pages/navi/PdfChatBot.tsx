// src/pages/SearchSplitView.tsx
import React, { useState } from 'react';
import { Steps, Typography, Spin, Button, Card } from 'antd';
import axios from 'axios';
import QuestionPanel from '@/components/chat/QuestionPanel';
import PdfCardList from '@/components/chat/PdfCardList';
import AnswerViewer from '@/components/chat/AnswerViewer';
import PdfPreviewModal from '@/components/chat/PdfPreviewModal';

const { Step } = Steps;

const cardStyle = {
    borderRadius: 16,
    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
    padding: 32,
    marginBottom: 0,
    background: '#fff', // AntDデフォルトカード色に統一
};

const SearchSplitView: React.FC = () => {
    const [category, setCategory] = useState('');
    const [tag, setTag] = useState('');
    const [template, setTemplate] = useState('自由入力');
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState('');
    const [sources, setSources] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [pdfToShow, setPdfToShow] = useState<string | null>(null);
    const [pdfModalVisible, setPdfModalVisible] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);

    const handleSearch = async () => {
        if (!question.trim()) return;
        setCurrentStep(3);
        setLoading(true);
        try {
            const res = await axios.post('/api/chat', {
                query: question,
                tags: [category, tag].filter(Boolean),
            });
            setAnswer(res.data.answer || '');
            setSources(
                res.data.sources?.filter(
                    (src: any) =>
                        typeof src.pdf === 'string' &&
                        src.pdf.endsWith('.pdf') &&
                        typeof src.section_title === 'string' &&
                        src.section_title.length > 0
                ) || []
            );
        } catch (err) {
            console.error(err);
            setAnswer('エラーが発生しました。');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div
            style={{
                height: '100vh',
                display: 'flex',
                flexDirection: 'column',
            }}
        >
            {loading && (
                <Spin tip='AIが回答中です...' size='large' fullscreen />
            )}

            <div style={{ padding: '12px 24px' }}>
                <Steps current={currentStep} size='small'>
                    <Step title='分類' />
                    <Step title='質問作成' />
                    <Step title='送信' />
                    <Step title='結果' />
                </Steps>
            </div>

            {/* 3カラム分割 */}
            <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                {/* 左カラム：質問フォーム＋関連PDF */}
                <div
                    style={{
                        width: 420,
                        padding: 24,
                        overflowY: 'auto',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 32,
                    }}
                >
                    {/* 入力欄カード */}
                    <QuestionPanel
                        category={category}
                        setCategory={(val) => {
                            setCategory(val);
                            setCurrentStep(1);
                        }}
                        tag={tag}
                        setTag={setTag}
                        template={template}
                        setTemplate={(val) => {
                            setTemplate(val);
                            if (val !== '自由入力') {
                                setQuestion(val);
                                setCurrentStep(2);
                            }
                        }}
                        question={question}
                        setQuestion={(val) => {
                            setQuestion(val);
                            if (val.trim()) setCurrentStep(2);
                        }}
                    />

                    {/* 関連PDFカード（他とデザイン統一） */}
                    <Card
                        bordered={false}
                        style={cardStyle}
                        bodyStyle={{ padding: '20px 24px 12px 24px' }}
                    >
                        <Typography.Title
                            level={5}
                            style={{ marginBottom: 10 }}
                        >
                            📄 関連PDF
                        </Typography.Title>
                        <PdfCardList
                            sources={sources}
                            onOpen={(path) => {
                                if (path && path.endsWith('.pdf')) {
                                    setPdfToShow(path);
                                    setPdfModalVisible(true);
                                }
                            }}
                        />
                    </Card>
                </div>

                {/* 中央カラム：送信ボタン */}
                <div
                    style={{
                        width: 120,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: 'transparent',
                    }}
                >
                    <Button
                        type='primary'
                        size='large'
                        block
                        style={{ height: 60, fontSize: 18 }}
                        disabled={!question.trim() || loading}
                        onClick={handleSearch}
                    >
                        質問を送信
                    </Button>
                </div>

                {/* 右カラム：回答 */}
                <div style={{ flex: 1, padding: 24, overflowY: 'auto' }}>
                    <Typography.Title level={4}>🤖 回答結果</Typography.Title>
                    <AnswerViewer answer={answer} />
                </div>
            </div>

            {/* PDFプレビューモーダル */}
            <PdfPreviewModal
                visible={pdfModalVisible}
                pdfUrl={pdfToShow}
                onClose={() => {
                    setPdfToShow(null);
                    setPdfModalVisible(false);
                }}
            />
        </div>
    );
};

export default SearchSplitView;
