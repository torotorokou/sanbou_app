import React, { useState } from 'react';
import { Typography, Modal, Button } from 'antd';
import { useResponsive, customTokens } from '@/shared';
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
    const { isMobile } = useResponsive();
    const [modalOpen, setModalOpen] = useState(false);

    // 親の高さいっぱいにフィットさせる（モーダルはビューポートに合わせて表示）

    const previewAreaStyle = {
        flex: 1,
        height: '100%',
        width: '100%',
        maxWidth: '100%',
        border: `1px solid ${customTokens.colorBorder}`,
        borderRadius: 8,
        boxShadow: `0 2px 8px ${customTokens.shadowLight}`,
        background: customTokens.colorBgCard,
        overflow: 'hidden',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        boxSizing: 'border-box' as const,
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            width: '100%',
            maxWidth: '100%',
            minHeight: 0,
            minWidth: 0,
            gap: 8,
            overflow: 'hidden',
            boxSizing: 'border-box' as const,
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

            <div style={previewAreaStyle}>
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
                styles={{ body: { padding: 12 } }}
                style={{ top: 20 }}
            >
                <div style={{ width: '100%', height: `calc(100vh - 160px)`, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    {React.isValidElement(children) ? (
                        React.cloneElement(children, { height: '100%' })
                    ) : (
                        children
                    )}
                </div>
            </Modal>
        </div>
    );
};

export default PreviewSection;
