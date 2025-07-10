// src/constants/sidebarMenu.tsx
import React from 'react';
import {
    DashboardOutlined,
    TableOutlined,
    FileTextOutlined,
    CompassOutlined,
    SettingOutlined,
    UploadOutlined,
    ToolOutlined,
    BookOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { ROUTER_PATHS } from './router';

export const SIDEBAR_MENU = [
    {
        key: 'dashboardGroup',
        icon: <DashboardOutlined />,
        label: 'ダッシュボード',
        children: [
            {
                key: ROUTER_PATHS.DASHBOARD, // ← パスそのもの
                icon: <DashboardOutlined />,
                label: <Link to={ROUTER_PATHS.DASHBOARD}>管理表</Link>,
            },
            {
                key: ROUTER_PATHS.FACTORY,
                icon: <TableOutlined />,
                label: <Link to={ROUTER_PATHS.FACTORY}>工場管理</Link>,
            },
            {
                key: ROUTER_PATHS.PRICING,
                icon: <FileTextOutlined />,
                label: <Link to={ROUTER_PATHS.PRICING}>単価表</Link>,
            },
        ],
    },
    {
        key: 'report',
        icon: <FileTextOutlined />,
        label: '帳票作成',
        children: [
            {
                key: ROUTER_PATHS.REPORT_MANAGE,
                icon: <FileTextOutlined />,
                label: <Link to={ROUTER_PATHS.REPORT_MANAGE}>管理業務</Link>,
            },
            {
                key: ROUTER_PATHS.REPORT_FACTORY,
                icon: <FileTextOutlined />,
                label: <Link to={ROUTER_PATHS.REPORT_FACTORY}>工場帳簿</Link>,
            },
        ],
    },
    {
        key: ROUTER_PATHS.NAVI,
        icon: <CompassOutlined />,
        label: <Link to={ROUTER_PATHS.NAVI}>参謀NAVI</Link>,
    },
    {
        key: 'management',
        icon: <SettingOutlined />,
        label: '管理機能',
        children: [
            {
                key: ROUTER_PATHS.SETTINGS,
                icon: <SettingOutlined />,
                label: <Link to={ROUTER_PATHS.SETTINGS}>設定</Link>,
            },
            {
                key: ROUTER_PATHS.ADMIN,
                icon: <ToolOutlined />,
                label: <Link to={ROUTER_PATHS.ADMIN}>管理者メニュー</Link>,
            },
        ],
    },
    {
        key: ROUTER_PATHS.UPLOAD,
        icon: <UploadOutlined />,
        label: <Link to={ROUTER_PATHS.UPLOAD}>データアップロード</Link>,
    },
    {
        key: ROUTER_PATHS.MANUAL,
        icon: <BookOutlined />,
        label: <Link to={ROUTER_PATHS.MANUAL}>マニュアル一覧</Link>,
    },
];
