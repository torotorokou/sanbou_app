/**
 * DatasetImportPage - データセットインポート画面（骨組み）
 * 
 * 責務: レイアウト・配置のみ
 * ロジック: useDatabaseUploadVM に委譲
 * プレビュー: DatasetPreviewScreen に委譲
 */

import React, { useState } from 'react';
import { Typography, Col, Row, Button, Modal, Spin, Empty, Select, Space, Badge } from 'antd';
import styles from './DatasetImportPage.module.css';

import {
  SimpleUploadPanel,
  useDatasetImportVM,
} from '@features/database/dataset-import';
import { UploadGuide, toFileStates } from '@features/database/dataset-uploadguide';
import { getAllDatasets, collectTypesForDataset, type DatasetKey } from '@features/database/config';
import { UploadCalendar } from '@features/database/upload-calendar';

const { Text } = Typography;

const DatasetImportPage: React.FC = () => {
  // ===== データセット選択 =====
  const [datasetKey, setDatasetKey] = useState<DatasetKey>('shogun_flash');
  
  // データセット一覧
  const datasets = getAllDatasets();
  
  // ===== ViewModel（状態管理・ロジック） =====
  const activeTypes = collectTypesForDataset(datasetKey);
  const {
    panelFiles,
    canUpload,
    uploading,
    uploadSuccess,
    isProcessing,
    onPickFile,
    onRemoveFile,
    onToggleSkip,
    onResetAll,
    doUpload,
    resetUploadState,
  } = useDatasetImportVM({ activeTypes, datasetKey });

  // 進捗表示用
  const requiredFiles = panelFiles.filter(p => p.required);
  const validCount = requiredFiles.filter(p => p.status === 'valid' && p.file).length;

  // UploadGuide 用の FileState に変換
  const fileStates = toFileStates(panelFiles);

  return (
    <>
      {/* Contentのpaddingを差し引いた固定高 */}
      <Row className={styles.pageContainer}>
        {/* 左カラム：アップロード面 */}
        <Col span={10} className={styles.leftCol}>
          {/* データセット切替 + 進捗 */}
          <div style={{ marginBottom: 12 }}>
            <Space size={8} wrap>
              <Select<DatasetKey>
                value={datasetKey}
                onChange={setDatasetKey}
                options={datasets.map(d => ({ value: d.key, label: d.label }))}
                style={{ minWidth: 260 }}
              />
              <Badge
                status={validCount === requiredFiles.length && requiredFiles.length > 0 ? 'success' : 'processing'}
                text={`必須 ${validCount}/${requiredFiles.length}`}
              />
            </Space>
          </div>

          <UploadGuide datasetKey={datasetKey} files={fileStates} />

          {/* CSVアップロードタイトル（固定） */}
          <Typography.Title level={5} style={{ margin: '12px 0 8px 0', fontSize: 13 }}>
            📂 CSVアップロード
          </Typography.Title>

          {/* 左カラム内部スクロール */}
          <div className={styles.uploadSection}>
            {panelFiles.length === 0 ? (
              <Empty description="CSV定義が見つかりません" />
            ) : (
              <SimpleUploadPanel
                items={panelFiles}
                onPickFile={onPickFile}
                onRemoveFile={onRemoveFile}
                onToggleSkip={onToggleSkip}
                onResetAll={onResetAll}
                showTitle={false}
              />
            )}
          </div>

          <Space direction="vertical" style={{ width: '100%' }}>
            <Button
              type="primary"
              disabled={!canUpload || panelFiles.length === 0 || uploading || isProcessing}
              loading={uploading || isProcessing}
              onClick={doUpload}
              block
            >
              {uploadSuccess ? 'アップロード完了' : isProcessing ? '処理中...' : uploading ? 'アップロード中...' : 'アップロードする'}
            </Button>
            
            {uploadSuccess && (
              <Button
                onClick={resetUploadState}
                block
              >
                別のファイルをアップロード
              </Button>
            )}
          </Space>
          
          {!canUpload && panelFiles.length > 0 && !uploadSuccess && (
            <div className={styles.hint}>
              <Text type="secondary">
                ※ 必須CSVをすべて選択＆検証OKにするとアップロード可能
              </Text>
            </div>
          )}
        </Col>

        {/* 右カラム：カレンダー */}
        <Col span={14} className={styles.rightCol}>
          <UploadCalendar datasetKey={datasetKey} />
        </Col>
      </Row>

      {/* 送信中モーダル */}
      <Modal
        open={uploading}
        footer={null}
        closable={false}
        centered
        maskClosable={false}
        styles={{ mask: { backdropFilter: 'blur(2px)' } }}
      >
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">CSVをアップロード中です。しばらくお待ちください。</Text>
          </div>
        </div>
      </Modal>
    </>
  );
};

export default DatasetImportPage;
