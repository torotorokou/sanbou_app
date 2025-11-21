/**
 * header/ui/SalesPivotHeader.tsx
 * ヘッダーUI（タイトル + CSV出力Dropdownボタン）
 * 
 * 【概要】
 * 売上ピボット分析画面のヘッダー部分を表示するプレゼンテーショナルコンポーネント
 * 
 * 【責務】
 * 1. ページタイトルの表示
 * 2. CSV出力ボタンとオプションメニューの表示
 * 3. ユーザー操作の受付と親コンポーネントへの通知
 * 
 * 【機能】
 * - CSV出力オプション設定（Dropdownメニュー内）
 *   - 追加カラム選択（残りモード1, 2）
 *   - 0実績除外
 *   - 営業ごと分割出力
 * - CSV出力実行（Blobダウンロード）
 * 
 * 【使用例】
 * ```tsx
 * <SalesPivotHeader
 *   canExport={true}
 *   exportOptions={exportOptions}
 *   onExportOptionsChange={setExportOptions}
 *   onExport={handleExport}
 *   onExportSuccess={() => message.success('CSV出力完了')}
 *   onExportError={(err) => message.error('CSV出力失敗')}
 *   periodLabel="202511"
 *   baseAx="customer"
 *   axB="item"
 *   axC="date"
 * />
 * ```
 */

import React from 'react';
import { Typography, Button, Dropdown, Switch, Select, Space } from 'antd';
import type { MenuProps } from 'antd';
import { DownloadOutlined, DownOutlined } from '@ant-design/icons';
import type { ExportOptions, Mode } from '../../shared/model/types';
import { axisLabel } from '../../shared/model/metrics';

/**
 * SalesPivotHeader Props
 * 
 * @property canExport - CSV出力可能かどうか（営業選択有無で判定）
 * @property exportOptions - 現在のCSV出力オプション
 * @property onExportOptionsChange - 出力オプション変更時のコールバック
 * @property onExport - CSV出力実行時のコールバック
 * @property onExportSuccess - 出力成功時のコールバック（オプション）
 * @property onExportError - 出力失敗時のコールバック（オプション）
 * @property periodLabel - 期間ラベル（表示用、例: "202511" or "202501-202503"）
 * @property baseAx - 基準軸（現在のモード）
 * @property axB - 第2軸（残りモード1）
 * @property axC - 第3軸（残りモード2）
 */
interface SalesPivotHeaderProps {
  canExport: boolean;
  exportOptions: ExportOptions;
  onExportOptionsChange: (options: ExportOptions | ((prev: ExportOptions) => ExportOptions)) => void;
  onExport: () => Promise<void>;
  onExportSuccess?: () => void;
  onExportError?: (error: Error) => void;
  periodLabel: string;
  baseAx: Mode;
  axB: Mode;
  axC: Mode;
}

/**
 * ヘッダーコンポーネント
 * 
 * @description
 * タイトルとCSV出力機能を提供するヘッダーUI
 * Dropdown内でCSV出力オプションを設定可能
 */
