import { customTokens } from './tokens';

export function generateCssVars(): string {
    return `
    :root {
      --color-primary: ${customTokens.colorPrimary};
      --color-success: ${customTokens.colorSuccess};
      --color-error: ${customTokens.colorError};
      --color-warning: ${customTokens.colorWarning};
      --color-info: ${customTokens.colorInfo};

      --color-bg-base: ${customTokens.colorBgBase};
      --color-bg-layout: ${customTokens.colorBgLayout};
      --color-bg-container: ${customTokens.colorBgContainer};
      --color-sider-bg: ${customTokens.colorSiderBg};
      --color-sider-text: ${customTokens.colorSiderText};
      --color-sider-hover: ${customTokens.colorSiderHover};

      --color-text: ${customTokens.colorText};
      --color-text-secondary: ${customTokens.colorTextSecondary};
      --color-border-secondary: ${customTokens.colorBorderSecondary};
    }
  `;
}
