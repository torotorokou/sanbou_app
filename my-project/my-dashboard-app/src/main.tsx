import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { ConfigProvider } from 'antd';
import { customTokens } from './theme/tokens';
import { generateCssVars } from './theme/cssVars';
import 'antd/dist/reset.css';
import './index.css';

// CSS変数を<head>に注入
const styleTag = document.createElement('style');
styleTag.innerHTML = generateCssVars();
document.head.appendChild(styleTag);

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <ConfigProvider theme={{ token: customTokens }}>
            <App />
        </ConfigProvider>
    </React.StrictMode>
);
