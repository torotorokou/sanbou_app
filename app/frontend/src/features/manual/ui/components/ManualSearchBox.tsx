/**
 * ManualSearchBox Component
 * マニュアル検索入力フォーム
 */

import React, { memo, useState } from "react";
import type { ManualSearchQuery } from "../../domain/types/manual.types";

interface ManualSearchBoxProps {
  onSearch: (query: ManualSearchQuery) => void;
  isLoading?: boolean;
}

export const ManualSearchBox = memo(
  ({ onSearch, isLoading = false }: ManualSearchBoxProps) => {
    const [keyword, setKeyword] = useState("");
    const [category, setCategory] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      onSearch({ q: keyword, category: category || undefined });
    };

    return (
      <form onSubmit={handleSubmit} className="manual-search-box space-y-4">
        <div>
          <label
            htmlFor="keyword"
            className="block text-sm font-medium text-gray-700"
          >
            キーワード
          </label>
          <input
            id="keyword"
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="検索キーワードを入力"
            disabled={isLoading}
          />
        </div>

        <div>
          <label
            htmlFor="category"
            className="block text-sm font-medium text-gray-700"
          >
            カテゴリ (オプション)
          </label>
          <input
            id="category"
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="カテゴリを指定"
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !keyword}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isLoading ? "検索中..." : "検索"}
        </button>
      </form>
    );
  },
);

ManualSearchBox.displayName = "ManualSearchBox";
