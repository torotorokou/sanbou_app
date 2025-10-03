import React, { useState } from 'react';
import { Typography, Modal, Button } from 'antd';
import { useWindowSize } from '@shared/hooks/ui';
import { customTokens } from '@/theme';
import { ExpandOutlined } from '@ant-design/icons';

interface PreviewSectionProps {
    title?: string;
    children?: React.ReactNode;
}

/**
 * プレビュー表示セクション
 * プレビューエリアのレイアウトを管理
 */
const PreviewSection: React.FC<PreviewSectionProps> = ({
    title = '📄 プレビュー画面',
    children
}) => {
    const { isMobile, isTablet } = useWindowSize();
    const [modalOpen, setModalOpen] = useState(false);

    // 親の高さいっぱいにフィットさせる（モーダルのみやや拡大）
    const BASE_HEIGHT = isMobile ? 320 : isTablet ? 420 : 520;
    const MODAL_HEIGHT_SCALE = 1.3;
    const modalMinHeight = Math.round(BASE_HEIGHT * MODAL_HEIGHT_SCALE);

    const previewAreaStyle = {
        flex: 1,
        height: '100%',
        width: '100%',
        border: `1px solid ${customTokens.colorBorder}`,
        borderRadius: 8,
        boxShadow: `0 2px 8px ${customTokens.shadowLight}`,
        background: customTokens.colorBgCard,
        overflow: 'hidden',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            width: '100%',
            minHeight: 0,
            gap: 8
        }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography.Title level={4} style={{ marginBottom: 0 }}>
                    {title}
                </Typography.Title>
                <div>
                    <Button
                        type='text'
                        icon={<ExpandOutlined />}
                        onClick={() => setModalOpen(true)}
                        aria-label='プレビューを拡大'
                    />
                </div>
            </div>

            <div style={previewAreaStyle} onClick={() => setModalOpen(true)}>
                {React.isValidElement(children) ? (
                    React.cloneElement(children, { height: '100%' })
                ) : (
                    children || (
                        <Typography.Text type='secondary'>
                            帳簿を作成するとここに表示されます。
                        </Typography.Text>
                    )
                )}
            </div>

            <Modal
                open={modalOpen}
                onCancel={() => setModalOpen(false)}
                footer={null}
                width={isMobile ? '95%' : '80%'}
                centered
                bodyStyle={{ padding: 12, minHeight: modalMinHeight }}
            >
                <div style={{ width: '100%', height: '100%', minHeight: modalMinHeight }}>
                    {React.isValidElement(children) ? (
                        React.cloneElement(children, { height: `${modalMinHeight}px` })
                    ) : (
                        children
                    )}
                </div>
            </Modal>
        </div>
    );
};

export default PreviewSection;
