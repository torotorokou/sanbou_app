import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import { ConfigProvider } from 'antd';
import { customTokens } from './theme/tokens';
import { generateCssVars } from './theme/cssVars';
import 'antd/dist/reset.css';
import './index.css';
import './shared/styles/base.css';

// ① customTokens（ブランドカラー等）からCSS変数を作る
const cssVars = generateCssVars();

// ② そのCSS変数を<head>にstyleタグで注入
const styleTag = document.createElement('style');
styleTag.innerHTML = cssVars;
document.head.appendChild(styleTag);

// ③ Ant DesignのConfigProviderにも customTokens を渡しておく（推奨）
ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <ConfigProvider theme={{ token: customTokens }}>
            <App />
        </ConfigProvider>
    </React.StrictMode>
);
