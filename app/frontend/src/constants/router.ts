// src/constants/router.ts

/**
 * アプリケーション内のページルート一覧
 * 各ルートが何のページなのかをコメントで明記しておくと保守性UP
 */
export const ROUTER_PATHS = {
    // ポータル(トップ)
    PORTAL: '/',
    // ダッシュボード系
    DASHBOARD: '/dashboard',
    FACTORY: '/factory',
    SALES_TREE: '/sales-tree',
    PRICING: '/pricing',
    CUSTOMER_LIST: '/customer-list',

    // 帳票系
    REPORT_MANAGE: '/report/manage',
    REPORT_FACTORY: '/report/factory',
    LEDGER_BOOK: '/ledger-book',

    // データ分析系
    ANALYSIS_CUSTOMERLIST: '/analysis/customer-list',

    // チャットボット系
    NAVI: '/navi',

    MANUALS: '/manuals',

    // 設定系
    SETTINGS: '/settings',
    ADMIN: '/admin',
    // UPLOAD: '/upload',

    // データベース系
    RECORD_LIST: '/database/records',
    UPLOAD_PAGE: '/database/upload',

    // その他
    TOKEN_PREVIEW: '/token-preview',
    // お知らせ
    NEWS: '/news',
};
