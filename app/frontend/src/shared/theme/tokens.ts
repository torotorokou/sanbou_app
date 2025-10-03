// src/theme/tokens.ts

export const customTokens = {
    // === 基本色パレット ===
    colorPrimary: '#10b981', // ブランドグリーン
    colorSuccess: '#22c55e', // 成功色
    colorError: '#ef4444', // エラー色
    colorWarning: '#f59e0b', // 警告色
    colorInfo: '#3b82f6', // 情報色
    colorNeutral: '#9ca3af', // 中性色

    // === 背景色 ===
    colorBgBase: '#f9fefb', // ベース背景
    colorBgLayout: '#eef5f0', // レイアウト背景
    colorBgContainer: '#ffffff', // コンテナ背景
    colorBgCard: '#fafafa', // カード背景

    // === テキスト色 ===
    colorText: '#1e293b', // メインテキスト
    colorTextSecondary: '#64748b', // セカンダリテキスト
    colorTextMuted: '#888', // ミュートテキスト

    // === サイドバー色 ===
    colorSiderBg: '#0f2a29', // サイドバー背景
    colorSiderText: '#ffffff', // サイドバーテキスト
    colorSiderHover: '#134e4a', // サイドバーホバー

    // === ボーダー・影 ===
    colorBorder: '#ccc', // 基本ボーダー
    colorBorderSecondary: '#d1fae5', // セカンダリボーダー
    shadowLight: 'rgba(0,0,0,0.05)', // 薄い影
    shadowMedium: 'rgba(0,0,0,0.10)', // 中程度の影

    // === チャート色（5色パレット） ===
    chartGreen: '#10b981', // メイン（グリーン）
    chartBlue: '#3b82f6', // ブルー
    chartOrange: '#f59e0b', // オレンジ
    chartRed: '#ef4444', // レッド
    chartPurple: '#6366f1', // パープル

    // === CSV背景色 ===
    csvShipmentBg: '#e6f7ff', // 出荷CSV背景（ブルー系）
    csvReceiveBg: '#fff1f0', // 受入CSV背景（レッド系）
    csvYardBg: '#f6ffed', // ヤードCSV背景（グリーン系）

    // === 状態色 ===
    statusValid: '#22c55e', // 有効状態（success色と統一）
    statusInvalid: '#ef4444', // 無効状態（error色と統一）
    statusUnknown: '#9ca3af', // 不明状態（neutral色と統一）

    // === 特殊用途色 ===
    highlightYellow: '#ffeb3b', // ハイライト色
    linkBlue: '#1890ff', // リンク色

    // === 透明度付きカラー ===
    whiteAlpha80: 'rgba(255, 255, 255, 0.8)',
    blackAlpha50: 'rgba(0, 0, 0, 0.5)',
};
