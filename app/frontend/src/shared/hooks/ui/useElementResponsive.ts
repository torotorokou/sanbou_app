/**
 * useElementResponsive - 要素幅ベースのレスポンシブ判定
 *
 * 【役割】
 * - コンテナ要素の幅に基づくブレークポイント判定
 * - useContainerSize + makeFlags の組み合わせ
 *
 * 【使用例】
 * ```tsx
 * const { ref, flags, width } = useElementResponsive<HTMLDivElement>();
 * return <div ref={ref}>{flags.flags.isMobile ? 'Mobile' : 'Desktop'}</div>;
 * ```
 */
import { useMemo } from "react";
import useContainerSize from "./useContainerSize";
import { makeFlags, type ResponsiveFlags } from "./useResponsive";

export function useElementResponsive<T extends HTMLElement>(): {
  ref: React.RefObject<T>;
  width: number;
  height: number;
  flags: ResponsiveFlags;
} {
  const { ref, size } = useContainerSize<T>();
  const flags = useMemo(() => makeFlags(size.width), [size.width]);
  return { ref, width: size.width, height: size.height, flags };
}

export default useElementResponsive;
