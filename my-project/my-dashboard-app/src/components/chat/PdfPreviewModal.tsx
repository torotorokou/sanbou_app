// --- PdfChatBot.tsx ---
import React, { useState, useRef, useEffect } from 'react';
import { Layout, Select, Input, Button, Typography, Space } from 'antd';
import axios from 'axios';
import ChatMessageCard from '@/components/chat/ChatMessageCard';
import PdfPreviewModal from '@/components/chat/PdfPreviewModal';
import { useScrollTracker } from '@/hooks/useScrollTracker';
import type { ChatMessage } from '@/types/chat';

const { Content, Footer } = Layout;
const { Option } = Select;
const { TextArea } = Input;

// ✅ 遅延実行ユーティリティ
const delay = (ms: number) => new Promise((res) => setTimeout(res, ms));

const PdfChatBot: React.FC = () => {
    const [category, setCategory] = useState('');
    const [pdf, setPdf] = useState<string>();
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [pdfModalVisible, setPdfModalVisible] = useState(false);
    const [pdfToShow, setPdfToShow] = useState<string>('');
    const [windowWidth, setWindowWidth] = useState(window.innerWidth);

    const contentRef = useRef<HTMLDivElement>(null);
    const { isAtBottom, hasNewMessage } = useScrollTracker(contentRef, [
        messages,
    ]);

    useEffect(() => {
        const handleResize = () => setWindowWidth(window.innerWidth);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // ✅ 段階的に会話を表示する
    const handleStart = async () => {
        // ✅ まず最初の「こんにちは！」を追加
        setMessages([{ role: 'bot', content: 'こんにちは！' }]);
        await delay(1000);

        try {
            // ✅ intro取得してメッセージに追加
            const res = await axios.get('/api/intro');
            const introText =
                res.data?.text || 'イントロが取得できませんでした。';

            setMessages((prev) => [
                ...prev,
                { role: 'bot', content: introText },
            ]);

            await delay(1200);

            // ✅ 最後にカテゴリボタン表示（content: '' でもOK）
            setMessages((prev) => [
                ...prev,
                {
                    role: 'bot',
                    content: 'カテゴリを選んでください。',
                    type: 'category-buttons',
                },
            ]);
        } catch (err) {
            console.error('❌ intro取得失敗:', err);
            setMessages((prev) => [
                ...prev,
                { role: 'bot', content: '説明の取得に失敗しました。' },
            ]);
        }
    };

    const handleCategorySelect = (cat: string) => {
        setCategory(cat);
        setMessages((prev) => [
            ...prev,
            {
                role: 'bot',
                content: `カテゴリ「${cat}」が選択されました。質問を入力してください。`,
            },
        ]);
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

    const openPdf = (pdfName?: string) => {
        if (!pdfName) return;
        setPdfToShow(`/pdf/${pdfName}`);
        setPdfModalVisible(true);
    };

    const shouldShowFooter =
        category !== '' && !messages.some((m) => m.type === 'category-buttons');

    return (
        <Layout style={{ padding: 24, background: '#fff', height: '100%' }}>
            <Content
                ref={contentRef}
                style={{
                    overflowY: 'auto',
                    maxHeight: '70vh',
                    marginBottom: 16,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 8,
                }}
            >
                {messages.length === 0 ? (
                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'center',
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
                ) : (
                    messages.map((msg, idx) => (
                        <ChatMessageCard
                            key={idx}
                            msg={msg}
                            index={idx}
                            windowWidth={windowWidth}
                            isLastBotMessage={
                                idx === messages.length - 1 &&
                                msg.role === 'bot' &&
                                !msg.type
                            }
                            onSelectCategory={handleCategorySelect}
                            onOpenPdf={openPdf}
                        />
                    ))
                )}
            </Content>

            {shouldShowFooter && (
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

            <PdfPreviewModal
                visible={pdfModalVisible}
                onClose={() => setPdfModalVisible(false)}
                pdfUrl={pdfToShow}
            />
        </Layout>
    );
};

export default PdfChatBot;
