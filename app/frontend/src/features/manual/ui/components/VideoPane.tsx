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

export interface VideoPaneRef {
  stopVideo: () => void;
}

export const VideoPane = React.forwardRef<VideoPaneRef, VideoPaneProps>(({ src, title, frameClassName, videoClassName }, ref) => {
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const iframeRef = React.useRef<HTMLIFrameElement>(null);

  React.useImperativeHandle(ref, () => ({
    stopVideo: () => {
      // MP4動画の停止
      if (videoRef.current) {
        videoRef.current.pause();
      }
      // YouTube/iframe動画の停止(srcを再設定してリロード)
      if (iframeRef.current && iframeRef.current.src) {
        const currentSrc = iframeRef.current.src;
        iframeRef.current.src = '';
        iframeRef.current.src = currentSrc;
      }
    },
  }));

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
    return <video ref={videoRef} src={src} className={videoClassName} controls />;
  }

  if (isYouTube) {
    const embed = toYouTubeEmbed(src);
    return (
      <iframe
        ref={iframeRef}
        title={`${title}-video`}
        src={embed}
        className={frameClassName}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    );
  }

  return <iframe ref={iframeRef} title={`${title}-video`} src={src} className={frameClassName} />;
});

VideoPane.displayName = 'VideoPane';
