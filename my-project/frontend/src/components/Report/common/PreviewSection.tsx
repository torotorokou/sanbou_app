import React from 'react';
import { Typography } from 'antd';
import { useDeviceType } from '../../../hooks/ui';
import { customTokens } from '../../../theme';

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
    const { isMobile, isTablet } = useDeviceType();

    const previewAreaStyle = {
        flex: 1,
        height: '100%',
        minHeight: isMobile ? '350px' : isTablet ? '450px' : '500px',
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
            gap: 8
        }}>
            <Typography.Title level={4} style={{ marginBottom: 0 }}>
                {title}
            </Typography.Title>
            <div style={previewAreaStyle}>
                {children || (
                    <Typography.Text type='secondary'>
                        帳簿を作成するとここに表示されます。
                    </Typography.Text>
                )}
            </div>
        </div>
    );
};

export default PreviewSection;
