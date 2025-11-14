import React, { useLayoutEffect, useRef, useState } from 'react';
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
  backgroundColor?: string;
  isOptional?: boolean;
  hideHead?: boolean;
  fallbackColumns?: string[];        // CSV未アップロード時のヘッダー定義
  showEmptyTableWhenNoData?: boolean; // fallbackColumns がない場合でも空テーブルを表示
};

export const CsvPreviewCard: React.FC<Props> = ({
  type,
  label,
  csvPreview,
  validationResult,
  cardHeight = 300,
  backgroundColor: propBackgroundColor,
  isOptional = false,
  hideHead = false,
  fallbackColumns,
  showEmptyTableWhenNoData = false,
}) => {
  const backgroundColor = propBackgroundColor || CSV_TYPE_COLORS[type] || '#ffffff';
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [scrollY, setScrollY] = useState(200);

  // ResizeObserver で実寸から scroll.y を算出
  useLayoutEffect(() => {
    const calc = () => {
      const card = cardRef.current;
      if (!card) return;
      
      // hideHead 時は head がレンダリングされないので offsetHeight = 0
      const head = hideHead ? null : (card.querySelector('.ant-card-head') as HTMLElement | null);
      const body = card.querySelector('.ant-card-body') as HTMLElement | null;
      
      const headH = head?.offsetHeight ?? 0;
      const bodyStyle = body ? getComputedStyle(body) : null;
      const padY = bodyStyle 
        ? parseFloat(bodyStyle.paddingTop || '0') + parseFloat(bodyStyle.paddingBottom || '0')
        : 0;
      
      // 横スクロールバー分 + 微調整（実測では 16〜18px 程度必要）
      const HSCROLL = 16;
      const FUDGE = 2;
      
      const computed = Math.max(80, Math.floor(cardHeight - headH - padY - HSCROLL - FUDGE));
      
      // デバッグログ（開発時のみ）
      if (process.env.NODE_ENV === 'development') {
        console.debug('[CsvPreviewCard]', type, '- cardH:', cardHeight, 'headH:', headH, 'padY:', padY, '→ scrollY:', computed);
      }
      
      setScrollY(computed);
    };
    
    const ro = new ResizeObserver(calc);
    if (cardRef.current) ro.observe(cardRef.current);
    calc();
    
    return () => ro.disconnect();
  }, [cardHeight, hideHead, type]);

  return (
    <div ref={cardRef} style={{ height: cardHeight, minHeight: 0, overflow: 'hidden' }}>
      <Card
      size="small"
      title={
        hideHead ? null : (
          <div>
            <span>
              {label ?? type} プレビュー
              {isOptional && <span style={{ color: '#1890ff', marginLeft: 8, fontSize: 13 }}>任意</span>}
              {validationResult === 'valid' ? (
                <span style={{ color: 'green', marginLeft: 12 }}>✅ 有効</span>
              ) : validationResult === 'invalid' ? (
                <span style={{ color: 'red', marginLeft: 12 }}>❌ 無効</span>
              ) : (
                <span style={{ color: 'gray', marginLeft: 12 }}>未判定</span>
              )}
            </span>
          </div>
        )
      }
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
      styles={{
        header: hideHead ? { display: 'none' } : { backgroundColor },
        body: {
          display: 'flex',
          flexDirection: 'column',
          padding: 8,
          flex: 1,
          minHeight: 0,
          overflow: 'hidden',
        },
      }}
    >
      {(() => {
        // 1. csvPreview がありデータがある → 通常のテーブル表示
        if (csvPreview && csvPreview.rows.length > 0) {
          return (
            <div
              style={{
                flex: 1,
                minHeight: 0,
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
              }}
              className="csv-preview-wrapper"
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
                size="small"
                scroll={{ x: 'max-content', y: scrollY }}
                variant="outlined"
                rowKey={(_, i) => (i ?? 0).toString()}
              />
            </div>
          );
        }
        
        // 2. fallbackColumns がある → ヘッダーのみの空テーブル表示
        if (fallbackColumns && fallbackColumns.length > 0) {
          return (
            <div
              style={{
                flex: 1,
                minHeight: 0,
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
              }}
              className="csv-preview-wrapper"
            >
              <Table
                columns={fallbackColumns.map((col, i) => ({
                  title: col,
                  dataIndex: i,
                  key: i,
                  width: 120,
                  ellipsis: true,
                }))}
                dataSource={[]}
                pagination={false}
                size="small"
                scroll={{ x: 'max-content', y: scrollY }}
                variant="outlined"
                locale={{ emptyText: 'CSV未アップロード（ヘッダー定義）' }}
              />
            </div>
          );
        }
        
        // 3. showEmptyTableWhenNoData が true → 1列の空テーブル表示
        if (showEmptyTableWhenNoData) {
          return (
            <div
              style={{
                flex: 1,
                minHeight: 0,
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
              }}
              className="csv-preview-wrapper"
            >
              <Table
                columns={[{ title: 'データなし', dataIndex: 'empty', key: 'empty', width: 120 }]}
                dataSource={[]}
                pagination={false}
                size="small"
                scroll={{ x: 'max-content', y: scrollY }}
                variant="outlined"
                locale={{ emptyText: 'CSV未アップロード' }}
              />
            </div>
          );
        }
        
        // 4. デフォルト → Empty コンポーネント表示
        return (
          <Empty
            description="プレビューなし"
            style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
            }}
          />
        );
      })()}
    </Card>
    </div>
  );
};
