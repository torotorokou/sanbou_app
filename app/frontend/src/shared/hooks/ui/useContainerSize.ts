// ResizeObserver ベースでコンテナ要素のサイズ変化を監視するフック
// 用途: コンポーネント幅/高さに応じて UI を切り替えたい場合に使用
// SSR セーフ、パフォーマンス配慮（初期値は 0、observer は最小限）

import { useEffect, useRef, useState } from "react";

export type ContainerSize = {
  width: number;
  height: number;
};

export const useContainerSize = <T extends HTMLElement>(): {
  ref: React.RefObject<T>;
  size: ContainerSize;
} => {
  const ref = useRef<T>(null);
  const [size, setSize] = useState<ContainerSize>({ width: 0, height: 0 });

  useEffect(() => {
    if (!ref.current || typeof window === "undefined") return;

    const el = ref.current;
    let frame: number | null = null;

    const update = (entry: ResizeObserverEntry) => {
      // 低頻度にするため rAF でスロットル
      if (frame != null) return;
      frame = window.requestAnimationFrame(() => {
        frame = null;
        const cr = entry.contentRect;
        setSize({ width: Math.round(cr.width), height: Math.round(cr.height) });
      });
    };

    const ro = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) update(entry);
    });
    ro.observe(el);

    // 初回測定
    setSize({
      width: Math.round(el.clientWidth),
      height: Math.round(el.clientHeight),
    });

    return () => {
      if (frame != null) window.cancelAnimationFrame(frame);
      ro.disconnect();
    };
  }, []);

  return { ref, size };
};

export default useContainerSize;
