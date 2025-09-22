import React, { useMemo, useState } from 'react';
import { Spin, Button } from 'antd';
import { FilePdfOutlined } from '@ant-design/icons';
import { apiGet, apiPost } from '@/services/httpClient';
import { pdfjs } from 'react-pdf';
import ChatQuestionSection from '@/components/chat/ChatQuestionSection';
import ChatSendButtonSection from '@/components/chat/ChatSendButtonSection';
import ChatAnswerSection from '@/components/chat/ChatAnswerSection';
import PdfPreviewModal from '@/components/chat/PdfPreviewModal';
import type { StepItem } from '@/components/ui/ReportStepIndicator';
import ReportStepIndicator from '@/components/ui/ReportStepIndicator';
import { useWindowSize } from '@/hooks/ui';
import { BREAKPOINTS as BP } from '@/shared/constants/breakpoints';
// YAMLを直接インポート（viteの@rollup/plugin-yamlでJSON化）
// YAML直読みを廃止し、バックエンドAPIから取得する

// ✅ 追加: 通知ストア
import { useNotificationStore } from '@/stores/notificationStore';

// ✅ PDF.js workerSrc の指定（react-pdf 9.x 以降の書き方）
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    'pdfjs-dist/build/pdf.worker.min.mjs',
    import.meta.url
).toString();

// 共通APIレスポンス型（バックエンド契約に合わせる）
// 共通APIレスポンス: src/types/api.ts を参照

// 今回の業務ペイロード
type ChatAnswerResult = {
    answer: string;
    pdf_url?: string | null;
};

// allPdfList と関連UIは削除（未使用）

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

    // Drawerや左サイドのPDF一覧は廃止

    // ✅ 追加: 通知のadd関数を取得
    const addNotification = useNotificationStore((s) => s.addNotification);

    // バックエンドから取得するカテゴリ/テンプレート/タグの辞書
    const [categoryData, setCategoryData] = useState<
        Record<string, { title: string; tag: string[] }[]>
    >({});

    // 初回マウント時に質問テンプレート一覧を取得
    React.useEffect(() => {
        const fetchOptions = async () => {
            try {
                // backend: rag_api -> /rag_api/api/question-options
                const res = await apiGet<Record<string, { title: string; tag: string[] }[]>>('/rag_api/api/question-options');
                // 期待フォーマット: { [category]: [{ title, tag: string[] }] }
                if (res && typeof res === 'object') {
                    setCategoryData(res as Record<string, { title: string; tag: string[] }[]>);
                } else {
                    console.warn('[API][question-options] Unexpected payload:', res);
                    setCategoryData({});
                }
            } catch (err) {
                console.error('[API][ERROR] /question-options:', err);
                setCategoryData({});
                addNotification({
                    type: 'error',
                    title: '質問テンプレートの取得に失敗',
                    message: 'カテゴリ・テンプレート候補を取得できませんでした。',
                    duration: 4000,
                });
            }
        };
        fetchOptions();
    }, []);

    // YAML直参照を廃止したため、推奨タグの内部利用はなし

    // 送信用：ユーザー選択のみ（一意化＆空除去）
    const tagsToSend = useMemo(() => Array.from(new Set(tags)).filter(Boolean), [tags]);

    // タグは最大3件までに制限するハンドラ
    const handleSetTag = (val: string[] | ((prev: string[]) => string[])) => {
        // val が関数か配列か両方に対応
        let nextTags: string[] = [];
        if (typeof val === 'function') {
            try {
                nextTags = val(tags) || [];
            } catch {
                nextTags = tags;
            }
        } else {
            nextTags = val || [];
        }
        // 一意化・空文字除去
        nextTags = Array.from(new Set(nextTags)).filter(Boolean);
        if (nextTags.length > 3) {
            // 上限超過は切り詰めて通知
            addNotification({
                type: 'warning',
                title: 'タグは3つまでです',
                message: 'タグは最大3つまで選択できます。先に選択した3つが採用されます。',
                duration: 3000,
            });
            nextTags = nextTags.slice(0, 3);
        }
        setTag(nextTags);
    };

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
            const res = await apiPost<ChatAnswerResult>(
                '/rag_api/api/generate-answer',
                payload
            );

            // ★ 詳細ログ
            console.log('[API][RESPONSE] data:', res);

            // 正規化: 新契約(ApiResponse) or 旧スキーマ(トップレベルkeys)
            // apiClientは成功時 resultを返す前提。旧スキーマ互換も一応考慮
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const anyRes: any = res ?? {};
            const normalized = {
                answer: anyRes.answer ?? '',
                pdf_url: anyRes.merged_pdf_url ?? anyRes.pdf_url ?? null,
            };

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
            console.error('[API][ERROR]', err);
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

    // 参考PDFの直接一覧表示機能は廃止

    const { width } = useWindowSize();
    const isNarrow = typeof width === 'number' ? width <= BP.mdMax : false;
    const isMd = typeof width === 'number' ? width >= BP.sm + 1 && width <= BP.mdMax : false;

    return (
        <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            {loading && <Spin tip="AIが回答中です..." size="large" fullscreen />}

            <div style={{ padding: '12px 24px' }}>
                <ReportStepIndicator currentStep={currentStep} items={stepItems} />
            </div>

            <div style={{ display: 'flex', flex: 1, overflow: 'hidden', minHeight: 0 }}>
                {/* 左 + 中央/右の組み替え: 狭い幅では質問フォーム下に送信ボタンを積む */}
                {isNarrow ? (
                    <>
                        <div
                            style={{
                                display: 'flex',
                                flex: isMd ? '1 1 50%' : '1 1 40%',
                                flexDirection: 'column',
                                minHeight: 0,
                            }}
                        >
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
                    // タグ更新はラッパー経由（最大3件制限）
                    setTag={handleSetTag}
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
                    categoryData={categoryData}
                />

                            <div style={{ padding: '4px 8px', display: 'flex', justifyContent: 'flex-start' }}>
                                <ChatSendButtonSection
                                    onClick={handleSearch}
                                    disabled={!question.trim() || tags.length === 0 || loading}
                                />
                            </div>
                        </div>

                        {/* 右カラム（回答） */}
                        <div style={{ flex: isMd ? '1 1 50%' : '1 1 60%', minHeight: 0 }}>
                            <ChatAnswerSection answer={answer} />
                        </div>
                    </>
                ) : (
                    /* 通常の 3 列レイアウト */
                    <>
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
                            // タグ更新はラッパー経由（最大3件制限）
                            setTag={handleSetTag}
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
                            categoryData={categoryData}
                        />

                        {/* 中央カラム */}
                        <ChatSendButtonSection
                            onClick={handleSearch}
                            // タグ必須の要件でなければ "|| tags.length === 0" は外す
                            disabled={!question.trim() || tags.length === 0 || loading}
                        />

                        {/* 右カラム */}
                        <ChatAnswerSection answer={answer} />
                    </>
                )}
            </div>

            {/* ===== 下部の参考PDFボタン（関連PDFを直接開く） ===== */}
            <div
                style={{
                    width: '100%',
                    maxWidth: '100%',
                    position: 'fixed',
                    left: 0,
                    bottom: 0,
                    zIndex: 200,
                    display: 'flex',
                    justifyContent: 'center',
                    pointerEvents: 'none',
                    paddingBottom: 'max(8px, env(safe-area-inset-bottom))',
                    boxSizing: 'border-box',
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
                        pointerEvents: 'auto',
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

            {/* Drawer機能・全PDF一覧は廃止しました */}

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
