// src/components/Report/viewer/ReportSampleThumbnail.tsx

import React, { useState } from 'react';
import { Modal, Button, Space } from 'antd';
import { Document, Page, pdfjs } from 'react-pdf';

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

type Props = {
    url: string;
    type: 'image' | 'pdf';
    width?: string;
    height?: string;
};

const ReportSampleThumbnail: React.FC<Props> = ({
    url,
    type,
    width = '100%',
    height = '160px',
}) => {
    const [visible, setVisible] = useState(false);
    const [zoom, setZoom] = useState(1.0);

    const handleZoomIn = () => setZoom((z) => Math.min(3, z + 0.1));
    const handleZoomOut = () => setZoom((z) => Math.max(0.5, z - 0.1));
    const resetZoom = () => setZoom(1.0);

    return (
        <>
            <div
                onClick={() => setVisible(true)}
                style={{
                    width,
                    height,
                    overflowY: 'auto',
                    overflowX: 'hidden',
                    borderRadius: 4,
                    background: '#f9f9f9',
                    border: '1px solid #ddd',
                    cursor: 'pointer',
                }}
            >
                {type === 'image' ? (
                    <img
                        src={url}
                        alt='帳票サンプル'
                        style={{
                            width: '100%',
                            height: 'auto',
                            objectFit: 'cover',
                            objectPosition: 'top',
                            display: 'block',
                        }}
                    />
                ) : (
                    <Document file={url}>
                        <Page pageNumber={1} width={300} />
                    </Document>
                )}
            </div>

            <Modal
                open={visible}
                onCancel={() => {
                    setVisible(false);
                    resetZoom();
                }}
                footer={null}
                width={640} // ✅ 固定幅に変更（これで横長にならない）
                style={{ top: 40 }}
                bodyStyle={{
                    padding: 0,
                    margin: 0,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '80vh',
                    overflow: 'auto', // ✅ 拡大時にスクロール可能に
                    position: 'relative',
                    background: '#fff',
                }}
            >
                {/* ズームボタン */}
                <div
                    style={{
                        position: 'absolute',
                        top: 16,
                        right: 16,
                        zIndex: 10,
                    }}
                >
                    <Space>
                        <Button size='small' onClick={handleZoomOut}>
                            －
                        </Button>
                        <Button size='small' onClick={handleZoomIn}>
                            ＋
                        </Button>
                        <Button size='small' onClick={resetZoom}>
                            リセット
                        </Button>
                    </Space>
                </div>

                {/* 表示本体 */}
                <div
                    style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        width: '100%',
                        overflow: 'auto',
                    }}
                >
                    {type === 'image' ? (
                        <img
                            src={url}
                            alt='拡大帳票'
                            style={{
                                height: `${80 * zoom}vh`,
                                width: 'auto',
                                objectFit: 'contain',
                            }}
                        />
                    ) : (
                        <Document
                            file={url}
                            onLoadError={(err) =>
                                console.error('PDF読み込みエラー:', err.message)
                            }
                        >
                            <Page
                                pageNumber={1}
                                width={600 * zoom} // ✅ 幅を明示的に
                            />
                        </Document>
                    )}
                </div>
            </Modal>
        </>
    );
};

export default ReportSampleThumbnail;
