import type { ThemeConfig } from 'antd';
import { customTokens } from './tokens';

export const appTheme: ThemeConfig = {
    token: {
        ...customTokens,
    },
};
