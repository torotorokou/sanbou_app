import React from 'react';
import { Button } from 'antd';

type VerticalActionButtonProps = {
    icon: React.ReactNode;
    text: string;
    onClick?: () => void;
    disabled?: boolean;
    backgroundColor?: string;
};

const VerticalActionButton: React.FC<VerticalActionButtonProps> = ({
    icon,
    text,
    onClick,
    disabled = false,
    backgroundColor = '#10b981',
}) => {
    return (
        <Button
            icon={icon}
            type='primary'
            size='large'
            shape='round'
            onClick={onClick}
            disabled={disabled}
            style={{
                writingMode: 'vertical-rl',
                textOrientation: 'mixed',
                height: 160,
                fontSize: '1.2rem',
                fontWeight: 600,
                backgroundColor,
                color: '#fff',
                border: 'none',
                borderRadius: '24px',
                boxShadow: '0 4px 10px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.3s ease',
                transform: 'scale(1)',
                cursor: disabled ? 'not-allowed' : 'pointer',
            }}
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
};

export default VerticalActionButton;
