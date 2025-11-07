import React, { useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Typography, Col, Row, Button, Modal, Spin, Tabs, Select, Space, Tag, Badge, Empty } from 'antd';
import { useResponsive } from '@/shared';

import {
  CsvUploadPanel,
  CsvPreviewCard,
  UploadInstructions,
  useCsvUploadHandler,
  useCsvUploadArea,
} from '@features/database';
// 開発用サンプルモデルを直接参照（実運用では '@features/database/model' に戻してください）
import { UPLOAD_CSV_DEFINITIONS, UPLOAD_CSV_TYPES, csvTypeColors } from '@features/database/model/sampleCsvModel';

const { Text } = Typography;

// ===== Layout constants =====
const CARD_GAP = 16;
const COLUMN_PADDING = 16;
const CARD_HEADER_HEIGHT = 48;
const TAB_BAR_HEIGHT_FALLBACK = 40;
const CARD_BODY_VERTICAL_PADDING = 8 * 2;

/** =========================================================
 * アップロード「種別」：3種類に切替
 * - 将軍_速報版：出荷一覧 / 受入一覧 / ヤード一覧
 * - 将軍_最終版：出荷一覧 / 受入一覧 / ヤード一覧
 * - マニフェスト：1次マニ / 2次マニ
 * ---------------------------------------------------------
 * ※ 既存の UPLOAD_CSV_DEFINITIONS が持つ label / bundle|group|dataset を優先し、
 *    見つからない場合は label のキーワードで推定して紐づけます。
 * =======================================================*/
type DatasetKey = 'shogun_flash' | 'shogun_final' | 'manifest';
type DatasetSpec = { key: DatasetKey; label: string };
const DATASETS: DatasetSpec[] = [
  { key: 'shogun_flash', label: '将軍_速報版' },
  { key: 'shogun_final', label: '将軍_最終版' },
  { key: 'manifest',     label: 'マニフェスト（1次・2次）' },
];

const getGroupDecl = (def: any): string | null =>
  (def?.bundle || def?.group || def?.dataset || null) as string | null;

const norm = (s: string) => s.toLowerCase();

/** datasetごとの “想定カテゴリ” とラベル判定関数 */
const CATEGORY_ORDER_BY_DATASET: Record<DatasetKey, string[]> = {
  shogun_flash: ['出荷', '受入', 'ヤード'],
  shogun_final: ['出荷', '受入', 'ヤード'],
  manifest: ['1次', '2次'],
};
const hasAny = (label: string, list: string[]) => list.some((kw) => label.includes(kw));

/** label から dataset を推定するヘルパ */
function isBelongToDatasetByLabel(dataset: DatasetKey, label: string): boolean {
  const l = label.toLowerCase();
  if (dataset === 'shogun_flash') return (l.includes('将軍') || l.includes('shogun')) && (l.includes('速報') || l.includes('flash'));
  if (dataset === 'shogun_final') return (l.includes('将軍') || l.includes('shogun')) && (l.includes('最終') || l.includes('final'));
  if (dataset === 'manifest')     return l.includes('マニ') || l.includes('マニフェスト') || l.includes('manifest');
  return false;
}

/** label がどの“カテゴリ”かを判定（datasetごとに異なるキーワードで） */
function categoryOfLabel(dataset: DatasetKey, label: string): string | null {
  const l = label;
  if (dataset === 'shogun_flash' || dataset === 'shogun_final') {
    if (l.includes('出荷')) return '出荷';
    if (l.includes('受入') || l.includes('受け入れ')) return '受入';
    if (l.includes('ヤード')) return 'ヤード';
    return null;
  }
  if (dataset === 'manifest') {
    if (hasAny(l, ['1次', '一次', 'primary'])) return '1次';
    if (hasAny(l, ['2次', '二次', 'secondary'])) return '2次';
    return null;
  }
  return null;
}

