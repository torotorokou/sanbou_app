import { useMemo } from 'react';

/**
 * レイアウトとスタイリングのロジックを管理するフック
 * 
 * 🎯 目的：
 * - インラインスタイルの複雑性を分離
 * - レスポンシブデザインの一元管理
 * - デザインシステムの整合性を保つ
 */
export const useReportLayoutStyles = () => {
  const styles = useMemo(() => ({
    container: {
      padding: 24,
    },
    mainLayout: {
      display: 'flex',
      gap: 24,
      alignItems: 'stretch',
      flexGrow: 1,
      marginTop: 16,
      minHeight: '80vh',
    },
    leftPanel: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: 16,
      width: 380,
      flexShrink: 0,
    },
    centerPanel: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      width: 100,
      flexShrink: 0,
    },
    rightPanel: {
      flex: 1,
      minWidth: 600,
      height: '80vh',
      display: 'flex',
      flexDirection: 'column' as const,
    },
    previewContainer: {
      display: 'flex',
      flex: 1,
      gap: 16,
      alignItems: 'center',
    },
    previewArea: {
      flex: 1,
      height: '100%',
      border: '1px solid #ccc',
      borderRadius: 8,
      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
      background: '#fafafa',
      overflow: 'hidden',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
    },
    downloadSection: {
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      width: 120,
      gap: 8,
    },
    sampleThumbnail: {
      className: 'sample-thumbnail',
    },
  }), []);

  return styles;
};
