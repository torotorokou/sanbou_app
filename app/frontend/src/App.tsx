import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { App as AntdApp } from 'antd';
import MainLayout from '@app/layout/MainLayout';

const App: React.FC = () => (
    <AntdApp>
        <BrowserRouter>
            <MainLayout />
        </BrowserRouter>
    </AntdApp>
);

export default App;