/** dataset のアクティブ type キーを収集（定義 → ラベル推定の順で） */
function collectTypesForDataset(dataset: DatasetKey): string[] {
  const decl = (UPLOAD_CSV_TYPES as string[]).filter((t) => {
    const def: any = (UPLOAD_CSV_DEFINITIONS as any)[t];
    const g = getGroupDecl(def);
    return g ? norm(String(g)) === dataset : false;
  });
  const byLabel = (UPLOAD_CSV_TYPES as string[]).filter((t) => {
    const def: any = (UPLOAD_CSV_DEFINITIONS as any)[t];
    const label = def?.label ?? t;
    return isBelongToDatasetByLabel(dataset, label);
  });

  // ユニーク化
  const pool = Array.from(new Set([...decl, ...byLabel]));

  // “期待カテゴリ順”に並べ替え（見つからないカテゴリは後ろ）
  const categories = CATEGORY_ORDER_BY_DATASET[dataset];
  const orderKey = (typeKey: string) => {
    const label: string = ((UPLOAD_CSV_DEFINITIONS as any)[typeKey]?.label ?? typeKey) as string;
    const cat = categoryOfLabel(dataset, label) ?? 'zzz';
    const idx = categories.indexOf(cat);
    return idx >= 0 ? idx : 9;
  };
  return pool.sort((a, b) => orderKey(a) - orderKey(b));
}

/** 全アクティブタイプを必須扱い（この種別では全てが揃って初回フロー成立、という前提） */
function requiredTypesForDataset(dataset: DatasetKey, activeTypes: string[]): string[] {
  return activeTypes;
}

// 背景に対して読める文字色
function readableTextColor(bg: string) {
  try {
    const c = bg.replace('#', '');
    const r = parseInt(c.substring(0, 2), 16);
    const g = parseInt(c.substring(2, 4), 16);
    const b = parseInt(c.substring(4, 6), 16);
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.6 ? '#111827' : '#ffffff';
  } catch {
    return '#ffffff';
  }
}

