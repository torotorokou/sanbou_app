/**
 * header/ui/SalesPivotHeader.tsx
 * ヘッダーUI（タイトル + CSV出力Dropdownボタン）
 */

import React from 'react';
import { Typography, Tooltip, Button, Dropdown, Switch, Select, Space } from 'antd';
import type { MenuProps } from 'antd';
import { DownloadOutlined, DownOutlined } from '@ant-design/icons';
import type { ExportOptions, Mode } from '../../shared/model/types';
import { axisLabel } from '../../shared/model/metrics';

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
          <Tooltip title="営業が未選択のためCSV出力できません">
            <Button icon={<DownloadOutlined />} type="default" disabled>
              CSV出力
            </Button>
          </Tooltip>
        ) : (
          <Tooltip
            title={`出力：選択営業 × ${axisLabel(baseAx)}${
              exportOptions.addAxisB ? ` × ${axisLabel(axB)}` : ''
            }${exportOptions.addAxisC ? ` × ${axisLabel(axC)}` : ''}（期間：${periodLabel}、0実績は${
              exportOptions.excludeZero ? '除外' : '含む'
            }、${exportOptions.splitBy === 'rep' ? '営業別分割' : '単一ファイル'}）`}
          >
            <Dropdown.Button
              type="default"
              icon={<DownloadOutlined />}
              overlayStyle={{ width: 380 }}
              menu={{ items: exportMenu }}
              onClick={handleExportClick}
              placement="bottomRight"
              trigger={['click']}
              buttonsRender={([left, right]) => [
                left,
                React.isValidElement(right) ? React.cloneElement(right, { icon: <DownOutlined /> }) : right,
              ]}
            >
              CSV出力
            </Dropdown.Button>
          </Tooltip>
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
