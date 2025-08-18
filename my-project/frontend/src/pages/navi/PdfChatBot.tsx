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

// ✅ 追加: 通知ストア
import { useNotificationStore } from '@/stores/notificationStore';

// ✅ PDF.js workerSrc の指定（react-pdf 9.x 以降の書き方）
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    'pdfjs-dist/build/pdf.worker.min.mjs',
    import.meta.url
).toString();

// 共通APIレスポンス型（バックエンド契約に合わせる）
type ApiResponse<T> = {
    status: 'success' | 'error';
    code: string;
    detail: string;
    result?: T | null;
    hint?: string | null;
};

// 今回の業務ペイロード
type ChatAnswerResult = {
    answer: string;
    pdf_url?: string | null;
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
    const [tags, setTag] = useState<string[]>([]);
    const [template, setTemplate] = useState('自由入力');
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState('');
    const [loading, setLoading] = useState(false);
    const [pdfUrl, setPdfUrl] = useState<string | null>(null); // ★ APIが返すPDFのURL
    const [pdfToShow, setPdfToShow] = useState<string | null>(null);
    const [pdfModalVisible, setPdfModalVisible] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);

    const [drawerOpen, setDrawerOpen] = useState(false);

    // ✅ 追加: 通知のadd関数を取得
    const addNotification = useNotificationStore((s) => s.addNotification);

    // 選択テンプレートに紐づく推奨タグ（YAML）を取得（※送信には使用しない）
    const templateTags = useMemo(() => {
        if (!category || !template || template === '自由入力') return [] as string[];
        const items =
            (categoryYaml as Record<string, { title: string; tag: string[] }[]>)[category] || [];
        const found = items.find((it) => it.title === template);
        return found?.tag ?? [];
    }, [category, template]);

    // 送信用：ユーザー選択のみ（一意化＆空除去）
    const tagsToSend = useMemo(() => Array.from(new Set(tags)).filter(Boolean), [tags]);

    const handleSearch = async (): Promise<void> => {
        if (!question.trim()) return;
        setCurrentStep(3);
        setLoading(true);

        // ★ 送信するのはユーザー選択のタグのみ（templateTagsは結合しない）
        const payload = {
            query: question,
            category: category,
            tags: tagsToSend,
        };

        console.log('[API][REQUEST] /rag_api/api/generate-answer payload:', payload);

        try {
            const res = await axios.post<ApiResponse<ChatAnswerResult> | any>(
                '/rag_api/api/generate-answer',
                payload
            );

            // ★ 詳細ログ
            console.log('[API][RESPONSE] status:', res.status, res.statusText);
            console.log('[API][RESPONSE] headers:', res.headers);
            console.log('[API][RESPONSE] data:', res.data);

            // 正規化: 新契約(ApiResponse) or 旧スキーマ(トップレベルkeys)
            let normalized: { answer: string; pdf_url?: string | null } | null = null;

            if (res.data && typeof res.data === 'object' && 'status' in res.data) {
                // 新契約
                if (res.data.status !== 'success') {
                    console.error('[API][ERROR] detail:', res.data?.detail, 'code:', res.data?.code);
                    setAnswer(res.data?.detail ?? 'エラーが発生しました。');
                    setPdfUrl(null);
                    addNotification({
                        type: 'error',
                        title: '取得に失敗しました',
                        message: res.data?.detail || 'サーバーからエラーが返されました。',
                        duration: 4000,
                    });
                    return;
                }
                const result = res.data?.result ?? null;
                normalized = {
                    answer: result?.answer ?? '',
                    pdf_url: result?.pdf_url ?? null,
                };
            } else {
                // 旧スキーマ: answer, pdf_urls, pages, merged_pdf_url などが直下に来る
                const legacy = res.data ?? {};
                normalized = {
                    answer: legacy.answer ?? '',
                    // merged_pdf_url > pdf_url の優先で採用
                    pdf_url: legacy.merged_pdf_url ?? legacy.pdf_url ?? null,
                };
            }

            setAnswer(normalized?.answer ?? '');
            setPdfUrl(normalized?.pdf_url ?? null);

            // ✅ 成功通知（任意）
            addNotification({
                type: 'success',
                title: 'AI応答を取得しました',
                message: normalized?.pdf_url ? '回答とPDFリンクを受信しました。' : '回答を受信しました。',
                duration: 2500,
            });
        } catch (err: unknown) {
            // 失敗時もできる限り詳細を表示
            if (axios.isAxiosError(err)) {
                console.error('[API][ERROR] AxiosError message:', err.message);
                console.error('[API][ERROR] request:', err.config);
                if (err.response) {
                    console.error('[API][ERROR] status:', err.response.status);
                    console.error('[API][ERROR] headers:', err.response.headers);
                    console.error('[API][ERROR] data:', err.response.data);
                } else {
                    console.error('[API][ERROR] no response (network?)');
                }
            } else {
                console.error('[API][ERROR] Unknown error:', err);
            }
            setAnswer('エラーが発生しました。');
            setPdfUrl(null);

            // ✅ 失敗通知
            addNotification({
                type: 'error',
                title: '取得に失敗しました',
                message: 'ネットワークまたはサーバーエラーです。',
                duration: 4000,
            });
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
            {loading && <Spin tip="AIが回答中です..." size="large" fullscreen />}

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
                    categoryData={
                        categoryYaml as Record<string, { title: string; tag: string[] }[]>
                    }
                />

                {/* 中央カラム */}
                <ChatSendButtonSection
                    onClick={handleSearch}
                    // タグ必須の要件でなければ "|| tags.length === 0" は外す
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
                    size="small"
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
                    disabled={!pdfUrl} // ★ pdfUrl が無いときは無効化
                    onClick={() => {
                        if (pdfUrl) {
                            // /pdfs/... → /rag_api/pdfs/... に補正
                            const normalizePdfUrl = (p: string): string => {
                                if (!p) return p;

                                // すでに rag_api/pdfs ならそのまま
                                if (p.startsWith('/rag_api/pdfs/')) return p;

                                // バックエンドが返す /pdfs/... を /rag_api/pdfs/... に置換
                                if (p.startsWith('/pdfs/')) {
                                    return p.replace('/pdfs/', '/rag_api/pdfs/');
                                }

                                // ファイル名だけなら /rag_api/pdfs に寄せる
                                return `/rag_api/pdfs/${p.replace(/^\//, '')}`;
                            };

                            const url = normalizePdfUrl(pdfUrl);
                            console.log('[参考PDF URL]', url);

                            setPdfToShow(url);
                            setPdfModalVisible(true);
                        }
                    }}

                    onMouseEnter={(e) => {
                        if (!pdfUrl) return;
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
                placement="bottom"
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
                            size="small"
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
