/**
 * ThemeProvider - Ant Designのテーマとロケール設定
 * 
 * 機能:
 *   - 日本語ロケールの適用
 *   - レスポンシブデザイン対応（コンポーネントサイズ自動調整）
 *   - カスタムトークンの適用
 * 
 * 設計方重:
 *   - 画面幅に応じてコンポーネントサイズを自動調整
 *     * デスクトップ（xl以上）: large
 *     * タブレット（md～xxl）: middle
 *     * モバイル（sm以下）: small
 *   - borderRadiusもレスポンシブに調整
 *   - useResponsive hookで画面幅を監視
 */
import React from "react";
import { ConfigProvider } from "antd";
import jaJP from 'antd/locale/ja_JP';
import { customTokens, useResponsive, isTabletOrHalf, isDesktop } from '@/shared';

/**
 * ThemeProviderコンポーネント
 * 
 * アプリケーション全体をラップし、Ant Designのテーマを適用する。
 * 
 * @param children - ラップする子要素（通常はアプリ全体）
 * 
 * @example
 * // main.tsxで使用
 * <ThemeProvider>
 *   <BrowserRouter>
 *     <App />
 *   </BrowserRouter>
 * </ThemeProvider>
 */
export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // 画面幅を監視し、レスポンシブなサイズ調整を行う
  const { width } = useResponsive();
  
  // タブレット以上（md～xxl）かどうか
  const isMd = typeof width === 'number' ? isTabletOrHalf(width) : false;
  
  // デスクトップ（xl以上）かどうか
  const isXlUp = typeof width === 'number' ? isDesktop(width) : false;
  
  // コンポーネントサイズの決定
  const componentSize = isXlUp ? "large" : isMd ? "middle" : "small";
  
  return (
    <ConfigProvider
      locale={jaJP}  // 日本語ロケール（日付、曜日、メッセージ等）
      componentSize={componentSize}  // レスポンシブサイズ
      theme={{ token: { ...customTokens, borderRadius: isMd ? 10 : 8 } }}  // カスタムトークン
    >
      {children}
    </ConfigProvider>
  );
};
