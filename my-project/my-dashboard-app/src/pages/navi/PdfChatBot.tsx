// SearchSplitView.tsx
import React, { useState } from 'react';
import { Steps, Typography, Spin } from 'antd';
import axios from 'axios';
import QuestionPanel from '@/components/chat/QuestionPanel';
import PdfCardList from '@/components/chat/PdfCardList';
import AnswerViewer from '@/components/chat/AnswerViewer';
import PdfPreviewModal from '@/components/chat/PdfPreviewModal';

const { Step } = Steps;

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

            <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                <div
                    style={{
                        width: 500,
                        padding: 24,
                        background: '#f0f2f5',
                        overflowY: 'auto',
                    }}
                >
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
                        onSubmit={handleSearch}
                        loading={loading}
                    />

                    <Typography.Title level={5}>📄 関連PDF</Typography.Title>
                    <PdfCardList
                        sources={sources}
                        onOpen={(path) => {
                            if (path && path.endsWith('.pdf')) {
                                setPdfToShow(path);
                                setPdfModalVisible(true);
                            }
                        }}
                    />
                </div>

                <div style={{ flex: 1, padding: 24, overflowY: 'auto' }}>
                    <Typography.Title level={4}>🤖 回答結果</Typography.Title>
                    <AnswerViewer answer={answer} />
                </div>
            </div>

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
