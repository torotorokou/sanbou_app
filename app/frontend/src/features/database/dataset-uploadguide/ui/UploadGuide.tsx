/**
 * UploadGuide - データセットアップロードガイド UI
 * 
 * データセット別の必要ファイル・注意事項・手順を表示
 * Alert で未完了・エラーを強調
 */

import React, { useEffect } from 'react';
import { Collapse, List, Tag, Typography } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import type { FileState } from '../model/types';
import { DATASET_RULES } from '@/features/csv-validation/model/rules';
import { notifyError } from '@features/notification';
import type { DatasetKey } from '@features/database/config';

const { Text } = Typography;

export interface UploadGuideProps {
  /** 現在選択されているデータセット */
  datasetKey: DatasetKey;
  /** アップロード対象のファイル状態リスト */
  files: FileState[];
}

export const UploadGuide: React.FC<UploadGuideProps> = ({ datasetKey, files }) => {
  const rule = DATASET_RULES?.[datasetKey];
  const reqList = rule?.requiredCsv ?? [];
  const reqTotal = reqList.length;

  // 未完了（必須 & valid でない）
  const missing = files.filter((f) => f.required && f.status !== 'valid');
  // エラー（invalid）
  const invalid = files.filter((f) => f.status === 'invalid');

  // 検証エラーがある場合、右上に通知を表示
  useEffect(() => {
    if (invalid.length > 0) {
      const errorFiles = invalid.map((f) => f.label).join('、');
      // プロジェクト共通の通知機構に差し替え
      notifyError('検証エラー', `${errorFiles} に問題があります`);
    }
  }, [invalid.length]); // invalid.length が変わった場合のみ再実行

  return (
    <div style={{ marginBottom: 16 }}>
      {/* 状況の要約（未完了） - 折り畳み式 */}
      {missing.length > 0 && (
        <Collapse
          defaultActiveKey={[]}
          style={{
            marginBottom: 8,
            backgroundColor: '#fffbe6',
            border: '1px solid #ffe58f',
            borderRadius: 6,
          }}
          expandIconPosition="start"
          items={[
            {
              key: 'missing',
              label: (
                <span style={{ fontWeight: 'bold', color: '#faad14' }}>
                  ⚠️ 未完了: 必須 {missing.length}/{reqTotal}
                </span>
              ),
              children: (
                <List
                  size="small"
                  dataSource={missing}
                  renderItem={(it) => (
                    <List.Item style={{ paddingLeft: 0 }}>
                      <Tag color="red">{it.label}</Tag>
                      <Text type="secondary">を選択/検証OKにしてください</Text>
                    </List.Item>
                  )}
                />
              ),
            },
          ]}
        />
      )}


      {/* 手順・必要ファイル・注意事項（Collapse） */}
      <Collapse
        defaultActiveKey={[]}
        style={{
          backgroundColor: '#f6ffed',
          border: '1px solid #b7eb8f',
          borderRadius: 6,
        }}
        expandIconPosition="start"
        items={[
          {
            key: 'howto',
            label: (
              <span style={{ fontWeight: 'bold' }}>
                <InfoCircleOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                アップロード手順
              </span>
            ),
            children: (
              <ol style={{ margin: 0, paddingLeft: 20, lineHeight: 1.8 }}>
                <li>
                  データセットを選択（現在：<strong>{datasetKey}</strong>）
                </li>
                <li>各カードに CSV をドラッグ＆ドロップ（またはクリック）</li>
                <li>自動検証（ヘッダ/型）を待つ</li>
                <li>プレビューで内容を確認</li>
                <li>「アップロードする」を押下</li>
              </ol>
            ),
          },
          {
            key: 'req',
            label: (
              <span style={{ fontWeight: 'bold' }}>
                <InfoCircleOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                必要ファイル
              </span>
            ),
            children: (
              <List
                size="small"
                dataSource={reqList}
                renderItem={(r) => (
                  <List.Item style={{ paddingLeft: 0 }}>
                    <Tag color="blue">{r.label}</Tag>
                    <Text type="secondary">（必須）</Text>
                    {Array.isArray(r.filenameHints) && r.filenameHints.length > 0 && (
                      <span style={{ marginLeft: 8, fontSize: 12, color: '#888' }}>
                        受入ファイル名例: {r.filenameHints.join(' / ')}
                      </span>
                    )}
                    {r.sampleUrl && (
                      <a
                        style={{ marginLeft: 8, fontSize: 12 }}
                        href={r.sampleUrl}
                        target="_blank"
                        rel="noreferrer"
                      >
                        サンプル
                      </a>
                    )}
                  </List.Item>
                )}
              />
            ),
          },
          ...(Array.isArray(rule?.globalNotes) && rule.globalNotes.length > 0
            ? [
                {
                  key: 'notes',
                  label: (
                    <span style={{ fontWeight: 'bold' }}>
                      <InfoCircleOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                      注意事項
                    </span>
                  ),
                  children: (
                    <List
                      size="small"
                      dataSource={rule.globalNotes}
                      renderItem={(note) => (
                        <List.Item style={{ paddingLeft: 0 }}>
                          <Text>{note}</Text>
                        </List.Item>
                      )}
                    />
                  ),
                },
              ]
            : []),
        ]}
      />
    </div>
  );
};
