import React from 'react';
import { Card } from 'antd';
import { useDeviceType } from '../../hooks/ui/useResponsive';

/**
 * レスポンシブデバッグ情報表示コンポーネント
 * 開発時にブレークポイントの動作を確認するため
 */
const ResponsiveDebugInfo: React.FC = () => {
    const deviceInfo = useDeviceType();

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
                <div>画面幅: {window.innerWidth}px</div>
                <div>isMobile: {deviceInfo.isMobile ? '✅' : '❌'}</div>
                <div>isTablet: {deviceInfo.isTablet ? '✅' : '❌'}</div>
                <div>isSmallDesktop: {deviceInfo.isSmallDesktop ? '✅' : '❌'}</div>
                <div>isMediumDesktop: {deviceInfo.isMediumDesktop ? '✅' : '❌'}</div>
                <div>isLargeDesktop: {deviceInfo.isLargeDesktop ? '✅' : '❌'}</div>
                <div>isMobileOrTablet: {deviceInfo.isMobileOrTablet ? '✅' : '❌'}</div>
            </div>
        </Card>
    );
};

export default ResponsiveDebugInfo;
