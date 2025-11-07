import React, { useEffect, useRef, useState } from 'react';
import { Card, Table, Empty } from 'antd';
import type { ValidationStatus } from '../../shared/types/common';
import type { CsvPreviewData } from '../model/types';

const CSV_TYPE_COLORS: Record<string, string> = {
  receive: '#f0f7e8ff',
  shipment: '#ffffffff',
  yard: '#ffffffff',
};

type Props = {
  type: string;
  label?: string;
  csvPreview: CsvPreviewData | null;
  validationResult: ValidationStatus;
  cardHeight?: number;
  tableBodyHeight?: number;
  backgroundColor?: string;
  isOptional?: boolean;
};

export const CsvPreviewCard: React.FC<Props> = ({
  type,
  label,
  csvPreview,
  validationResult,
  cardHeight = 300,
  tableBodyHeight = 220,
  backgroundColor: propBackgroundColor,
  isOptional = false,
}) => {
  const backgroundColor = propBackgroundColor || CSV_TYPE_COLORS[type] || '#ffffff';

  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const [measuredTableHeight, setMeasuredTableHeight] = useState<number | null>(null);

  useEffect(() => {
    const el = wrapperRef.current;
    if (!el) return;
    const update = () => {
      const h = el.clientHeight;
      setMeasuredTableHeight(h);
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [cardHeight, tableBodyHeight]);

  const usedTableHeight = tableBodyHeight ?? measuredTableHeight ?? Math.max(80, Math.floor(cardHeight * 0.6));

  return (
    <Card
      title={
        <span>
          {label ?? type} プレビュー
          {isOptional && (
            <span
              style={{
                color: '#1890ff',
                marginLeft: 8,
                fontSize: 13,
              }}
            >
              任意
            </span>
          )}
          {validationResult === 'valid' ? (
            <span style={{ color: 'green', marginLeft: 12 }}>
              ✅ 有効
            </span>
          ) : validationResult === 'invalid' ? (
            <span style={{ color: 'red', marginLeft: 12 }}>
              ❌ 無効
            </span>
          ) : (
            <span style={{ color: 'gray', marginLeft: 12 }}>
              未判定
            </span>
          )}
        </span>
      }
      size='small'
      headStyle={{ backgroundColor }}
      bodyStyle={{
        padding: 8,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxSizing: 'border-box',
      }}
      style={{
        height: cardHeight,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
      }}
    >
      {csvPreview && csvPreview.rows.length > 0 ? (
        <div
          className="responsive-x"
          ref={wrapperRef}
          style={{
            flex: 1,
            width: '100%',
            overflow: 'hidden',
            overflowX: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            maxHeight: usedTableHeight,
          }}
        >
          <Table
            columns={csvPreview.columns.map((col, i) => ({
              title: col,
              dataIndex: i,
              key: i,
              width: 120,
              ellipsis: true,
            }))}
            dataSource={csvPreview.rows.map((row) =>
              Object.fromEntries(row.map((v, ci) => [ci, v]))
            )}
            pagination={false}
            size='small'
            scroll={{ y: usedTableHeight, x: Math.max(csvPreview.columns.length * 120, 800) }}
            bordered
            rowKey={(_, i) => (i ?? 0).toString()}
            style={{ minWidth: csvPreview.columns.length * 120, flex: '0 0 auto' }}
          />
        </div>
      ) : (
        <Empty description='プレビューなし' />
      )}
    </Card>
  );
};
