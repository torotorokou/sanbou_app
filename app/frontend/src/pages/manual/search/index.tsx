/**
 * マニュアル検索ページ
 * FSD: ページ層は組み立てのみ
 */
import React, { useCallback, useState } from 'react';
import styles from './SearchPage.module.css';
import { useManualSearch } from '@features/manual';
import { ManualSearchBox } from '@features/manual';
import { ManualResultList } from '@features/manual';
import { ManualViewer } from '@features/manual';
import { useManualDoc } from '@features/manual';
import type { ManualDoc } from '@features/manual';

const ManualSearchPage: React.FC = () => {
  const { setQuery, data, loading, error } = useManualSearch({ q: '' });
  const { getUrl } = useManualDoc();
  const [selectedDoc, setSelectedDoc] = useState<ManualDoc | null>(null);

  const handleSearch = useCallback(
    (searchQuery: { q: string; category?: string }) => {
      setQuery(searchQuery);
      setSelectedDoc(null);
    },
    [setQuery]
  );

  const handleSelectDoc = useCallback((doc: ManualDoc) => {
    setSelectedDoc(doc);
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedDoc(null);
  }, []);

  return (
    <div className={styles.pageContainer}>
      <header className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>マニュアル検索</h1>
        <p className={styles.pageDescription}>BFF-based Manual API Demo</p>
      </header>

      <main className={styles.mainContent}>
        <div className={styles.gridContainer}>
          {/* 左パネル: 検索と結果 */}
          <div className={styles.searchPanel}>
            <div className={styles.searchBox}>
              <ManualSearchBox onSearch={handleSearch} isLoading={loading} />
            </div>

            <div className={styles.resultList}>
              {error ? (
                <div className={styles.error}>
                  <p>エラー: {error.message}</p>
                </div>
              ) : (
                <>
                  {data && data.items.length > 0 && (
                    <div className={styles.resultCount}>
                      <p>{data.total || 0} 件の結果</p>
                    </div>
                  )}
                  <ManualResultList
                    results={data?.items || []}
                    onSelect={handleSelectDoc}
                    isLoading={loading}
                  />
                </>
              )}
            </div>
          </div>

          {/* 右パネル: ドキュメントビューア */}
          <div className={styles.viewerPanel}>
            {selectedDoc ? (
              <div className={styles.viewerContainer}>
                <div className={styles.viewerHeader}>
                  <button
                    onClick={handleClearSelection}
                    className={styles.closeButton}
                    aria-label="閉じる"
                  >
                    ✕
                  </button>
                  <span className={styles.viewerTitle}>ドキュメントプレビュー</span>
                </div>
                <div className={styles.viewerContent}>
                  <ManualViewer
                    src={getUrl(selectedDoc.docId, selectedDoc.title)}
                    title={selectedDoc.title}
                    className={styles.viewer}
                  />
                </div>
              </div>
            ) : (
              <div className={styles.emptyViewer}>
                <div className={styles.emptyContent}>
                  <div className={styles.emptyIcon}>📄</div>
                  <p className={styles.emptyText}>ドキュメントを選択してください</p>
                  <p className={styles.emptyHint}>
                    検索結果からドキュメントをクリックすると、
                    <br />
                    ここにプレビューが表示されます
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default ManualSearchPage;
