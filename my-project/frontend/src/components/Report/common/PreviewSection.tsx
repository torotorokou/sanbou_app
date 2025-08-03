import React from 'react';
import { Typography } from 'antd';

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
  const previewAreaStyle = {
    flex: 1,
    height: '100%',
    minHeight: '500px',
    border: '1px solid #ccc',
    borderRadius: 8,
    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
    background: '#fafafa',
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
