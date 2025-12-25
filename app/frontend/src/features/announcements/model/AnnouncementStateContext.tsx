/**
 * AnnouncementStateContext - お知らせの状態管理コンテキスト
 *
 * 既読状態の変更をアプリケーション全体で共有するためのコンテキスト。
 * 既読にした際に未読数を再計算するトリガーを提供。
 */

import React, { createContext, useContext, useState, useCallback } from "react";
import type { ReactNode } from "react";

interface AnnouncementStateContextValue {
  /** 既読状態の変更カウンター（変更時にインクリメント） */
  readStateVersion: number;
  /** 既読状態が変更されたことを通知 */
  notifyReadStateChanged: () => void;
}

const AnnouncementStateContext = createContext<
  AnnouncementStateContextValue | undefined
>(undefined);

interface AnnouncementStateProviderProps {
  children: ReactNode;
}

/**
 * お知らせ状態プロバイダー
 */
export const AnnouncementStateProvider: React.FC<
  AnnouncementStateProviderProps
> = ({ children }) => {
  const [readStateVersion, setReadStateVersion] = useState(0);

  const notifyReadStateChanged = useCallback(() => {
    setReadStateVersion((v) => v + 1);
  }, []);

  return (
    <AnnouncementStateContext.Provider
      value={{ readStateVersion, notifyReadStateChanged }}
    >
      {children}
    </AnnouncementStateContext.Provider>
  );
};

/**
 * お知らせ状態コンテキストを使用するフック
 */
export const useAnnouncementState = (): AnnouncementStateContextValue => {
  const context = useContext(AnnouncementStateContext);
  if (!context) {
    throw new Error(
      "useAnnouncementState must be used within AnnouncementStateProvider",
    );
  }
  return context;
};
