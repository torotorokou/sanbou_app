import React, { useState } from 'react';
import {
    Layout,
    Select,
    Input,
    Button,
    List,
    Typography,
    Card,
    Tag,
    Modal,
    Empty,
    Space,
} from 'antd';
import axios from 'axios';
import type { ChatMessage } from '@/types/chat';

const { Header, Content, Footer } = Layout;
const { Option } = Select;
const { TextArea } = Input;

const PdfChatBot: React.FC = () => {
    const [pdf, setPdf] = useState<string>();
    const [tags, setTags] = useState<string[]>([]);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [pdfModalVisible, setPdfModalVisible] = useState(false);
    const [pdfToShow, setPdfToShow] = useState<string>('');

    const handleSend = async () => {
        if (!input.trim()) return;

        setLoading(true);
        const userMessage: ChatMessage = { role: 'user', content: input };
        setMessages((prev) => [...prev, userMessage]);

        const payload = {
            query: input,
            tags,
            pdf,
        };
        console.log('📤 axios送信前 payload:', payload);

        try {
            const res = await axios.post('/api/chat', payload);
            console.log('✅ axios応答:', res.data);

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
            console.error('📦 詳細:', err?.response?.data || err);
        } finally {
            setLoading(false);
        }
    };

    const openPdf = (pdfName?: string) => {
        if (!pdfName) return;
        const url = `/pdf/${pdfName}`;
        console.log('PDF表示URL:', url);
        setPdfToShow(url);
        setPdfModalVisible(true);
    };

    return (
        <Layout style={{ padding: 24, background: '#fff', height: '100%' }}>
            <Header
                style={{
                    background: 'transparent',
                    padding: 0,
                    marginBottom: 16,
                }}
            >
                <div style={{ display: 'flex', gap: 12 }}>
                    <Select
                        placeholder='📁 PDFファイルを選択'
                        style={{ width: 200 }}
                        value={pdf}
                        onChange={setPdf}
                        allowClear
                    >
                        <Option value='doc1.pdf'>doc1.pdf</Option>
                        <Option value='doc2.pdf'>doc2.pdf</Option>
                    </Select>

                    <Select
                        mode='multiple'
                        placeholder='🏷 タグを選択'
                        style={{ width: 300 }}
                        value={tags}
                        onChange={setTags}
                        allowClear
                    >
                        <Option value='RPF'>RPF</Option>
                        <Option value='廃プラ'>廃プラ</Option>
                        <Option value='セメント'>セメント</Option>
                    </Select>
                </div>
            </Header>

            <Content
                style={{
                    overflowY: 'auto',
                    maxHeight: '70vh',
                    marginBottom: 16,
                }}
            >
                <List
                    dataSource={messages}
                    renderItem={(msg, idx) => (
                        <Card
                            key={idx}
                            size='small'
                            style={{
                                marginBottom: 8,
                                background:
                                    msg.role === 'user' ? '#f6ffed' : '#e6f7ff',
                            }}
                            title={msg.role === 'user' ? '👤 あなた' : '🤖 AI'}
                        >
                            <Typography.Paragraph>
                                {msg.content}
                            </Typography.Paragraph>

                            {msg.sources?.map((src, i) => (
                                <div key={i} style={{ marginTop: 8 }}>
                                    <Tag color='blue'>{src.pdf}</Tag>
                                    <Tag color='purple'>
                                        {src.section_title}
                                    </Tag>
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
                    )}
                />
            </Content>

            <Footer style={{ padding: 0 }}>
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
                        padding: 0, // ✅ ← これが特に重要（iframeがつぶれるのを防ぐ）
                        overflow: 'hidden', // ✅ ← iframeがはみ出さないように
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
                        style={{
                            border: 'none',
                            display: 'block', // ✅ Safari対応などでも有効
                        }}
                    />
                ) : (
                    <Empty description='PDFが読み込まれていません' />
                )}
            </Modal>
        </Layout>
    );
};

export default PdfChatBot;
