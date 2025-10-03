import React from 'react';
import { Card } from 'antd';
import { useWindowSize } from '@shared/hooks/ui';

/**
 * レスポンシブデバッグ情報表示コンポーネント
 * 開発時にブレークポイントの動作を確認するため
 */
const ResponsiveDebugInfo: React.FC = () => {
    const { width, isMobile, isTablet, isDesktop } = useWindowSize();

    return (
        <Card
            size="small"
            title="🔍 レスポンシブデバッグ情報"
            style={{
                position: 'fixed',
                top: 10,
                right: 10,
                zIndex: 9999,
                minWidth: 200,
                fontSize: '12px'
            }}
        >
            <div style={{ fontSize: '11px', lineHeight: 1.4 }}>
                <div>画面幅: {width}px</div>
                <div>isMobile: {isMobile ? '✅' : '❌'}</div>
                <div>isTablet: {isTablet ? '✅' : '❌'}</div>
                <div>isDesktop: {isDesktop ? '✅' : '❌'}</div>
                <div>isMobileOrTablet: {isMobile || isTablet ? '✅' : '❌'}</div>
            </div>
        </Card>
    );
};

export default ResponsiveDebugInfo;
