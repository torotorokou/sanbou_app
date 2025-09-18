import React from 'react';
import { Layout } from 'antd';
import Sidebar from '@/layouts/Sidebar';

const { Header, Content } = Layout;

type Props = { children: React.ReactNode; header?: React.ReactNode };

const AppShell: React.FC<Props> = ({ children, header }) => {
  return (
    <Layout style={{ minHeight: '100dvh' }}>
      {header && (
        <Header style={{ height: 'var(--header-height)', lineHeight: 'var(--header-height)' }}>
          {header}
        </Header>
      )}
      <Layout style={{ height: header ? `calc(100% - var(--header-height))` : '100%', display: 'flex' }}>
        <Sidebar />
        {/* 副作用: Contentを単一スクロールに。二重スクロール解消・stickyが機能 */}
        <Content className="flex-col min-h-0" style={{ display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'auto' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppShell;
