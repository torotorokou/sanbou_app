import React, { useState } from 'react';
import { Card } from 'antd';
import CsvUploadCard from './CsvUploadCard';
import type { CsvFileType } from '../../../domain/types';
import type { UploadProps } from 'antd';
import { customTokens } from '@shared/theme/tokens';
import { useWindowSize } from '@shared/hooks/ui';

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
    const { isMobile, isTablet } = useWindowSize();

    // 画面サイズに応じたスクロール制御:
    // - vhベースでmaxHeightを設定し、overflowYは常に'auto'（必要時のみスクロールバー表示）
    // - これによりCSVの数に依存せず、画面が小さいほどスクロールが出やすくなる
    const panelMaxHeight = isMobile ? '55vh' : isTablet ? '60vh' : '65vh';

    // カードの高さを統一（デバイス別に最小限の差分）
    const getCardHeight = () => (isMobile ? 80 : isTablet ? 90 : 100);

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
                // 画面サイズに応じたmaxHeight、必要時のみスクロール
                maxHeight: panelMaxHeight,
                overflowY: 'auto',
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
                        validationResult={(entry.validationResult === 'ok' ? 'valid' : entry.validationResult === 'ng' ? 'invalid' : entry.validationResult) ?? 'unknown'}
                        cardHeight={getCardHeight()} // 統一された高さを渡す
                    />
                ))}
            </div>
        </Card>
    );
};

export default CsvUploadPanel;