export const SalesPivotHeader: React.FC<SalesPivotHeaderProps> = ({
  canExport,
  exportOptions,
  onExportOptionsChange,
  onExport,
  onExportSuccess,
  onExportError,
  periodLabel,
  baseAx,
  axB,
  axC,
}) => {
  // CSV出力メニュー
  const exportMenu: MenuProps['items'] = [
    { key: 'title', label: <b>出力条件</b> },
    { type: 'divider' },

    // 追加カラム：残りモード1
    {
      key: 'addB',
      label: (
        <div onClick={(e) => e.stopPropagation()}>
          <Space>
            <Switch
              size="small"
              checked={exportOptions.addAxisB}
              onChange={(v) => onExportOptionsChange((prev) => ({ ...prev, addAxisB: v }))}
            />
            <span>追加カラム：{axisLabel(axB)}</span>
          </Space>
        </div>
      ),
    },

    // 追加カラム：残りモード2
    {
      key: 'addC',
      label: (
        <div onClick={(e) => e.stopPropagation()}>
          <Space>
            <Switch
              size="small"
              checked={exportOptions.addAxisC}
              onChange={(v) => onExportOptionsChange((prev) => ({ ...prev, addAxisC: v }))}
            />
            <span>追加カラム：{axisLabel(axC)}</span>
          </Space>
        </div>
      ),
    },

    { type: 'divider' },

    // 0実績除外
    {
      key: 'opt-zero',
      label: (
        <Space onClick={(e) => e.stopPropagation()}>
          <Switch
            size="small"
            checked={exportOptions.excludeZero}
            onChange={(checked) => onExportOptionsChange((prev) => ({ ...prev, excludeZero: checked }))}
          />
          <span>0実績を除外する（Excel負荷対策）</span>
        </Space>
      ),
    },

    // 分割出力
    {
      key: 'opt-split',
      label: (
        <Space onClick={(e) => e.stopPropagation()}>
          <Select
            size="small"
            value={exportOptions.splitBy}
            onChange={(v: 'none' | 'rep') => onExportOptionsChange((prev) => ({ ...prev, splitBy: v }))}
            options={[
              { label: '分割しない', value: 'none' },
              { label: '営業ごとに分割', value: 'rep' },
            ]}
            style={{ width: 180 }}
          />
          <span>（Excel負荷対策）</span>
        </Space>
      ),
    },
  ];

  const handleExportClick = () => {
    onExport()
      .then(() => {
        onExportSuccess?.();
      })
      .catch((e) => {
        console.error(e);
        onExportError?.(e as Error);
      });
  };

  return (
    <div className="sales-tree-header">
      <Typography.Title level={3} className="sales-tree-title">
        <span className="sales-tree-title-accent">売上ツリー</span>
      </Typography.Title>
      <div className="sales-tree-header-actions">
        {!canExport ? (
          <Button 
            icon={<DownloadOutlined />} 
            type="default" 
            disabled
            title="営業が未選択のためCSV出力できません"
          >
            CSV出力
          </Button>
        ) : (
          <Space.Compact>
            <Button
              type="default"
              icon={<DownloadOutlined />}
              onClick={handleExportClick}
              title={`出力：選択営業 × ${axisLabel(baseAx)}${
                exportOptions.addAxisB ? ` × ${axisLabel(axB)}` : ''
              }${exportOptions.addAxisC ? ` × ${axisLabel(axC)}` : ''}（期間：${periodLabel}、0実績は${
                exportOptions.excludeZero ? '除外' : '含む'
              }、${exportOptions.splitBy === 'rep' ? '営業別分割' : '単一ファイル'}）`}
            >
              CSV出力
            </Button>
            <Dropdown
              menu={{ items: exportMenu }}
              placement="bottomRight"
              trigger={['click']}
            >
              <Button type="default" icon={<DownOutlined />} />
            </Dropdown>
          </Space.Compact>
        )}
      </div>

      {/* ヘッダースタイル */}
      <style>{`
        .app-header { position: relative; padding: 12px 0 4px; }
        .app-title { text-align: center; font-weight: 700; letter-spacing: 0.02em; margin: 0; }
        .app-title-accent { 
          display: inline-flex; 
          align-items: center; 
          gap: 10px; 
          padding-left: 8px; 
          color: #000; 
          font-weight: 700; 
          line-height: 1.2; 
          font-size: 1.05em; 
        }
        .app-title-accent::before { 
          content: ""; 
          display: inline-block; 
          width: 6px; 
          height: 22px; 
          background: #237804; 
          border-radius: 3px; 
        }
        .app-header-actions { 
          position: absolute; 
          right: 0; 
          top: 8px; 
          display: flex; 
          gap: 8px; 
        }
      `}</style>
    </div>
  );
};
