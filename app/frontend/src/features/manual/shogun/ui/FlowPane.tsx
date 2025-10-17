/**
 * FlowPane UI Component
 * フローチャート表示（純粋UI）
 */
import React from 'react';
import { Empty } from 'antd';

export interface FlowPaneProps {
  src?: string;
  title: string;
  frameClassName?: string;
  imgClassName?: string;
}

export const FlowPane: React.FC<FlowPaneProps> = ({ src, title, frameClassName, imgClassName }) => {
  if (!src) {
    return (
      <div style={{ height: '100%' }}>
        <Empty description="フローチャート未設定" />
      </div>
    );
  }

  const lower = src.toLowerCase();
  if (lower.endsWith('.pdf')) {
    return <iframe title={`${title}-flow`} src={src} className={frameClassName} />;
  }
  if (/\.(png|jpg|jpeg|svg|webp)$/.test(lower)) {
    return <img src={src} alt={`${title}-flow`} className={imgClassName} />;
  }
  return <iframe title={`${title}-flow`} src={src} className={frameClassName} />;
};
