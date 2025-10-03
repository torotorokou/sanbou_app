import React, { useLayoutEffect, useRef, useState } from 'react';
import { Typography, Col, Row, Button, Modal, Spin, Tabs } from 'antd';
import { csvTypeColors } from '@shared/theme';

import {
    CsvUploadPanel,
    CsvPreviewCard,
    UploadInstructions,
    useCsvUploadHandler,
    useCsvUploadArea,
} from '@features/database';
import { UPLOAD_CSV_TYPES, UPLOAD_CSV_DEFINITIONS } from '@shared/constants/uploadCsvConfig';

const { Text } = Typography;
// Layout constants
const CARD_GAP = 16; // matches the column gap
const COLUMN_PADDING = 16; // matches the Col padding used below
const CARD_HEADER_HEIGHT = 48; // approximate Card header height (title area)
// Tabsバーの高さは実測に切替（初期値はフォールバック）
const TAB_BAR_HEIGHT_FALLBACK = 40;
const CARD_BODY_VERTICAL_PADDING = 8 * 2; // bodyStyle padding top+bottom

const UploadDatabasePage: React.FC = () => {
    const {
        files,
        validationResults,
        csvPreviews,
        canUpload,
        handleCsvFile,
        removeCsvFile,
    } = useCsvUploadArea();

    const { uploading, handleUpload } = useCsvUploadHandler(files);

    const panelFiles = UPLOAD_CSV_TYPES.map((type) => ({
        label: UPLOAD_CSV_DEFINITIONS[type].label,
        file: files[type],
        required: UPLOAD_CSV_DEFINITIONS[type].required,
        onChange: (f: File | null) => f && handleCsvFile(UPLOAD_CSV_DEFINITIONS[type].label, f),
        validationResult: (validationResults[type] === 'valid' ? 'ok' :
            validationResults[type] === 'invalid' ? 'ng' : 'unknown') as 'ok' | 'ng' | 'unknown',
        onRemove: () => removeCsvFile(type),
    }));

    // dynamic sizing based on Row height
    const rowRef = useRef<HTMLDivElement | null>(null);
    const tabsRef = useRef<HTMLDivElement | null>(null);
    const [cardHeight, setCardHeight] = useState<number>(300);
    const [tableBodyHeight, setTableBodyHeight] = useState<number>(200);
    const [tabBarHeight, setTabBarHeight] = useState<number>(TAB_BAR_HEIGHT_FALLBACK);

    useLayoutEffect(() => {
        const calc = () => {
            const rowEl = rowRef.current;
            if (!rowEl) return;
            const rowH = rowEl.clientHeight || (window.innerHeight || document.documentElement.clientHeight || 910);
            // Tabsバーの実高さを測定
            const tabEl = tabsRef.current?.querySelector('.ant-tabs-nav') as HTMLElement | null;
            const measuredTab = tabEl?.offsetHeight ?? TAB_BAR_HEIGHT_FALLBACK;
            if (measuredTab !== tabBarHeight) setTabBarHeight(measuredTab);
            // available space inside the column (subtract paddings)
            const bottomSafeSpace = 16;
            const avail = Math.max(400, Math.floor(rowH - (COLUMN_PADDING * 2) - bottomSafeSpace));
            // tabs: only one card visible at a time, account for tab bar height
            const ch = Math.max(160, Math.floor(avail - measuredTab));
            setCardHeight(ch);
            const tbh = Math.max(80, ch - CARD_HEADER_HEIGHT - CARD_BODY_VERTICAL_PADDING - 8);
            setTableBodyHeight(tbh);
        };
        // initial calc and on resize
        const raf = requestAnimationFrame(calc);
        const onResize = () => calc();
        window.addEventListener('resize', onResize);
        return () => {
            cancelAnimationFrame(raf);
            window.removeEventListener('resize', onResize);
        };
    }, []);

    // helper: choose readable text color (black/white) based on background
    const readableTextColor = (bg: string) => {
        try {
            const c = bg.replace('#', '');
            const r = parseInt(c.substring(0, 2), 16);
            const g = parseInt(c.substring(2, 4), 16);
            const b = parseInt(c.substring(4, 6), 16);
            // relative luminance approximate
            const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
            return luminance > 0.6 ? '#111827' : '#ffffff';
        } catch {
            return '#ffffff';
        }
    };

    return (
        <>
            {/* Contentのpaddingを差し引いた固定高: calc(100dvh - 2*--page-padding) */}
            <Row
                ref={rowRef}
                style={{
                    height: 'calc(100dvh - (var(--page-padding, 0px) * 2))',
                    minHeight: 600,
                    overflow: 'hidden',
                }}
            >
                <Col
                    span={8}
                    style={{
                        padding: 16,
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        overflow: 'hidden',
                    }}
                >
                    <UploadInstructions />

                    {/* 左カラムは内部だけスクロール許可 */}
                    <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', paddingRight: 4 }}>
                    <CsvUploadPanel
                        upload={{
                            files: panelFiles,
                            makeUploadProps: (label) => ({
                                accept: '.csv',
                                showUploadList: false,
                                beforeUpload: (file: File) => {
                                    handleCsvFile(label, file);
                                    return false;
                                },
                            }),
                        }}
                    />
                    </div>

                    <Button
                        type="primary"
                        disabled={!canUpload}
                        onClick={handleUpload}
                        style={{ marginTop: 24, width: '100%' }}
                    >
                        アップロードする
                    </Button>
                </Col>

                <Col
                    span={16}
                    style={{
                        padding: 16,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: CARD_GAP,
                        height: '100%',
                        // prevent outer vertical scrollbar; let inner table handle scrolling
                        overflow: 'hidden',
                    }}
                >
                    <Tabs
                        defaultActiveKey={UPLOAD_CSV_TYPES[0]}
                        style={{ height: '100%' }}
                        // refでラップしてタブバーの実高さを計測
                        renderTabBar={(props, DefaultTabBar) => (
                            <div ref={(el) => { tabsRef.current = el; }}>
                                <DefaultTabBar {...props} />
                            </div>
                        )}
                        items={UPLOAD_CSV_TYPES.map((type) => {
                            const bg = csvTypeColors[type as keyof typeof csvTypeColors] || '#777';
                            const fg = readableTextColor(bg);
                            return ({
                                key: type,
                                label: (
                                    <div
                                        style={{
                                            display: 'inline-block',
                                            padding: '4px 10px',
                                            borderRadius: 9999,
                                            background: bg,
                                            color: fg,
                                            fontWeight: 600,
                                            fontSize: 14,
                                        }}
                                    >
                                        {UPLOAD_CSV_DEFINITIONS[type].label}
                                    </div>
                                ),
                                children: (
                                    <div style={{ height: cardHeight, overflow: 'hidden' }}>
                                        <CsvPreviewCard
                                            type={type}
                                            csvPreview={csvPreviews[type]}
                                            validationResult={validationResults[type]}
                                            cardHeight={cardHeight}
                                            tableBodyHeight={tableBodyHeight}
                                            backgroundColor={bg}
                                        />
                                    </div>
                                ),
                            });
                        })}
                    />
                </Col>
            </Row>

            <Modal
                open={uploading}
                footer={null}
                closable={false}
                centered
                maskClosable={false}
                maskStyle={{ backdropFilter: 'blur(2px)' }}
            >
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                    <Spin size="large" tip="アップロード中です…" />
                    <div style={{ marginTop: 16 }}>
                        <Text type="secondary">CSVをアップロード中です。しばらくお待ちください。</Text>
                    </div>
                </div>
            </Modal>
        </>
    );
};

export default UploadDatabasePage;
