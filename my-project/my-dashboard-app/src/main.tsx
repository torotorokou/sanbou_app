// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import 'antd/dist/reset.css'; // Ant Design v5 用。v4なら 'antd/dist/antd.css'
import './index.css'; // グローバルスタイル（必要なら）

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
