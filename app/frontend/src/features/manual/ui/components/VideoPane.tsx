/**
 * VideoPane UI Component
 * 動画表示（純粋UI）
 */
import React from 'react';
import { Empty } from 'antd';

function toYouTubeEmbed(url: string): string {
  if (/youtube\.com\/watch\?v=/.test(url)) {
    const id = new URL(url).searchParams.get('v');
    return id ? `https://www.youtube.com/embed/${id}` : url;
  }
  const m = url.match(/youtu\.be\/([^?&]+)/);
  if (m?.[1]) return `https://www.youtube.com/embed/${m[1]}`;
  return url;
}

export interface VideoPaneProps {
  src?: string;
  title: string;
  frameClassName?: string;
  videoClassName?: string;
}

export const VideoPane: React.FC<VideoPaneProps> = ({ src, title, frameClassName, videoClassName }) => {
  if (!src) {
    return (
      <div style={{ height: '100%' }}>
        <Empty description="動画未設定" />
      </div>
    );
  }

  const lower = src.toLowerCase();
  const isMp4 = lower.endsWith('.mp4');
  const isYouTube = /youtube\.com|youtu\.be/.test(lower);

  if (isMp4) {
    return <video src={src} className={videoClassName} controls />;
  }

  if (isYouTube) {
    const embed = toYouTubeEmbed(src);
    return (
      <iframe
        title={`${title}-video`}
        src={embed}
        className={frameClassName}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    );
  }

  return <iframe title={`${title}-video`} src={src} className={frameClassName} />;
};
