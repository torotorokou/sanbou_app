/**
 * ManualViewer Component
 * PDFドキュメントビューア
 */

import React, { memo } from 'react';

interface ManualViewerProps {
  src: string;
  title?: string;
  className?: string;
}

export const ManualViewer = memo(({ src, title = 'マニュアル', className = '' }: ManualViewerProps) => {
  return (
    <div className={`manual-viewer ${className}`}>
      <iframe
        src={src}
        title={title}
        className="w-full h-full border-0"
        style={{ minHeight: '600px' }}
      />
    </div>
  );
});

ManualViewer.displayName = 'ManualViewer';
