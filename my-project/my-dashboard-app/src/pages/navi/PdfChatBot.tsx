import React, { useState } from 'react';
import { Typography, Spin, Button, Card, Drawer } from 'antd';
import {
    FilePdfOutlined,
    MenuUnfoldOutlined,
    SendOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import { pdfjs } from 'react-pdf';
import QuestionPanel from '@/components/chat/QuestionPanel';
import PdfCardList from '@/components/chat/PdfCardList';
import AnswerViewer from '@/components/chat/AnswerViewer';
import PdfPreviewModal from '@/components/chat/PdfPreviewModal';
import VerticalActionButton from '@/components/ui/VerticalActionButton';
import type { StepItem } from '@/components/ui/ReportStepIndicator';
import ReportStepIndicator from '@/components/ui/ReportStepIndicator';
// PDF.js workerSrc の指定
pdfjs.GlobalWorkerOptions.workerSrc = '/pdfjs/pdf.worker.min.js';

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

// ステップの内容を自由にカスタマイズ可能
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

    // Drawer用
    const [drawerOpen, setDrawerOpen] = useState(false);

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

    // 全PDF一覧から選択時
    const handleSelectPdfFromAll = (pdf: string) => {
        setPdfToShow(`/pdf/${pdf}`); // ← ここでフルパスにして渡す
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

            {/* ステップインジケーターを共通UIで */}
            <div style={{ padding: '12px 24px' }}>
                <ReportStepIndicator
                    currentStep={currentStep}
                    items={stepItems}
                />
            </div>

            <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                {/* 左カラム：質問フォーム＋関連PDF */}
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

                    <Typography.Title level={5} style={{ marginBottom: 5 }}>
                        📄 関連PDF
                    </Typography.Title>
                    <Card
                        variant='borderless'
                        styles={{ body: { padding: '4px 8px' } }}
                        style={cardStyle}
                    >
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

                {/* 中央カラム：送信ボタン（縦書き VerticalActionButton 使用） */}
                <div
                    style={{
                        width: 70,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: 'transparent',
                    }}
                >
                    <VerticalActionButton
                        icon={<SendOutlined />}
                        text='質問を送信'
                        onClick={handleSearch}
                        disabled={!question.trim() || loading}
                        // backgroundColor='#1677ff'
                        // writingMode='vertical-rl'
                    />
                </div>

                {/* 右カラム：回答 */}
                <div style={{ flex: 1, padding: 24, overflowY: 'auto' }}>
                    <Typography.Title level={4}>🤖 回答結果</Typography.Title>
                    <AnswerViewer answer={answer} />
                </div>
            </div>

            {/* ===== 下部 Drawerトリガー ===== */}
            <div
                style={{
                    width: '100vw',
                    position: 'fixed',
                    left: 0,
                    bottom: 0,
                    zIndex: 200,
                    display: 'flex',
                    justifyContent: 'center',
                    pointerEvents: 'none',
                }}
            >
                <Button
                    icon={
                        <MenuUnfoldOutlined
                            style={{ fontSize: 22, verticalAlign: -4 }}
                        />
                    }
                    size='large'
                    style={{
                        margin: 8,
                        borderRadius: 24,
                        boxShadow: '0 4px 16px rgba(0,0,0,0.10)',
                        background: '#fff',
                        pointerEvents: 'auto',
                        display: 'flex',
                        alignItems: 'center',
                        fontWeight: 600,
                    }}
                    onClick={() => setDrawerOpen(true)}
                >
                    すべてのPDFを見る
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
