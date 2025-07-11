import React, { useState, useRef, useEffect } from 'react';
import { Modal, Button, Space } from 'antd';

type Props = {
    url: string;
    width?: string;
    height?: string;
};

const ReportSampleThumbnail: React.FC<Props> = ({
    url,
    width = '100%',
    height = '160px',
}) => {
    const [visible, setVisible] = useState(false);
    const [zoom, setZoom] = useState(1.0);
    const [isZoomed, setIsZoomed] = useState(false);

    // 画像の実サイズ
    const [imgSize, setImgSize] = useState({ width: 0, height: 0 });

    const containerRef = useRef<HTMLDivElement | null>(null);
    const isDragging = useRef(false);
    const startPos = useRef({ x: 0, y: 0 });
    const scrollPos = useRef({ left: 0, top: 0 });

    // 画像ロード時
    const handleImageLoad = (
        e: React.SyntheticEvent<HTMLImageElement, Event>
    ) => {
        const { naturalWidth, naturalHeight } = e.currentTarget;
        setImgSize({ width: naturalWidth, height: naturalHeight });
    };

    // パン操作
    const handleMouseDown = (e: React.MouseEvent) => {
        if (!containerRef.current || !isZoomed) return;
        isDragging.current = true;
        startPos.current = { x: e.clientX, y: e.clientY };
        scrollPos.current = {
            left: containerRef.current.scrollLeft,
            top: containerRef.current.scrollTop,
        };
        containerRef.current.style.cursor = 'grabbing';
    };
    const handleMouseMove = (e: React.MouseEvent) => {
        if (!isDragging.current || !containerRef.current) return;
        const dx = e.clientX - startPos.current.x;
        const dy = e.clientY - startPos.current.y;
        containerRef.current.scrollLeft = scrollPos.current.left - dx;
        containerRef.current.scrollTop = scrollPos.current.top - dy;
    };
    const handleMouseUp = () => {
        isDragging.current = false;
        if (containerRef.current && isZoomed) {
            containerRef.current.style.cursor = 'grab';
        }
    };

    // ズーム
    const handleZoomIn = () => {
        setZoom((z) => {
            const newZoom = Math.min(3, z + 0.1);
            setIsZoomed(newZoom !== 1.0);
            return newZoom;
        });
    };
    const handleZoomOut = () => {
        setZoom((z) => {
            const newZoom = Math.max(0.5, z - 0.1);
            setIsZoomed(newZoom !== 1.0);
            return newZoom;
        });
    };
    const resetZoom = () => {
        setZoom(1.0);
        setIsZoomed(false);
    };

    useEffect(() => {
        if (containerRef.current && !isZoomed) {
            containerRef.current.scrollLeft = 0;
            containerRef.current.scrollTop = 0;
        }
    }, [zoom, isZoomed]);

    // 画面サイズ
    const MODAL_MARGIN = 48;
    const VIEWPORT_W = typeof window !== 'undefined' ? window.innerWidth : 1024;
    const VIEWPORT_H = typeof window !== 'undefined' ? window.innerHeight : 768;

    // 90%の最大高さ
    const MAX_MODAL_HEIGHT = Math.floor(VIEWPORT_H * 0.9);
    // 90%の最大幅
    const MAX_MODAL_WIDTH = Math.floor(VIEWPORT_W * 0.95);

    // ズーム反映後の画像サイズ
    let displayWidth = imgSize.width * zoom;
    let displayHeight = imgSize.height * zoom;

    // 高さが90%超える場合は縮小して比率維持
    if (displayHeight > MAX_MODAL_HEIGHT) {
        const scale = MAX_MODAL_HEIGHT / displayHeight;
        displayHeight = MAX_MODAL_HEIGHT;
        displayWidth = displayWidth * scale;
    }
    // 幅が画面幅を超える場合も縮小
    if (displayWidth > MAX_MODAL_WIDTH) {
        const scale = MAX_MODAL_WIDTH / displayWidth;
        displayWidth = MAX_MODAL_WIDTH;
        displayHeight = displayHeight * scale;
    }

    return (
        <>
            {/* サムネイル */}
            <div
                onClick={() => setVisible(true)}
                style={{
                    width,
                    height,
                    overflow: 'hidden',
                    borderRadius: 4,
                    background: '#f9f9f9',
                    border: '1px solid #ddd',
                    cursor: 'pointer',
                }}
            >
                <img
                    src={url}
                    alt='帳票サンプル'
                    style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        objectPosition: 'top',
                        display: 'block',
                    }}
                />
            </div>

            {/* モーダル拡大表示 */}
            <Modal
                open={visible}
                onCancel={() => {
                    setVisible(false);
                    resetZoom();
                }}
                footer={null}
                centered
                width={displayWidth}
                style={{ top: 32, padding: 0 }}
                bodyStyle={{
                    padding: 0,
                    margin: 0,
                    background: '#fff',
                    height: displayHeight,
                    overflow: 'hidden',
                    position: 'relative',
                    boxShadow: '0 4px 24px rgba(0,0,0,0.10)',
                }}
                maskClosable
                destroyOnClose
            >
                {/* ズーム操作 */}
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

                {/* 拡大画像 */}
                <div
                    ref={containerRef}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                    style={{
                        width: displayWidth,
                        height: displayHeight,
                        overflow: isZoomed ? 'auto' : 'hidden',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        cursor: isZoomed ? 'grab' : 'default',
                        userSelect: 'none',
                        background: '#fff',
                    }}
                >
                    <img
                        src={url}
                        alt='拡大帳票'
                        style={{
                            width: displayWidth,
                            height: displayHeight,
                            objectFit: 'contain',
                            objectPosition: 'center',
                            transition: 'width 0.1s, height 0.1s',
                            display: 'block',
                            pointerEvents: 'none',
                        }}
                        onLoad={handleImageLoad}
                        draggable={false}
                    />
                </div>
            </Modal>
        </>
    );
};

export default ReportSampleThumbnail;
