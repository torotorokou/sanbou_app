import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Table } from 'antd';
import type { TableProps } from 'antd';

type AutoHeightTableProps<RecordType extends object = Record<string, unknown>> = TableProps<RecordType> & {
  bottomPadding?: number;
};

export function AutoHeightTable<RecordType extends object = Record<string, unknown>>({ bottomPadding = 16, scroll, ...rest }: AutoHeightTableProps<RecordType>) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [bodyHeight, setBodyHeight] = useState<number | undefined>(undefined);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const resize = () => {
      const rect = el.getBoundingClientRect();
      const available = window.innerHeight - rect.top - bottomPadding;
      setBodyHeight(Math.max(0, Math.floor(available)));
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(document.body);
    ro.observe(el);
    window.addEventListener('resize', resize);
    return () => {
      ro.disconnect();
      window.removeEventListener('resize', resize);
    };
  }, [bottomPadding]);

  const mergedScroll = useMemo(() => ({
    ...scroll,
    y: bodyHeight,
  }), [scroll, bodyHeight]);

  return (
    <div ref={wrapRef} className="min-h-0" style={{ display: 'flex', flexDirection: 'column' }}>
      <Table {...rest} scroll={mergedScroll} />
    </div>
  );
}

export default AutoHeightTable;
