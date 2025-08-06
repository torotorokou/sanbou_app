import React, { useState } from 'react';
import { Card, Typography } from 'antd';
import CsvUploadCard from './CsvUploadCard';
import type { CsvFileType } from './types';
import type { UploadProps } from 'antd';
import { customTokens } from '@/theme/tokens';
import { useDeviceType } from '@/hooks/ui/useResponsive';

type CsvUploadPanelProps = {
    upload: {
        files: CsvFileType[];
        makeUploadProps: (
            label: string,
            setter: (file: File) => void
        ) => UploadProps;
    };
};

const CsvUploadPanel: React.FC<CsvUploadPanelProps> = ({ upload }) => {
    const [hoveringIndex, setHoveringIndex] = useState<number | null>(null);
    const { isMobile, isTablet } = useDeviceType();

    // 最もシンプルな高さ計算：固定サイズ + 画面高さベースのスクロール制御
    const calculateHeight = () => {
        // 固定高さ（CSV数に関係なく）
        const fixedHeight = isMobile ? 320 : isTablet ? 380 : 450;

        // PC画面の高さによる動的スクロール制御
        if (typeof window !== 'undefined' && !isMobile && !isTablet) {
            const screenHeight = window.innerHeight;
            // 画面が小さい場合（800px以下）はスクロール有効
            const enableScroll = screenHeight <= 800;

            return {
                height: fixedHeight,
                overflowY: enableScroll ? 'auto' as const : 'hidden' as const,
            };
        }

        // モバイル・タブレットは常にスクロールなし
        return {
            height: fixedHeight,
            overflowY: 'hidden' as const,
        };
    };

    // カードの高さを統一（シンプルに）
    const getCardHeight = () => {
        // ファイル数に関係なく統一された高さ
        return isMobile ? 80 : isTablet ? 90 : 100;
    };

    const { height, overflowY } = calculateHeight();

    return (
        <Card
            size={isMobile ? 'small' : 'default'}
            bodyStyle={{
                padding: isMobile ? '12px' : isTablet ? '16px' : '20px', // bodyのパディングを最適化
            }}
            // title={
            //     <Typography.Title
            //         level={isMobile ? 5 : 4}
            //         style={{
            //             margin: 0,
            //             fontSize: isMobile ? '13px' : isTablet ? '15px' : '16px' // タイトルサイズを縮小
            //         }}
            //     >
            //         📂 CSVアップロード
            //     </Typography.Title>
            // }
            style={{
                borderRadius: isMobile ? 8 : 12,
                backgroundColor: customTokens.colorBgBase,
                width: '100%',
                // シンプルな高さ設定
                height: height,
                maxHeight: height,
                overflowY: overflowY,
            }}
        >
            <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: isMobile ? 8 : isTablet ? 10 : 12, // シンプルなgap
                padding: isMobile ? '8px 0' : isTablet ? '10px 0' : '12px 0', // シンプルなパディング
            }}>
                {upload.files.map((entry, index) => (
                    <CsvUploadCard
                        key={entry.label}
                        label={entry.label}
                        file={entry.file}
                        required={entry.required}
                        onChange={entry.onChange}
                        uploadProps={upload.makeUploadProps(
                            entry.label,
                            entry.onChange
                        )}
                        isHovering={hoveringIndex === index}
                        onHover={(hover) =>
                            setHoveringIndex(hover ? index : null)
                        }
                        validationResult={entry.validationResult ?? 'unknown'}
                        cardHeight={getCardHeight()} // 統一された高さを渡す
                    />
                ))}
            </div>
        </Card>
    );
};

export default CsvUploadPanel;
