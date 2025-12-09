/**
 * FlowPane UI Component
 * フローチャート表示（純粋UI）+ 遅延ロード対応
 */
import React from 'react';
import { Empty } from 'antd';

export interface FlowPaneProps {
  src?: string;
  title: string;
  frameClassName?: string;
  imgClassName?: string;
  lazy?: boolean; // 遅延ロードフラグ
}

export const FlowPane: React.FC<FlowPaneProps> = ({ src, title, frameClassName, imgClassName, lazy = false }) => {
  const [shouldLoad, setShouldLoad] = React.useState(!lazy);

  React.useEffect(() => {
    if (lazy && src) {
      // 遅延ロード：少し待ってからロード開始
      const timer = setTimeout(() => setShouldLoad(true), 50);
      return () => clearTimeout(timer);
    }
  }, [lazy, src]);

  if (!src) {
    return (
      <div style={{ height: '100%' }}>
        <Empty description="フローチャート未設定" />
      </div>
    );
  }

  if (!shouldLoad) {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
        <span style={{ color: '#999' }}>読み込み中...</span>
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
