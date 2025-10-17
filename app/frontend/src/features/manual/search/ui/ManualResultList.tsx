/**
 * ManualResultList Component
 * マニュアル検索結果リスト表示
 */

import React, { memo } from 'react';
import type { ManualDoc } from '../../shared/model/types';

interface ManualResultListProps {
  results: ManualDoc[];
  isLoading?: boolean;
  error?: Error | null;
  onSelect?: (doc: ManualDoc) => void;
}

export const ManualResultList = memo(({
  results,
  isLoading = false,
  error = null,
  onSelect
}: ManualResultListProps) => {
  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">検索中...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-700">
        エラー: {error.message}
      </div>
    );
  }

  if (results.length === 0) {
    return <div className="text-center py-8 text-gray-500">結果がありません</div>;
  }

  return (
    <ul className="manual-result-list space-y-2">
      {results.map((doc) => (
        <li
          key={doc.docId}
          className="border border-gray-200 rounded-md p-4 hover:bg-gray-50 cursor-pointer"
          onClick={() => onSelect?.(doc)}
        >
          <h3 className="font-semibold text-lg text-gray-900">{doc.title}</h3>
          {doc.category && (
            <span className="inline-block mt-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
              {doc.category}
            </span>
          )}
          {doc.tags && doc.tags.length > 0 && (
            <div className="mt-2 flex gap-1 flex-wrap">
              {doc.tags.map((tag) => (
                <span key={tag} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                  {tag}
                </span>
              ))}
            </div>
          )}
          <div className="mt-2 text-sm text-gray-600">
            {doc.mimeType} {doc.size && `• ${(doc.size / 1024).toFixed(1)} KB`}
          </div>
        </li>
      ))}
    </ul>
  );
});

ManualResultList.displayName = 'ManualResultList';
