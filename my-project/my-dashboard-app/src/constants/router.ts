// src/constants/router.ts

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

/**
 * アプリケーション内のページルート一覧
 * 各ルートが何のページなのかをコメントで明記しておくと保守性UP
 */
export const ROUTER_PATHS = {
    // ダッシュボード系
    DASHBOARD: '/dashboard',
    FACTORY: '/factory',

    // 帳票系
    REPORT_MANAGE: '/report/manage',
    REPORT_FACTORY: '/report/factory',

    // チャットボット系
    NAVI: '/navi',

    // 設定系
    SETTINGS: '/settings',
    ADMIN: '/admin',
    UPLOAD: '/upload',
    MANUAL: '/manual',

    // その他
    TOKEN_PREVIEW: '/token-preview',
};
