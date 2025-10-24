// サイドバーの「デフォルト開閉状態」を画面幅から自動決定するフック
// 仕様:
// - 画面幅 <= BREAKPOINTS.smallPC のとき: デフォルト「閉じる」
// - 画面幅 >  BREAKPOINTS.smallPC のとき: デフォルト「開く」
// - リサイズ時にも上記ルールに追従する
// - UI（Sidebar.tsx）からは、このフックが返す collapsed/setCollapsed を利用する

import { useEffect, useState } from "react";
import { isDesktop, ANT } from "@/shared";

// 単一責任原則（SOLIDのS）: 判定ロジックをこのフックに集約し、UIから分離
export const useSidebarDefault = () => {
  // 内部状態: サイドバーが畳まれているか（true=閉じている）
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    if (typeof window === "undefined") return false; // SSR等では開いた状態にしておく
    const w = window.innerWidth;
    return !isDesktop(w); // 1280 未満は閉じる
  });

  useEffect(() => {
    // リサイズに応じてデフォルト状態を更新（ルールを常に優先）
    const updateByRule = () => {
      const w = window.innerWidth;
      const shouldCollapse = w < ANT.xl; // 同義: !isDesktop(w)
      setCollapsed(shouldCollapse);
    };

    window.addEventListener("resize", updateByRule);
    return () => window.removeEventListener("resize", updateByRule);
  }, []);

  return { collapsed, setCollapsed };
};

export type UseSidebarDefaultReturn = ReturnType<typeof useSidebarDefault>;
