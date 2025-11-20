/**
 * shared/ui/styles.ts
 * 売上ピボット機能の共通スタイル定義
 */

export const salesPivotStyles = `
  .app-header {
    position: relative;
    padding: 12px 0 4px;
  }

  .app-title {
    text-align: center;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin: 0;
  }

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

  .accent-card {
    border-left: 4px solid #23780410;
    overflow: hidden;
  }

  .accent-primary {
    border-left-color: #237804;
  }

  .accent-secondary {
    border-left-color: #52c41a;
  }

  .accent-gold {
    border-left-color: #faad14;
  }

  .card-section-header {
    font-weight: 600;
    padding: 6px 10px;
    margin-bottom: 12px;
    border-radius: 6px;
    background: #f3fff4;
    border: 1px solid #e6f7e6;
  }

  .card-subtitle {
    color: rgba(0, 0, 0, 0.55);
    margin-bottom: 6px;
    font-size: 12px;
  }

  .mini-bar-bg {
    flex: 1;
    height: 6px;
    background: #f6f7fb;
    border-radius: 4px;
    overflow: hidden;
  }

  .mini-bar {
    height: 100%;
  }

  .mini-bar-blue {
    background: #237804;
  }

  .mini-bar-green {
    background: #52c41a;
  }

  .mini-bar-gold {
    background: #faad14;
  }

  .zebra-even {
    background: #ffffff;
  }

  .zebra-odd {
    background: #fbfcfe;
  }

  .ant-table-tbody > tr:hover > td {
    background: #f6fff4 !important;
  }

  .ant-table-header {
    box-shadow: inset 0 -1px 0 #f0f0f0;
  }

  .summary-tags {
    font-size: 14px;
  }

  .summary-tags .ant-tag {
    font-size: 14px;
    padding: 0 10px;
  }
`;
