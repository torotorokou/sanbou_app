import React, { useState } from 'react';
import { Modal } from 'antd';
import { ANT } from '@/shared/constants/breakpoints';

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
    const [imgSize, setImgSize] = useState({ width: 0, height: 0 });

    // 実画像サイズ取得
    const handleImageLoad = (
        e: React.SyntheticEvent<HTMLImageElement, Event>
    ) => {
        const { naturalWidth, naturalHeight } = e.currentTarget;
        setImgSize({ width: naturalWidth, height: naturalHeight });
    };

    // 画面サイズ
    const VIEWPORT_W = typeof window !== 'undefined' ? window.innerWidth : 1024; // 1024 は一般的なタブレット横幅
    const VIEWPORT_H = typeof window !== 'undefined' ? window.innerHeight : ANT.md;

    // モーダルの最大サイズ
    const MAX_MODAL_HEIGHT = Math.floor(VIEWPORT_H * 0.9);
    const MAX_MODAL_WIDTH = Math.floor(VIEWPORT_W * 0.95);

    // 画像サイズ（画面内最大になるよう調整）
    let displayWidth = imgSize.width;
    let displayHeight = imgSize.height;
    if (displayHeight > MAX_MODAL_HEIGHT) {
        const scale = MAX_MODAL_HEIGHT / displayHeight;
        displayHeight = MAX_MODAL_HEIGHT;
        displayWidth = displayWidth * scale;
    }
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

            {/* モーダルプレビュー */}
            <Modal
                open={visible}
                onCancel={() => setVisible(false)}
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
                <div
                    style={{
                        width: displayWidth,
                        height: displayHeight,
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
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
                            display: 'block',
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
