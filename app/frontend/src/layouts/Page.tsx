import React from 'react';

type Props = {
  header?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
};

const Page: React.FC<Props> = ({ header, footer, children, className, style }) => {
  return (
    <div className={`flex-col min-h-0 ${className ?? ''}`} style={{ height: '100%', overflow: 'hidden', ...style }}>
      {header && (
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>{header}</div>
      )}
      <div className="min-h-0 overflow-auto p-content">
        {children}
      </div>
      {footer && (
        <div style={{ padding: '8px 16px', borderTop: '1px solid #f0f0f0' }}>{footer}</div>
      )}
    </div>
  );
};

export default Page;
