import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Table } from 'antd';
import type { TableProps } from 'antd';

type AutoHeightTableProps<RecordType extends object = Record<string, unknown>> = TableProps<RecordType> & {
  /** Table外枠との余白分を差し引く（ヘッダーやパディング） */
  paddingOffset?: number;
};

export function AutoHeightTable<RecordType extends object = Record<string, unknown>>({ paddingOffset = 24, scroll, ...rest }: AutoHeightTableProps<RecordType>) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [bodyHeight, setBodyHeight] = useState<number | undefined>(undefined);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const compute = () => {
      const available = el.clientHeight - paddingOffset;
      setBodyHeight(Math.max(0, Math.floor(available)));
    };
    compute();
    const ro = new ResizeObserver(compute);
    ro.observe(el);
    // 親の高さ変化も捉えたい場合は親要素をobserve
    if (el.parentElement) ro.observe(el.parentElement);
    window.addEventListener('resize', compute);
    return () => {
      ro.disconnect();
      window.removeEventListener('resize', compute);
    };
  }, [paddingOffset]);

  const mergedScroll = useMemo(() => ({
    ...scroll,
    y: bodyHeight,
  }), [scroll, bodyHeight]);

  return (
    <div ref={wrapRef} className="min-h-0" style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <Table {...rest} scroll={mergedScroll} />
    </div>
  );
}

export default AutoHeightTable;
