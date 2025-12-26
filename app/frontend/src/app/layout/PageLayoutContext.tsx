/**
 * PageLayoutContext
 *
 * ページコンポーネントがレイアウト設定をMainLayoutに伝えるためのContext
 *
 * 使用例：
 * ```tsx
 * const MyPage = () => {
 *   usePageLayout({ noPadding: true });
 *   return <div>...</div>;
 * };
 * ```
 */
import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";

export interface PageLayoutConfig {
  /** 左右のパディングを無効化 (全幅レイアウト用) */
  noPadding?: boolean;
}

interface PageLayoutContextValue {
  config: PageLayoutConfig;
  setConfig: (config: PageLayoutConfig) => void;
}

const PageLayoutContext = createContext<PageLayoutContextValue | undefined>(
  undefined,
);

export const PageLayoutProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [config, setConfigState] = useState<PageLayoutConfig>({});

  const setConfig = useCallback((newConfig: PageLayoutConfig) => {
    setConfigState(newConfig);
  }, []);

  return (
    <PageLayoutContext.Provider value={{ config, setConfig }}>
      {children}
    </PageLayoutContext.Provider>
  );
};

/**
 * ページコンポーネントで使用するHook
 * ページのマウント時にレイアウト設定を宣言する
 */
export const usePageLayout = (config: PageLayoutConfig) => {
  const context = useContext(PageLayoutContext);

  if (!context) {
    console.warn("usePageLayout must be used within PageLayoutProvider");
    return;
  }

  React.useEffect(() => {
    context.setConfig(config);
    // クリーンアップ: ページがアンマウントされたらデフォルトに戻す
    return () => {
      context.setConfig({});
    };
  }, [config.noPadding]); // 設定が変更されたときのみ再実行
};

/**
 * MainLayoutで現在のレイアウト設定を取得するHook
 */
export const usePageLayoutConfig = (): PageLayoutConfig => {
  const context = useContext(PageLayoutContext);

  if (!context) {
    return {}; // Providerの外では空の設定を返す
  }

  return context.config;
};
