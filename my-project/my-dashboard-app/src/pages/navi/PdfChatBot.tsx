import React, { useState, useEffect, useRef } from 'react';
import {
    Layout,
    Select,
    Input,
    Button,
    Typography,
    Card,
    Tag,
    Modal,
    Empty,
    Space,
} from 'antd';
import axios from 'axios';
import TypewriterText from '@/components/ui/TypewriterText';
import type { ChatMessage } from '@/types/chat';

const { Content, Footer } = Layout;
const { Option } = Select;
const { TextArea } = Input;

const PdfChatBot: React.FC = () => {
    const [step, setStep] = useState(0);
    const [category, setCategory] = useState('');
    const [pdf, setPdf] = useState<string>();
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [pdfModalVisible, setPdfModalVisible] = useState(false);
    const [pdfToShow, setPdfToShow] = useState<string>('');
    const [windowWidth, setWindowWidth] = useState(window.innerWidth);
    const [isAtBottom, setIsAtBottom] = useState(true);
    const [hasNewMessage, setHasNewMessage] = useState(false);

    const contentRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleResize = () => setWindowWidth(window.innerWidth);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    useEffect(() => {
        if (isAtBottom && contentRef.current) {
            contentRef.current.scrollTop = contentRef.current.scrollHeight;
            setHasNewMessage(false); // 新着通知リセット
        } else if (!isAtBottom) {
            setHasNewMessage(true); // 新着フラグを立てる
        }
    }, [messages]);

    const handleScroll = () => {
        const el = contentRef.current;
        if (!el) return;
        const isBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
        setIsAtBottom(isBottom);
    };

    const handleStart = async () => {
        setMessages([{ role: 'bot', content: 'こんにちは！' }]);
        setStep(1);
        try {
            const res = await axios.get('/api/intro');
            setMessages((prev) => [
                ...prev,
                { role: 'bot', content: res.data.text },
            ]);
            setTimeout(() => {
                setMessages((prev) => [
                    ...prev,
                    { role: 'bot', content: '', type: 'category-buttons' },
                ]);
                setStep(2);
            }, 1500);
        } catch (err) {
            console.error('❌ intro取得失敗:', err);
        }
    };

    const handleCategorySelect = (cat: string) => {
        setCategory(cat);
        setMessages((prev) => [
            ...prev,
            {
                role: 'bot',
                content: `カテゴリ「${cat}」が選択されました。質問を入力してください。\nカテゴリを変更したい場合は、画面下の「カテゴリを変更」ボタンを押してください。`,
            },
        ]);
        setStep(3);
    };

    const handleSend = async () => {
        if (!input.trim()) return;
        setLoading(true);
        const userMessage: ChatMessage = { role: 'user', content: input };
        setMessages((prev) => [...prev, userMessage]);

        try {
            const res = await axios.post('/api/chat', {
                query: input,
                tags: [category],
                pdf,
            });
            if (res.data?.answer) {
                const botMessage: ChatMessage = {
                    role: 'bot',
                    content: res.data.answer,
                    sources: res.data.sources || [],
                };
                setMessages((prev) => [...prev, botMessage]);
            }
            setInput('');
        } catch (err: any) {
            console.error('❌ チャット送信エラー:', err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleCategoryChangeRequest = () => {
        setStep(2);
        setMessages((prev) => [
            ...prev,
            {
                role: 'bot',
                content: 'カテゴリを選び直してください。',
                type: 'category-buttons',
            },
        ]);
    };

    const openPdf = (pdfName?: string) => {
        if (!pdfName) return;
        setPdfToShow(`/pdf/${pdfName}`);
        setPdfModalVisible(true);
    };

    const getCardStyle = (role: 'user' | 'bot') => {
        let width = '100%';
        if (windowWidth >= 1024) {
            width = role === 'user' ? '40%' : '60%';
        } else if (windowWidth >= 768) {
            width = '70%';
        }
        return {
            width,
            alignSelf: role === 'user' ? 'flex-start' : 'flex-end',
            background: role === 'user' ? '#f6ffed' : '#e6f7ff',
        };
    };

    return (
        <Layout style={{ padding: 24, background: '#fff', height: '100%' }}>
            <Content
                ref={contentRef}
                onScroll={handleScroll}
                style={{
                    overflowY: 'auto',
                    maxHeight: '70vh',
                    marginBottom: 16,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 8,
                }}
            >
                {step === 0 && (
                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            height: '60vh',
                        }}
                    >
                        <Button
                            type='primary'
                            size='large'
                            onClick={handleStart}
                        >
                            🚀 参謀NAVIに聞いてみる
                        </Button>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <Card
                        key={idx}
                        size='small'
                        title={msg.role === 'user' ? '👤 あなた' : '🤖 AI'}
                        style={getCardStyle(msg.role)}
                    >
                        <Typography.Paragraph>
                            {msg.role === 'bot' &&
                            idx === messages.length - 1 &&
                            step <= 2 &&
                            !msg.type ? (
                                <TypewriterText text={msg.content} />
                            ) : (
                                msg.content?.split('\n').map((line, i) => (
                                    <React.Fragment key={i}>
                                        {line}
                                        <br />
                                    </React.Fragment>
                                ))
                            )}
                        </Typography.Paragraph>

                        {msg.type === 'category-buttons' && step === 2 && (
                            <div style={{ marginTop: 8 }}>
                                <Typography.Text
                                    strong
                                    style={{
                                        display: 'block',
                                        marginBottom: 8,
                                    }}
                                >
                                    📚 カテゴリ一覧
                                </Typography.Text>
                                {['処理', '設備', '法令', '運搬', '分析'].map(
                                    (cat) => (
                                        <Button
                                            key={cat}
                                            onClick={() =>
                                                handleCategorySelect(cat)
                                            }
                                            style={{
                                                marginRight: 8,
                                                marginBottom: 8,
                                            }}
                                        >
                                            {cat}
                                        </Button>
                                    )
                                )}
                            </div>
                        )}

                        {msg.sources?.map((src, i) => (
                            <div key={i} style={{ marginTop: 8 }}>
                                <Tag color='blue'>{src.pdf}</Tag>
                                <Tag color='purple'>{src.section_title}</Tag>
                                <Typography.Text type='secondary'>
                                    {src.highlight}
                                </Typography.Text>
                                <br />
                                <Button
                                    type='link'
                                    size='small'
                                    onClick={() => openPdf(src.pdf)}
                                >
                                    📖 PDFを開く
                                </Button>
                            </div>
                        ))}
                    </Card>
                ))}
            </Content>

            {/* ✅ 新着メッセージバッジ */}
            {!isAtBottom && hasNewMessage && (
                <div
                    style={{
                        position: 'fixed',
                        bottom: 100,
                        left: '50%',
                        transform: 'translateX(-50%)',
                        background: '#1890ff',
                        color: 'white',
                        padding: '6px 16px',
                        borderRadius: 16,
                        cursor: 'pointer',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                        zIndex: 1000,
                    }}
                    onClick={() => {
                        contentRef.current?.scrollTo({
                            top: contentRef.current.scrollHeight,
                            behavior: 'smooth',
                        });
                        setHasNewMessage(false); // 表示を消す
                    }}
                >
                    ⬇ 新着メッセージ
                </div>
            )}

            {step >= 3 && (
                <Footer style={{ padding: 0 }}>
                    <div style={{ marginBottom: 8 }}>
                        <Select
                            placeholder='📁 PDFファイルを選択'
                            style={{ width: 200, marginRight: 16 }}
                            value={pdf}
                            onChange={setPdf}
                            allowClear
                        >
                            <Option value='doc1.pdf'>doc1.pdf</Option>
                            <Option value='doc2.pdf'>doc2.pdf</Option>
                        </Select>
                        <Typography.Text strong style={{ marginRight: 12 }}>
                            カテゴリ: {category}
                        </Typography.Text>
                        <Button
                            size='small'
                            onClick={handleCategoryChangeRequest}
                        >
                            カテゴリを変更
                        </Button>
                    </div>
                    <Space.Compact style={{ width: '100%' }}>
                        <TextArea
                            rows={2}
                            style={{ width: 'calc(100% - 100px)' }}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder='質問を入力...'
                            onPressEnter={(e) => {
                                if (!e.shiftKey) {
                                    e.preventDefault();
                                    handleSend();
                                }
                            }}
                        />
                        <Button
                            type='primary'
                            loading={loading}
                            onClick={handleSend}
                            style={{ width: 100 }}
                        >
                            送信
                        </Button>
                    </Space.Compact>
                </Footer>
            )}

            <Modal
                open={pdfModalVisible}
                onCancel={() => setPdfModalVisible(false)}
                footer={null}
                title='📖 PDFプレビュー'
                width='80%'
                styles={{
                    body: {
                        height: '80vh',
                        padding: 0,
                        overflow: 'hidden',
                    },
                }}
            >
                {pdfToShow ? (
                    <iframe
                        key={pdfToShow}
                        title='PDF Preview'
                        src={pdfToShow}
                        width='100%'
                        height='100%'
                        style={{ border: 'none', display: 'block' }}
                    />
                ) : (
                    <Empty description='PDFが読み込まれていません' />
                )}
            </Modal>
        </Layout>
    );
};

export default PdfChatBot;
