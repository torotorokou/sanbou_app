import { customTokens } from './tokens';

export function generateCssVars(): string {
    return `
    :root {
      /* 基本カラー */
      --color-primary: ${customTokens.colorPrimary};
      --color-success: ${customTokens.colorSuccess};
      --color-error: ${customTokens.colorError};
      --color-warning: ${customTokens.colorWarning};
      --color-info: ${customTokens.colorInfo};

      /* 背景色 */
      --color-bg-base: ${customTokens.colorBgBase};
      --color-bg-layout: ${customTokens.colorBgLayout};
      --color-bg-container: ${customTokens.colorBgContainer};
      --color-sider-bg: ${customTokens.colorSiderBg};
      --color-sider-text: ${customTokens.colorSiderText};
      --color-sider-hover: ${customTokens.colorSiderHover};

      /* テキスト色 */
      --color-text: ${customTokens.colorText};
      --color-text-secondary: ${customTokens.colorTextSecondary};
      --color-border-secondary: ${customTokens.colorBorderSecondary};
      
      /* チャート系 */
      --chart-primary: ${customTokens.chartGreen};
      --chart-success: ${customTokens.colorSuccess};
      --chart-info: ${customTokens.colorInfo};
      --chart-warning: ${customTokens.colorWarning};
      --chart-danger: ${customTokens.colorError};
      
      /* アクション系 */
      --action-primary: ${customTokens.colorInfo};
      --action-secondary: ${customTokens.colorWarning};
      
      /* CSV系 */
      --csv-shipment-bg: ${customTokens.csvShipmentBg};
      --csv-receive-bg: ${customTokens.csvReceiveBg};
      --csv-yard-bg: ${customTokens.csvYardBg};
      
      /* ボーダー・影 */
      --border-light: ${customTokens.colorBorder};
      --shadow-light: ${customTokens.shadowLight};
      --shadow-medium: ${customTokens.shadowMedium};
      
      /* レポート系 */
      --report-card-bg: ${customTokens.colorBgCard};
      --report-preview-bg: ${customTokens.colorBgCard};
      
      /* 状態系 */
      --status-valid: ${customTokens.statusValid};
      --status-invalid: ${customTokens.statusInvalid};
      --status-unknown: ${customTokens.statusUnknown};
      
      /* レスポンシブ対応 */
      --sidebar-transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      --content-transition: padding 0.3s ease-in-out;
      
  /* ブレークポイント (値は JS 側 'src/shared/constants/breakpoints.ts' を単一のソースにすること) */
  --breakpoint-mobile: 767px; /* BREAKPOINTS.sm */
  --breakpoint-tablet: 1023px; /* BREAKPOINTS.tabletMax (informational) */
  --breakpoint-auto-collapse: 1280px; /* BREAKPOINTS.autoCollapse */
  --breakpoint-force-collapse: 900px; /* BREAKPOINTS.forceCollapse */
    }
  `;
}
