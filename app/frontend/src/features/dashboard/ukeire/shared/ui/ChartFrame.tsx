/**
 * ChartFrame Component
 * 親の実寸高さを測ってResponsiveContainerに渡すラッパー
 */

import React, { useEffect, useRef, useState } from "react";
import { ResponsiveContainer } from "recharts";

type ChartFrameProps = React.PropsWithChildren<{ style?: React.CSSProperties }>;

export const ChartFrame: React.FC<ChartFrameProps> = ({ style, children }) => {
  const ref = useRef<HTMLDivElement | null>(null);
  const [h, setH] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let disposed = false;
    const setFromRect = () => {
      const r = el.getBoundingClientRect();
      const hh = Math.max(0, Math.floor(r.height));
      setH((prev) => (Math.abs(prev - hh) > 1 ? hh : prev));
    };
    const ro = new ResizeObserver(() =>
      requestAnimationFrame(() => !disposed && setFromRect()),
    );
    ro.observe(el);
    let tries = 0;
    const kick = () => {
      if (disposed) return;
      setFromRect();
      if (h === 0 && tries++ < 20) requestAnimationFrame(kick);
    };
    kick();
    window.addEventListener("resize", setFromRect);
    return () => {
      disposed = true;
      ro.disconnect();
      window.removeEventListener("resize", setFromRect);
    };
  }, [h]);

  return (
    <div
      ref={ref}
      style={{ height: "100%", width: "100%", minHeight: 200, ...style }}
    >
      {h > 0 ? (
        <ResponsiveContainer width="100%" height={h}>
          {children as unknown as React.ReactElement}
        </ResponsiveContainer>
      ) : (
        <ResponsiveContainer width="100%" minHeight={200} aspect={3}>
          {children as unknown as React.ReactElement}
        </ResponsiveContainer>
      )}
    </div>
  );
};
