/**
 * DatasetPreviewScreen - プレビュー画面骨組み
 * 
 * 責務:
 * - Tabs 構築
 * - ResizeObserver で cardHeight 計測
 * - CsvPreviewCard への props 伝達
 */

import React, { useLayoutEffect, useRef, useState } from 'react';
import { Col, Row, Tabs, Empty } from 'antd';
import { useDatasetPreviewVM } from '../model/useDatasetPreviewVM';
import { CsvPreviewCard } from '../ui/CsvPreviewCard';
import { readableTextColor } from '../../shared/ui/colors';
import type { PreviewSource } from '../model/types';
import './styles.css';

export type DatasetPreviewScreenProps = {
  source: PreviewSource;
  initialTypeKey?: string;
};

const TAB_BAR_FALLBACK = 40;

export const DatasetPreviewScreen: React.FC<DatasetPreviewScreenProps> = ({ 
  source, 
  initialTypeKey 
}) => {
  const { tabs } = useDatasetPreviewVM(source);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const tabsRef = useRef<HTMLDivElement | null>(null);
  const [cardHeight, setCardHeight] = useState(300);

  useLayoutEffect(() => {
    const calc = () => {
      const host = hostRef.current;
      if (!host) return;
      
      const h = host.clientHeight;
      const navEl = tabsRef.current?.querySelector('.ant-tabs-nav') as HTMLElement | null;
      const navH = navEl?.offsetHeight ?? TAB_BAR_FALLBACK;
      const margin = 8; // tabBarStyle の marginBottom
      
      const computed = Math.max(160, Math.floor(h - navH - margin));
      
      // デバッグログ（開発時のみ有効化）
      if (process.env.NODE_ENV === 'development') {
        console.debug('[DatasetPreviewScreen] hostH:', h, 'navH:', navH, 'margin:', margin, '→ cardHeight:', computed);
      }
      
      setCardHeight(computed);
    };
    
    const ro = new ResizeObserver(calc);
    if (hostRef.current) ro.observe(hostRef.current);
    calc();
    
    return () => ro.disconnect();
  }, []);

  return (
    <Row className="dp-row">
      <Col span={24} className="dp-right">
        <div ref={hostRef} className="dp-host">
          {tabs.length === 0 ? (
            <div className="dp-empty">
              <Empty description="プレビュー対象がありません" />
            </div>
          ) : (
            <Tabs
              defaultActiveKey={initialTypeKey ?? tabs[0].key}
              className="dp-tabs"
              tabBarStyle={{ marginBottom: 8, flexShrink: 0 }}
              renderTabBar={(props, DefaultTabBar) => (
                <div ref={(el) => { tabsRef.current = el; }}>
                  <DefaultTabBar {...props} />
                </div>
              )}
              items={tabs.map(t => {
                const fg = readableTextColor(t.color ?? '#777');
                return {
                  key: t.key,
                  label: (
                    <div 
                      className="dp-pill" 
                      style={{ 
                        background: t.color ?? '#777',
                        color: fg 
                      }}
                    >
                      <span>{t.label}</span>
                      {t.status === 'valid' ? (
                        <span style={{ marginLeft: 6, fontSize: 12 }}>✅</span>
                      ) : t.status === 'invalid' ? (
                        <span style={{ marginLeft: 6, fontSize: 12 }}>❌</span>
                      ) : (
                        <span style={{ marginLeft: 6, fontSize: 12, opacity: 0.6 }}>未</span>
                      )}
                    </div>
                  ),
                  children: (
                    <div className="dp-pane">
                      <CsvPreviewCard
                        type={t.key}
                        label={t.label}
                        csvPreview={t.preview}
                        validationResult={t.status ?? 'unknown'}
                        cardHeight={cardHeight}
                        backgroundColor={t.color}
                        hideHead={true}
                        fallbackColumns={t.fallbackColumns}
                      />
                    </div>
                  ),
                };
              })}
            />
          )}
        </div>
      </Col>
    </Row>
  );
};
