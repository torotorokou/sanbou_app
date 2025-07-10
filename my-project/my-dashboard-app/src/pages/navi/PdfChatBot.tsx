import React, { useState, useEffect, useRef } from 'react';
import {
    Layout,
    Input,
    Button,
    Typography,
    Card,
    Tag,
    Modal,
    Empty,
    Select,
    Space,
} from 'antd';
import axios from 'axios';
import TypewriterText from '@/components/ui/TypewriterText';
import type { ChatMessage } from '@/types/chat';

const { Content, Footer } = Layout;
const { TextArea } = Input;
const { Option } = Select;

const PdfChatBot: React.FC = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [category, setCategory] = useState('');
    const [input, setInput] = useState('');
    const [pdf, setPdf] = useState<string>();
    const [loading, setLoading] = useState(false);
    const [pdfToShow, setPdfToShow] = useState('');
    const [pdfModalVisible, setPdfModalVisible] = useState(false);
    const [isDisplaying, setIsDisplaying] = useState(false);
    const [windowWidth, setWindowWidth] = useState(window.innerWidth);

    const contentRef = useRef<HTMLDivElement>(null);
    const messageQueue = useRef<ChatMessage[]>([]);
    const didInit = useRef(false);

    // ✅ メッセージキュー処理
    const showNextMessage = () => {
        if (messageQueue.current.length === 0) {
            setIsDisplaying(false);
            return;
        }
        const next = messageQueue.current.shift()!;
        setMessages((prev) => [...prev, next]);
        setTimeout(showNextMessage, 1200);
    };

    const enqueueMessages = (msgs: ChatMessage[]) => {
        messageQueue.current.push(...msgs);
        if (!isDisplaying) {
            setIsDisplaying(true);
            showNextMessage();
        }
    };

    useEffect(() => {
        if (!didInit.current) {
            didInit.current = true;
            enqueueMessages([
                { role: 'bot', content: 'こんにちは！' },
                {
                    role: 'bot',
                    content:
                        '私は産業廃棄物の専門AIです。カテゴリを選んでください。',
                },
                { role: 'bot', content: '', type: 'category-buttons' },
            ]);
        }
    }, []);

    useEffect(() => {
        const handleResize = () => setWindowWidth(window.innerWidth);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const handleCategorySelect = (cat: string) => {
        setCategory(cat);
        enqueueMessages([
            {
                role: 'bot',
                content: `カテゴリ「${cat}」が選ばれました。質問をどうぞ。`,
            },
        ]);
    };

    const handleSend = async () => {
        if (!input.trim()) return;
        const userMessage: ChatMessage = { role: 'user', content: input };
        setMessages((prev) => [...prev, userMessage]);
        setLoading(true);
        try {
            const res = await axios.post('/api/chat', {
                query: input,
                tags: [category],
                pdf,
            });
            const botMessage: ChatMessage = {
                role: 'bot',
                content: res.data.answer,
                sources: res.data.sources || [],
            };
            enqueueMessages([botMessage]);
            setInput('');
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
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
        <Layout style={{ height: '100%', background: '#fff', padding: 24 }}>
            <Content
                ref={contentRef}
                style={{
                    overflowY: 'auto',
                    maxHeight: '70vh',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 8,
                    marginBottom: 16,
                }}
            >
                {messages.map((msg, idx) => (
                    <Card
                        key={idx}
                        size='small'
                        title={msg.role === 'user' ? '👤 あなた' : '🤖 AI'}
                        style={getCardStyle(msg.role)}
                    >
                        <Typography.Paragraph>
                            {msg.role === 'bot' &&
                            !msg.type &&
                            idx === messages.length - 1 &&
                            isDisplaying ? (
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

                        {msg.type === 'category-buttons' && (
                            <div>
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
                        カテゴリ: {category || '未選択'}
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
