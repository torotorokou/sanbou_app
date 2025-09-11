import React, { useState, useMemo } from 'react';
import {
    Layout,
    Input,
    Checkbox,
    Button,
    List,
    Typography,
    Tag,
    Pagination,
    Space,
    Modal,
} from 'antd';
import { Document, Page, pdfjs } from 'react-pdf';
import { customTokens } from '../theme';

// ✅ react-pdf@9.2.1 に対応した worker の指定方法
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    'pdfjs-dist/build/pdf.worker.min.mjs',
    import.meta.url
).toString();

const { Title, Text } = Typography;
const { Sider, Content } = Layout;

type Item = {
    key: string;
    pdf: string;
    title: string;
    category: string;
    content: string;
    updatedAt: string;
    relatedPages?: number[];
};

const pdfList = [
    'doc1.pdf',
    'manual2.pdf',
    'specs2024.pdf',
    '規程集.pdf',
    '重要通知.pdf',
];

const categories = ['技術', '総務', '現場'];

const mockData: Item[] = Array.from({ length: 20 }, (_, i) => ({
    key: `${i + 1}`,
    pdf: pdfList[i % pdfList.length],
    title: `マニュアルタイトル ${i + 1}`,
    category: categories[i % categories.length],
    content: `これはPDF「${pdfList[i % pdfList.length]
        }」に属するマニュアル本文テキストの例です。検索語「${i % 3 === 0 ? '重要' : i % 3 === 1 ? '注意' : '操作'
        }」が含まれています。`,
    updatedAt: `2025-07-${(i % 30) + 1}`.padStart(10, '0'),
    relatedPages: [1 + (i % 5), 3 + (i % 3)],
}));

const highlightText = (text: string, keyword: string) => {
    if (!keyword) return text;
    const regex = new RegExp(
        `(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`,
        'gi'
    );
    const parts = text.split(regex);
    return (
        <>
            {parts.map((part, i) =>
                regex.test(part) ? (
                    <span key={i} style={{ backgroundColor: customTokens.highlightYellow }}>
                        {part}
                    </span>
                ) : (
                    part
                )
            )}
        </>
    );
};

const PdfViewerModal: React.FC<{
    visible: boolean;
    pdfFile: string | null;
    onClose: () => void;
}> = ({ visible, pdfFile, onClose }) => {
    const [numPages, setNumPages] = useState<number>(0);

    const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
        setNumPages(numPages);
    };

    return (
        <Modal
            open={visible}
            onCancel={onClose}
            footer={null}
            width='80vw'
            style={{ top: 20 }}
            bodyStyle={{ overflowY: 'auto', height: '80vh' }}
            title={pdfFile}
            destroyOnClose
        >
            {pdfFile && (
                <Document
                    file={`/pdf/${pdfFile}`}
                    onLoadSuccess={onDocumentLoadSuccess}
                    loading='PDF読み込み中...'
                >
                    {Array.from(new Array(numPages), (el, index) => (
                        <Page
                            key={`page_${index + 1}`}
                            pageNumber={index + 1}
                        />
                    ))}
                </Document>
            )}
        </Modal>
    );
};

