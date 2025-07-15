import React, { useState } from 'react';
import { Typography, Spin, Button, Card, Drawer } from 'antd';
import { FilePdfOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import axios from 'axios';
import { pdfjs } from 'react-pdf';
import ChatQuestionSection from '@/components/chat/ChatQuestionSection';
import ChatSendButtonSection from '@/components/chat/ChatSendButtonSection';
import ChatAnswerSection from '@/components/chat/ChatAnswerSection';
import PdfPreviewModal from '@/components/chat/PdfPreviewModal';
import type { StepItem } from '@/components/ui/ReportStepIndicator';
import ReportStepIndicator from '@/components/ui/ReportStepIndicator';

// ✅ PDF.js workerSrc の指定（react-pdf 9.x 以降の書き方）
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    'pdfjs-dist/build/pdf.worker.min.mjs',
    import.meta.url
).toString();

const cardStyle = {
    borderRadius: 16,
    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
    padding: 10,
    marginBottom: 0,
    background: '#fff',
};

const allPdfList = [
    'doc1.pdf',
    'manual2.pdf',
    'specs2024.pdf',
    '規程集.pdf',
    '重要通知.pdf',
    'report2022.pdf',
    'guide.pdf',
    'data.pdf',
    'flow.pdf',
    'notes.pdf',
];

const stepItems: StepItem[] = [
    { title: '分類', description: 'カテゴリ選択' },
    { title: '質問作成', description: '質問入力' },
    { title: '送信', description: 'AIに質問' },
    { title: '結果', description: '回答を確認' },
];

const PdfChatBot: React.FC = () => {
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

    const [drawerOpen, setDrawerOpen] = useState(false);

    const handleSearch = async () => {
        if (!question.trim()) return;
        setCurrentStep(3);
        setLoading(true);
        try {
            const res = await axios.post('/api/ai/chat', {
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

    const handleSelectPdfFromAll = (pdf: string) => {
        setPdfToShow(`/pdf/${pdf}`);
        setPdfModalVisible(true);
        setDrawerOpen(false);
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
                <ReportStepIndicator
                    currentStep={currentStep}
                    items={stepItems}
                />
            </div>

            <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                {/* 左カラム */}
                <ChatQuestionSection
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
                    sources={sources}
                    onOpenPdf={(path) => {
                        if (path && path.endsWith('.pdf')) {
                            setPdfToShow(path);
                            setPdfModalVisible(true);
                        }
                    }}
                    cardStyle={cardStyle}
                />

                {/* 中央カラム */}
                <ChatSendButtonSection
                    onClick={handleSearch}
                    disabled={!question.trim() || loading}
                />

                {/* 右カラム */}
                <ChatAnswerSection answer={answer} />
            </div>

            {/* ===== 下部の小さなPDF一覧表示ボタン（常時表示） ===== */}
            <div
                style={{
                    width: '100vw',
                    position: 'fixed',
                    left: 0,
                    bottom: 0,
                    zIndex: 200,
                    display: 'flex',
                    justifyContent: 'center',
                    pointerEvents: 'auto',
                    paddingBottom: 8,
                }}
            >
                <Button
                    size='small'
                    style={{
                        width: 130,
                        height: 32,
                        borderRadius: 24,
                        boxShadow: '0 4px 16px rgba(0,0,0,0.10)',
                        background: '#fff',
                        fontWeight: 600,
                        transition: 'all 0.3s ease',
                        overflow: 'hidden',
                        whiteSpace: 'nowrap',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 6,
                    }}
                    onClick={() => setDrawerOpen(true)}
                    onMouseEnter={(e) => {
                        const btn = e.currentTarget;
                        btn.style.width = '180px';
                        btn.style.height = '48px';
                        btn.style.fontSize = '16px';
                        btn.style.padding = '0 24px';
                    }}
                    onMouseLeave={(e) => {
                        const btn = e.currentTarget;
                        btn.style.width = '130px';
                        btn.style.height = '32px';
                        btn.style.fontSize = '';
                        btn.style.padding = '';
                    }}
                >
                    <MenuUnfoldOutlined style={{ fontSize: 18 }} />
                    PDF一覧を表示
                </Button>
            </div>

            {/* Drawer: 全PDFファイル一覧（クリックでモーダル表示） */}
            <Drawer
                title={
                    <span>
                        <FilePdfOutlined
                            style={{ marginRight: 8, color: '#d32029' }}
                        />
                        全PDFファイル一覧
                    </span>
                }
                placement='bottom'
                open={drawerOpen}
                onClose={() => setDrawerOpen(false)}
                height={180}
                closable={true}
                styles={{
                    body: {
                        background: '#fafbfc',
                        padding: '18px 20px 8px 20px',
                        overflowX: 'auto',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                    },
                }}
            >
                <div
                    style={{
                        display: 'flex',
                        flexDirection: 'row',
                        gap: 16,
                        overflowX: 'auto',
                        paddingBottom: 8,
                    }}
                >
                    {allPdfList.map((pdf) => (
                        <Card
                            key={pdf}
                            hoverable
                            size='small'
                            style={{
                                width: 120,
                                height: 72,
                                minWidth: 100,
                                textAlign: 'center',
                                cursor: 'pointer',
                                overflow: 'hidden',
                                padding: 4,
                                border: '1px solid #e5e5e5',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                background: '#fff',
                            }}
                            styles={{
                                body: {
                                    padding: 4,
                                    minHeight: 12,
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                },
                            }}
                            onClick={() => handleSelectPdfFromAll(pdf)}
                        >
                            <div style={{ fontSize: 22, marginBottom: 2 }}>
                                📄
                            </div>
                            <div
                                style={{
                                    fontSize: 12,
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                    width: 96,
                                }}
                                title={pdf}
                            >
                                {pdf}
                            </div>
                        </Card>
                    ))}
                </div>
            </Drawer>

            {/* モーダルPDFプレビュー */}
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

export default PdfChatBot;
