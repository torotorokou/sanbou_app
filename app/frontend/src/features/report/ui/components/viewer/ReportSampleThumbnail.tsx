import React, { useState } from 'react';
import { Modal } from 'antd';
import { useResponsive } from '@/shared';

type Props = {
    url: string;
    width?: string;
    height?: string;
};

/**
 * レポートサンプルサムネイルコンポーネント - useResponsive(flags)統合版
 * 
 * 🔄 リファクタリング内容：
 * - window.innerWidth/innerHeight直参照を全廃
 * - useResponsive(width, height, flags)で画面サイズを取得
 * - モーダルサイズを段階的に決定（4段階レスポンシブ）
 */

const ReportSampleThumbnail: React.FC<Props> = ({
    url,
    width = '100%',
    height = '160px',
}) => {
    const [visible, setVisible] = useState(false);
    const [imgSize, setImgSize] = useState({ width: 0, height: 0 });

    // responsive: flagsベースの段階スイッチ
    const { width: viewportWidth, height: viewportHeight, flags } = useResponsive();

    // 実画像サイズ取得
    const handleImageLoad = (
        e: React.SyntheticEvent<HTMLImageElement, Event>
    ) => {
        const { naturalWidth, naturalHeight } = e.currentTarget;
        setImgSize({ width: naturalWidth, height: naturalHeight });
    };

    // responsive: 段階的な値決定（Mobile→Tablet→Laptop→Desktop）
    const pickByDevice = <T,>(mobile: T, tablet: T, laptop: T, desktop: T): T => {
        if (flags.isMobile) return mobile;
        if (flags.isTablet) return tablet;
        if (flags.isLaptop) return laptop;
        return desktop; // isDesktop
    };

    // responsive: モーダルの最大サイズ率（画面比）
    const modalHeightRatio = pickByDevice(0.85, 0.88, 0.90, 0.90);
    const modalWidthRatio = pickByDevice(0.90, 0.92, 0.95, 0.95);

    // モーダルの最大サイズ
    const MAX_MODAL_HEIGHT = Math.floor(viewportHeight * modalHeightRatio);
    const MAX_MODAL_WIDTH = Math.floor(viewportWidth * modalWidthRatio);

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
                styles={{
                    body: {
                        padding: 0,
                        margin: 0,
                        background: '#fff',
                        height: displayHeight,
                        overflow: 'hidden',
                        position: 'relative',
                        boxShadow: '0 4px 24px rgba(0,0,0,0.10)',
                    }
                }}
                maskClosable
                destroyOnHidden
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