const ManualSearchWithSidebarAndFullPdf: React.FC = () => {
    const [selectedPdfs, setSelectedPdfs] = useState<string[]>([]);
    const [keyword, setKeyword] = useState('');
    const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [modalVisible, setModalVisible] = useState(false);
    const [modalPdf, setModalPdf] = useState<string | null>(null);
    const [modalPage, setModalPage] = useState(1);
    const [fullPdfVisible, setFullPdfVisible] = useState(false);
    const [fullPdfFile, setFullPdfFile] = useState<string | null>(null);

    const pageSize = 5;

    const onPdfChange = (checkedValues: Array<string | number>) => {
        setSelectedPdfs(checkedValues.map(String));
        setCurrentPage(1);
    };

    const onCategoryChange = (checkedValues: Array<string | number>) => {
        setSelectedCategories(checkedValues.map(String));
        setCurrentPage(1);
    };

    const filteredData = useMemo(() => {
        const kw = keyword.trim().toLowerCase();
        return mockData
            .filter((item) => {
                if (
                    selectedPdfs.length > 0 &&
                    !selectedPdfs.includes(item.pdf)
                ) {
                    return false;
                }
                if (
                    selectedCategories.length > 0 &&
                    !selectedCategories.includes(item.category)
                ) {
                    return false;
                }
                if (!kw) return true;
                return (
                    item.title.toLowerCase().includes(kw) ||
                    item.content.toLowerCase().includes(kw)
                );
            })
            .sort((a, b) => {
                const countA =
                    (a.title.match(new RegExp(kw, 'gi'))?.length || 0) +
                    (a.content.match(new RegExp(kw, 'gi'))?.length || 0);
                const countB =
                    (b.title.match(new RegExp(kw, 'gi'))?.length || 0) +
                    (b.content.match(new RegExp(kw, 'gi'))?.length || 0);
                return countB - countA;
            });
    }, [keyword, selectedPdfs, selectedCategories]);

    const pageData = filteredData.slice(
        (currentPage - 1) * pageSize,
        currentPage * pageSize
    );

    const openPageModal = (pdf: string, page: number) => {
        setModalPdf(pdf);
        setModalPage(page);
        setModalVisible(true);
    };

    const openFullPdfModal = (pdf: string) => {
        setFullPdfFile(pdf);
        setFullPdfVisible(true);
    };

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sider width={240} style={{ background: '#fff', padding: 16 }}>
                <Title level={4}>PDF選択</Title>
                <Checkbox.Group
                    options={pdfList}
                    value={selectedPdfs}
                    onChange={onPdfChange}
                    style={{ display: 'flex', flexDirection: 'column', gap: 8 }}
                />

                <Title level={4} style={{ marginTop: 24 }}>
                    カテゴリ絞り込み
                </Title>
                <Checkbox.Group
                    options={categories}
                    value={selectedCategories}
                    onChange={onCategoryChange}
                    style={{ display: 'flex', flexDirection: 'column', gap: 8 }}
                />
            </Sider>

            <Layout>
                <Content style={{ padding: 24 }}>
                    <Space
                        direction='vertical'
                        style={{ width: '100%' }}
                        size='middle'
                    >
                        <Input.Search
                            placeholder='キーワードを入力'
                            enterButton='検索'
                            value={keyword}
                            onChange={(e) => setKeyword(e.target.value)}
                            onSearch={() => setCurrentPage(1)}
                            allowClear
                            size='large'
                        />

                        <Text>検索結果: {filteredData.length} 件</Text>

                        <List
                            itemLayout='vertical'
                            size='large'
                            dataSource={pageData}
                            renderItem={(item) => (
                                <List.Item key={item.key}>
                                    <List.Item.Meta
                                        title={
                                            <>
                                                {highlightText(
                                                    item.title,
                                                    keyword
                                                )}{' '}
                                                <Tag
                                                    style={{
                                                        cursor: 'pointer',
                                                        textDecoration:
                                                            'underline',
                                                        color: customTokens.linkBlue,
                                                    }}
                                                    onClick={() =>
                                                        openFullPdfModal(
                                                            item.pdf
                                                        )
                                                    }
                                                >
                                                    {item.pdf}
                                                </Tag>{' '}
                                                <Tag>{item.category}</Tag>
                                            </>
                                        }
                                        description={
                                            <>
                                                <div>
                                                    {highlightText(
                                                        item.content,
                                                        keyword
                                                    )}
                                                </div>
                                                <div
                                                    style={{
                                                        marginTop: 8,
                                                        color: customTokens.colorTextMuted,
                                                    }}
                                                >
                                                    更新日: {item.updatedAt}
                                                </div>
                                                {item.relatedPages && (
                                                    <div
                                                        style={{ marginTop: 8 }}
                                                    >
                                                        関連ページ:{' '}
                                                        {item.relatedPages.map(
                                                            (p) => (
                                                                <Button
                                                                    key={`${item.key}-page-${p}`} // 重複しないkeyに修正
                                                                    size='small'
                                                                    onClick={() =>
                                                                        openPageModal(
                                                                            item.pdf,
                                                                            p
                                                                        )
                                                                    }
                                                                    style={{
                                                                        marginRight: 4,
                                                                    }}
                                                                >
                                                                    {p}
                                                                </Button>
                                                            )
                                                        )}
                                                    </div>
                                                )}
                                            </>
                                        }
                                    />
                                </List.Item>
                            )}
                        />

                        <Pagination
                            current={currentPage}
                            pageSize={pageSize}
                            total={filteredData.length}
                            onChange={(page) => setCurrentPage(page)}
                            style={{ textAlign: 'right' }}
                        />
                    </Space>
                </Content>
            </Layout>

            {/* 関連ページモーダル */}
            <Modal
                open={modalVisible}
                onCancel={() => setModalVisible(false)}
                footer={null}
                width={800}
                centered
                title={`${modalPdf} - ページ ${modalPage}`}
            >
                <div
                    style={{
                        minHeight: 360,
                        textAlign: 'center',
                        paddingTop: 40,
                        fontSize: 18,
                    }}
                >
                    {/* ここにPDF.jsでページレンダリングを実装 */}
                    <p>PDFビューアプレースホルダー</p>
                    <p>ファイル: {modalPdf}</p>
                    <p>ページ番号: {modalPage}</p>
                </div>
            </Modal>

            {/* フルPDF表示モーダル */}
            <PdfViewerModal
                visible={fullPdfVisible}
                pdfFile={fullPdfFile}
                onClose={() => setFullPdfVisible(false)}
            />
        </Layout>
    );
};

export default ManualSearchWithSidebarAndFullPdf;
