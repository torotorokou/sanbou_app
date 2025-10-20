/**
 * useContainerSize Hook
 * ResizeObserver を使ってコンテナサイズを監視する共通フック
 */

import { useEffect, useRef, useState } from "react";

export interface ContainerSize {
  width: number;
  height: number;
}

export function useContainerSize(): [React.RefObject<HTMLDivElement>, ContainerSize | null] {
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState<ContainerSize | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new ResizeObserver((entries) => {
      if (entries[0]) {
        const { width, height } = entries[0].contentRect;
        setSize({ width, height });
      }
    });

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return [ref, size];
}
