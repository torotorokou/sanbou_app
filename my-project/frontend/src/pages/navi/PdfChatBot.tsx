import React, { useMemo, useState } from 'react';
import { Spin, Button, Card, Drawer } from 'antd';
import { FilePdfOutlined } from '@ant-design/icons';
import axios from 'axios';
import { pdfjs } from 'react-pdf';
import ChatQuestionSection from '@/components/chat/ChatQuestionSection';
import ChatSendButtonSection from '@/components/chat/ChatSendButtonSection';
import ChatAnswerSection from '@/components/chat/ChatAnswerSection';
import PdfPreviewModal from '@/components/chat/PdfPreviewModal';
import type { StepItem } from '@/components/ui/ReportStepIndicator';
import ReportStepIndicator from '@/components/ui/ReportStepIndicator';
// YAMLを直接インポート（viteの@rollup/plugin-yamlでJSON化）
import categoryYaml from '@/config/category_question_templates.yaml';

// ✅ PDF.js workerSrc の指定（react-pdf 9.x 以降の書き方）
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    'pdfjs-dist/build/pdf.worker.min.mjs',
    import.meta.url
).toString();

// 関連PDFカード削除に伴いcardStyleは不要

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
    const [tags, setTag] = useState<string[]>([]);
    const [template, setTemplate] = useState('自由入力');
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState('');
    const [sources, setSources] = useState<{ pdf: string; section_title: string }[]>([]);
    const [loading, setLoading] = useState(false);
    const [pdfToShow, setPdfToShow] = useState<string | null>(null);
    const [pdfModalVisible, setPdfModalVisible] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);

    const [drawerOpen, setDrawerOpen] = useState(false);

    // 選択テンプレートに紐づく推奨タグ（YAML）を取得（※送信には使用しない）
    const templateTags = useMemo(() => {
        if (!category || !template || template === '自由入力') return [] as string[];
        const items = (categoryYaml as Record<string, { title: string; tag: string[] }[]>)[category] || [];
        const found = items.find((it) => it.title === template);
        return found?.tag ?? [];
    }, [category, template]);

    // 送信用：ユーザー選択のみ（一意化＆空除去）
    const tagsToSend = useMemo(
        () => Array.from(new Set(tags)).filter(Boolean),
        [tags]
    );

    const handleSearch = async () => {
        if (!question.trim()) return;
        setCurrentStep(3);
        setLoading(true);

        // ★ 送信するのはユーザー選択のタグのみ（templateTagsは結合しない）
        const payload = {
            query: question,
            category: category,
            tags: tagsToSend,
        };

        console.log('送信するデータ:', payload);

        try {
            const res = await axios.post('/ai_api/chat', payload);
            setAnswer(res.data.answer || '');
            setSources(
                (res.data.sources || [])
                    .filter(
                        (src: { pdf?: unknown; section_title?: unknown }) =>
                            typeof src.pdf === 'string' &&
                            (src.pdf as string).endsWith('.pdf') &&
                            typeof src.section_title === 'string' &&
                            (src.section_title as string).length > 0
                    )
                    .map((src: { pdf: string; section_title: string }) => ({
                        pdf: src.pdf,
                        section_title: src.section_title,
                    }))
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
            {loading && <Spin tip='AIが回答中です...' size='large' fullscreen />}

            <div style={{ padding: '12px 24px' }}>
                <ReportStepIndicator currentStep={currentStep} items={stepItems} />
            </div>

            <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                {/* 左カラム */}
                <ChatQuestionSection
                    category={category}
                    setCategory={(val) => {
                        setCategory(val);
                        setCurrentStep(1);
                        // カテゴリ変更時に選択をリセット
                        setTag([]);
                        setTemplate('自由入力');
                    }}
                    tags={tags}
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
                    categoryData={categoryYaml as Record<string, { title: string; tag: string[] }[]>}
                />

                {/* 中央カラム */}
                <ChatSendButtonSection
                    onClick={handleSearch}
                    disabled={!question.trim() || tags.length === 0 || loading}
                />

                {/* 右カラム */}
                <ChatAnswerSection answer={answer} />
            </div>

            {/* ===== 下部の参考PDFボタン（関連PDFを直接開く） ===== */}
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
                    disabled={sources.length === 0}
                    onClick={() => {
                        if (sources.length > 0) {
                            const first = sources[0];
                            setPdfToShow(`/pdf/${first.pdf}`);
                            setPdfModalVisible(true);
                        }
                    }}
                    onMouseEnter={(e) => {
                        if (sources.length === 0) return;
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
                    <FilePdfOutlined style={{ fontSize: 18 }} />
                    参考PDF
                </Button>
            </div>

            {/* Drawer: 全PDFファイル一覧（クリックでモーダル表示） */}
            <Drawer
                title={
                    <span>
                        <FilePdfOutlined style={{ marginRight: 8, color: '#d32029' }} />
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
                            <div style={{ fontSize: 22, marginBottom: 2 }}>📄</div>
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
            {pdfToShow && (
                <PdfPreviewModal
                    visible={pdfModalVisible}
                    pdfUrl={pdfToShow}
                    onClose={() => {
                        setPdfToShow(null);
                        setPdfModalVisible(false);
                    }}
                />
            )}
        </div>
    );
};

export default PdfChatBot;