const UploadDatabasePage: React.FC = () => {
  const { height } = useResponsive();

  // ===== 種別切替（3種類） =====
  const [datasetKey, setDatasetKey] = useState<DatasetKey>('shogun_flash');
  const datasetSpec = useMemo(() => DATASETS.find((d) => d.key === datasetKey)!, [datasetKey]);
  const activeTypes = useMemo(() => collectTypesForDataset(datasetSpec.key), [datasetSpec.key]);

  const {
    files,
    validationResults,
    csvPreviews,
    handleCsvFile,
    removeCsvFile,
  } = useCsvUploadArea();

  // 左パネル＆アップロード対象は “activeTypes のみ”
  const panelFiles = useMemo(() => activeTypes.map((type) => ({
    label: (UPLOAD_CSV_DEFINITIONS as any)[type]?.label ?? type,
    file: (files as any)[type] as File | null,
    required: true, // この種別では全ファイル必須扱い
    onChange: (f: File | null) => f && handleCsvFile((UPLOAD_CSV_DEFINITIONS as any)[type]?.label ?? type, f),
    validationResult: (
      (validationResults as any)[type] === 'valid'
        ? 'ok'
        : (validationResults as any)[type] === 'invalid'
        ? 'ng'
        : 'unknown'
    ) as 'ok' | 'ng' | 'unknown',
    onRemove: () => removeCsvFile(type),
  })), [activeTypes, files, validationResults, handleCsvFile, removeCsvFile]);

  const filesForActive = useMemo(() => {
    const entries = activeTypes.map((t) => [t, (files as any)[t] ?? null]);
    return Object.fromEntries(entries) as Record<string, File | null>;
  }, [files, activeTypes]);

  // このページでは “選択中種別のファイルだけ”を送る
  const { uploading, handleUpload } = useCsvUploadHandler(filesForActive);

  // ===== canUpload（選択中種別の必須が全て valid & 選択済み） =====
  const canUploadForDataset = useMemo(() => {
    const requiredTypes = requiredTypesForDataset(datasetKey, activeTypes);
    if (requiredTypes.length === 0) return false;
    return requiredTypes.every((t) => {
      const v = (validationResults as any)[t];
      const f = (files as any)[t];
      return !!f && v === 'valid';
    });
  }, [datasetKey, activeTypes, validationResults, files]);

  // ===== 右プレビューの高さ算出 =====
  const rowRef = useRef<HTMLDivElement | null>(null);
  const tabsRef = useRef<HTMLDivElement | null>(null);
  const [cardHeight, setCardHeight] = useState<number>(300);
  const [tableBodyHeight, setTableBodyHeight] = useState<number>(200);
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
      const tbh = Math.max(80, ch - CARD_HEADER_HEIGHT - CARD_BODY_VERTICAL_PADDING - 8);
      setTableBodyHeight(tbh);
    };
    const raf = requestAnimationFrame(calc);
    const onResize = () => calc();
    window.addEventListener('resize', onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
    };
  }, [height, tabBarHeight]);

  // 進捗バッジ（選択中データセット内の必須タイプの充足率）
  const requiredTypes = requiredTypesForDataset(datasetKey, activeTypes);
  const requiredDone = requiredTypes.filter((t) => (validationResults as any)[t] === 'valid' && (files as any)[t]).length;

  return (
    <>
      {/* Contentのpaddingを差し引いた固定高 */}
      <Row
        ref={rowRef}
        style={{
          height: 'calc(100dvh - (var(--page-padding, 0px) * 2))',
          minHeight: 600,
          overflow: 'hidden',
        }}
      >
        {/* 左カラム：種別切替 + アップロード面 */}
        <Col
          span={8}
          style={{
            padding: 16,
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* ヘッダー（3種切替 + 状態） */}
          <div style={{ marginBottom: 12 }}>
            <Space size={8} wrap>
              <Select<DatasetKey>
                value={datasetKey}
                onChange={setDatasetKey}
                options={DATASETS.map((d) => ({ value: d.key, label: d.label }))}
                style={{ minWidth: 260 }}
              />
              <Tag bordered={false} color="default">
                対象ファイル: {activeTypes.length} 件
              </Tag>
              <Badge
                status={requiredDone === requiredTypes.length && requiredTypes.length > 0 ? 'success' : 'processing'}
                text={`必須 ${requiredDone}/${requiredTypes.length}`}
              />
            </Space>
          </div>

          <UploadInstructions />

          {/* 左カラム内部スクロール */}
          <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', paddingRight: 4 }}>
            {activeTypes.length === 0 ? (
              <Empty description="この種別に対応するCSV定義が見つかりません（modelの定義を確認してください）" />
            ) : (
              <CsvUploadPanel
                upload={{
                  files: panelFiles,
                  makeUploadProps: (label) => ({
                    accept: '.csv',
                    showUploadList: false,
                    beforeUpload: (file: File) => {
                      handleCsvFile(label, file);
                      return false;
                    },
                  }),
                }}
              />
            )}
          </div>

          <Button
            type="primary"
            disabled={!canUploadForDataset || activeTypes.length === 0}
            onClick={handleUpload}
            style={{ marginTop: 24, width: '100%' }}
          >
            アップロードする
          </Button>
          {!canUploadForDataset && activeTypes.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">
                ※ 選択中の種別で「必須CSVをすべて選択＆検証OK」にするとアップロード可能です。
              </Text>
            </div>
          )}
        </Col>

        {/* 右カラム：プレビュー（選択中種別のファイルだけタブで表示） */}
        <Col
          span={16}
          style={{
            padding: 16,
            display: 'flex',
            flexDirection: 'column',
            gap: CARD_GAP,
            height: '100%',
            overflow: 'hidden',
          }}
        >
          {activeTypes.length === 0 ? (
            <div style={{ flex: 1, display: 'grid', placeItems: 'center' }}>
              <Empty description="プレビュー対象のCSVがありません" />
            </div>
          ) : (
            <Tabs
              key={datasetKey} // 種別切替で初期アクティブをリセット
              defaultActiveKey={activeTypes[0]}
              style={{ height: '100%' }}
              renderTabBar={(props, DefaultTabBar) => (
                <div ref={(el) => { tabsRef.current = el; }}>
                  <DefaultTabBar {...props} />
                </div>
              )}
              items={activeTypes.map((type) => {
                const label = (UPLOAD_CSV_DEFINITIONS as any)[type]?.label ?? type;
                const bg = (csvTypeColors as any)[type] || '#777';
                const fg = readableTextColor(bg);
                return ({
                  key: type,
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
                      {label}
                    </div>
                  ),
                  children: (
                    <div style={{ height: cardHeight, overflow: 'hidden' }}>
                      <CsvPreviewCard
                        type={type}
                        csvPreview={(csvPreviews as any)[type]}
                        validationResult={(validationResults as any)[type]}
                        cardHeight={cardHeight}
                        tableBodyHeight={tableBodyHeight}
                        backgroundColor={bg}
                      />
                    </div>
                  ),
                });
              })}
            />
          )}
        </Col>
      </Row>

      {/* 送信中 */}
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

export default UploadDatabasePage;
