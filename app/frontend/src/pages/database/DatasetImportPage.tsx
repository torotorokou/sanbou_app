/**
 * DatasetImportPage - データセットインポート画面（骨組み）
 * 
 * 責務: レイアウト・配置のみ
 * ロジック: useDatabaseUploadVM に委譲
 */

import React, { useLayoutEffect, useRef, useState } from 'react';
import { Typography, Col, Row, Button, Modal, Spin, Tabs, Empty, Select, Space, Badge } from 'antd';
import { useResponsive } from '@/shared';
import styles from './DatasetImportPage.module.css';

import {
  UploadInstructions,
  SimpleUploadPanel,
} from '@features/database/ui';
import { useDatabaseUploadVM } from '@features/database/hooks/useDatabaseUploadVM';
import { csvTypeColors } from '@features/database/model/sampleCsvModel';
import { readableTextColor } from '@features/database/model/constants';
import { DATASETS, type DatasetKey } from '@features/database/model/dataset';

const { Text } = Typography;

// ===== Layout constants =====
const COLUMN_PADDING = 16;
const TAB_BAR_HEIGHT_FALLBACK = 40;

const DatasetImportPage: React.FC = () => {
  const { height } = useResponsive();
  
  // ===== データセット選択 =====
  const [datasetKey, setDatasetKey] = useState<DatasetKey>('shogun_flash');
  
  // ===== ViewModel（状態管理・ロジック） =====
  const {
    panelFiles,
    canUpload,
    uploading,
    onPickFile,
    onRemoveFile,
    doUpload,
  } = useDatabaseUploadVM({ datasetKey });

  // ===== 右プレビューの高さ算出（レイアウト責務） =====
  const rowRef = useRef<HTMLDivElement | null>(null);
  const tabsRef = useRef<HTMLDivElement | null>(null);
  const [cardHeight, setCardHeight] = useState<number>(300);
  const [tabBarHeight, setTabBarHeight] = useState<number>(TAB_BAR_HEIGHT_FALLBACK);

  useLayoutEffect(() => {
    const calc = () => {
      const rowEl = rowRef.current;
      if (!rowEl) return;
      const rowH = rowEl.clientHeight || height || 910;
      const tabEl = tabsRef.current?.querySelector('.ant-tabs-nav') as HTMLElement | null;
      const measuredTab = tabEl?.offsetHeight ?? TAB_BAR_HEIGHT_FALLBACK;
      if (measuredTab !== tabBarHeight) setTabBarHeight(measuredTab);
      const bottomSafeSpace = 16;
      const avail = Math.max(400, Math.floor(rowH - (COLUMN_PADDING * 2) - bottomSafeSpace));
      const ch = Math.max(160, Math.floor(avail - measuredTab));
      setCardHeight(ch);
    };
    const raf = requestAnimationFrame(calc);
    const onResize = () => calc();
    window.addEventListener('resize', onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
    };
  }, [height, tabBarHeight]);

  // 進捗表示用
  const requiredFiles = panelFiles.filter(p => p.required);
  const validCount = requiredFiles.filter(p => p.status === 'valid' && p.file).length;

  return (
    <>
      {/* Contentのpaddingを差し引いた固定高 */}
      <Row ref={rowRef} className={styles.pageContainer}>
        {/* 左カラム：アップロード面 */}
        <Col span={8} className={styles.leftCol}>
          {/* データセット切替 + 進捗 */}
          <div style={{ marginBottom: 12 }}>
            <Space size={8} wrap>
              <Select<DatasetKey>
                value={datasetKey}
                onChange={setDatasetKey}
                options={DATASETS.map(d => ({ value: d.key, label: d.label }))}
                style={{ minWidth: 260 }}
              />
              <Badge
                status={validCount === requiredFiles.length && requiredFiles.length > 0 ? 'success' : 'processing'}
                text={`必須 ${validCount}/${requiredFiles.length}`}
              />
            </Space>
          </div>

          <UploadInstructions />

          {/* 左カラム内部スクロール */}
          <div className={styles.uploadSection}>
            {panelFiles.length === 0 ? (
              <Empty description="CSV定義が見つかりません" />
            ) : (
              <SimpleUploadPanel
                items={panelFiles}
                onPickFile={onPickFile}
                onRemoveFile={onRemoveFile}
              />
            )}
          </div>

          <Button
            type="primary"
            disabled={!canUpload || panelFiles.length === 0}
            onClick={doUpload}
            className={styles.uploadButton}
          >
            アップロードする
          </Button>
          
          {!canUpload && panelFiles.length > 0 && (
            <div className={styles.hint}>
              <Text type="secondary">
                ※ 必須CSVをすべて選択＆検証OKにするとアップロード可能です。
              </Text>
            </div>
          )}
        </Col>

        {/* 右カラム：プレビュー */}
        <Col span={16} className={styles.rightCol}>
          {panelFiles.length === 0 ? (
            <div style={{ flex: 1, display: 'grid', placeItems: 'center' }}>
              <Empty description="プレビュー対象のCSVがありません" />
            </div>
          ) : (
            <Tabs
              key={datasetKey} // 切替時にリセット
              defaultActiveKey={panelFiles[0]?.typeKey}
              style={{ height: '100%' }}
              renderTabBar={(props, DefaultTabBar) => (
                <div ref={(el) => { tabsRef.current = el; }}>
                  <DefaultTabBar {...props} />
                </div>
              )}
              items={panelFiles.map((item) => {
                const bg = csvTypeColors[item.typeKey] || '#777';
                const fg = readableTextColor(bg);
                return {
                  key: item.typeKey,
                  label: (
                    <div
                      style={{
                        display: 'inline-block',
                        padding: '4px 10px',
                        borderRadius: 9999,
                        background: bg,
                        color: fg,
                        fontWeight: 600,
                        fontSize: 14,
                      }}
                    >
                      {item.label}
                    </div>
                  ),
                  children: (
                    <div style={{ height: cardHeight, overflow: 'hidden' }}>
                      {/* TODO: CsvPreviewCardを統合 */}
                      <div style={{ padding: 16 }}>
                        <Text>プレビュー: {item.file?.name ?? '未選択'}</Text>
                      </div>
                    </div>
                  ),
                };
              })}
            />
          )}
        </Col>
      </Row>

      {/* 送信中モーダル */}
      <Modal
        open={uploading}
        footer={null}
        closable={false}
        centered
        maskClosable={false}
        maskStyle={{ backdropFilter: 'blur(2px)' }}
      >
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <Spin size="large" tip="アップロード中です…" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">CSVをアップロード中です。しばらくお待ちください。</Text>
          </div>
        </div>
      </Modal>
    </>
  );
};

export default DatasetImportPage;
