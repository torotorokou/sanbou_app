/**
 * useInstallTabsFillCSS Hook
 * Tabs高さフィックス用CSSを動的にインストール
 */

import { useEffect } from 'react';
import { tabsFillCSS, TABS_FILL_CLASS } from '../styles/tabsFill.css';

export const useInstallTabsFillCSS = (): string => {
  useEffect(() => {
    const el = document.createElement('style');
    el.setAttribute('data-tabs-fill', 'true');
    el.textContent = tabsFillCSS;
    document.head.appendChild(el);
    return () => {
      document.head.removeChild(el);
    };
  }, []);

  return TABS_FILL_CLASS;
};
