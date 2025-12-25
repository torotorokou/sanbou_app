/**
 * Analysis Action Buttons Component
 *
 * 分析実行・CSVダウンロードボタン
 */

import React from 'react';
import { Button } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';

type Props = {
  onAnalyze: () => void;
  onDownload: () => void;
  isAnalyzeDisabled: boolean;
  isDownloadDisabled: boolean;
};

/**
 * 分析アクションボタン群
 *
 * 分析実行とCSVダウンロードボタンを提供
 */
const AnalysisActionButtons: React.FC<Props> = ({
  onAnalyze,
  onDownload,
  isAnalyzeDisabled,
  isDownloadDisabled,
}) => (
  <>
    <Button
      type="primary"
      size="large"
      block
      disabled={isAnalyzeDisabled}
      onClick={onAnalyze}
      style={{
        fontWeight: 600,
        letterSpacing: 1,
        marginBottom: 16,
        height: 48,
      }}
    >
      分析する
    </Button>

    <Button
      type="default"
      size="large"
      block
      disabled={isDownloadDisabled}
      onClick={onDownload}
      icon={<DownloadOutlined />}
      style={{
        fontWeight: 600,
        letterSpacing: 1,
        height: 48,
        borderColor: '#f43f5e',
        color: isDownloadDisabled ? undefined : '#f43f5e',
      }}
    >
      CSVダウンロード
    </Button>
  </>
);

export default AnalysisActionButtons;
