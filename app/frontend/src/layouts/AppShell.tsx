import React from 'react';
import { Layout } from 'antd';
import Sidebar from '@/layout/Sidebar';

const { Header, Content } = Layout;

type Props = { children: React.ReactNode; header?: React.ReactNode };

const AppShell: React.FC<Props> = ({ children, header }) => {
  return (
    <Layout style={{ height: '100%', overflow: 'hidden' }}>
      {header && (
        <Header style={{ height: 'var(--header-height)', lineHeight: 'var(--header-height)' }}>
          {header}
        </Header>
      )}
      <Layout style={{ height: header ? `calc(100% - var(--header-height))` : '100%' }}>
        <Sidebar />
        <Content className="flex-col min-h-0" style={{ overflow: 'hidden' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppShell;
