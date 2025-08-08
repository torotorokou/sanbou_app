import React from 'react';
import { Button } from 'antd';
import { useDeviceType } from '../../hooks/ui/useResponsive';

type VerticalActionButtonProps = {
    icon: React.ReactNode;
    text: string;
    onClick?: () => void;
    disabled?: boolean;
    backgroundColor?: string;
    href?: string; // ✅ ダウンロード用のリンク先（あれば <a> に変換）
    download?: boolean; // ✅ <a download> 属性指定用
};

const VerticalActionButton: React.FC<VerticalActionButtonProps> = ({
    icon,
    text,
    onClick,
    disabled = false,
    backgroundColor = '#10b981',
    href,
    download = false,
}) => {
    const { isMobileOrTablet, isMobile } = useDeviceType();

    const baseStyle: React.CSSProperties = {
        writingMode: isMobileOrTablet ? 'horizontal-tb' : 'vertical-rl',
        textOrientation: isMobileOrTablet ? 'mixed' : 'mixed',
        height: isMobile ? 48 : isMobileOrTablet ? 56 : 160,
        width: isMobileOrTablet ? '100%' : 'auto',
        minWidth: isMobileOrTablet ? 120 : 'auto',
        fontSize: isMobile ? '0.9rem' : isMobileOrTablet ? '1rem' : '1.2rem',
        fontWeight: 600,
        borderRadius: isMobileOrTablet ? '12px' : '24px',
        border: 'none',
        transition: 'all 0.3s ease',
        transform: 'scale(1)',
        color: '#fff',
        cursor: disabled ? 'not-allowed' : 'pointer',
        backgroundColor: disabled ? '#ccc' : backgroundColor,
        boxShadow: disabled ? 'none' : '0 4px 10px rgba(0, 0, 0, 0.1)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        textDecoration: 'none',
        flexDirection: 'row',
        gap: 8,
    };

    const button = (
        <Button
            icon={icon}
            type='primary'
            size='large'
            shape='round'
            disabled={disabled}
            onClick={href ? undefined : onClick}
            style={baseStyle}
            onMouseEnter={(e) => {
                if (!disabled) {
                    e.currentTarget.style.transform = 'scale(1.05)';
                    e.currentTarget.style.boxShadow =
                        '0 6px 14px rgba(0, 0, 0, 0.2)';
                }
            }}
            onMouseLeave={(e) => {
                if (!disabled) {
                    e.currentTarget.style.transform = 'scale(1)';
                    e.currentTarget.style.boxShadow =
                        '0 4px 10px rgba(0, 0, 0, 0.1)';
                }
            }}
        >
            {text}
        </Button>
    );

    return href ? (
        <a href={href} download={download} style={{ textDecoration: 'none' }}>
            {button}
        </a>
    ) : (
        button
    );
};

export default VerticalActionButton;
