import React from 'react';
import ManualSearch from './ListPage';

// 既存の ManualSearch コンポーネントの UI を再利用する簡易ラッパー。
// 将来的に Manual 固有の子ページ（一覧 / カテゴリ / 詳細など）を分割する場合は
// このフォルダに新しいコンポーネントを追加してください。
const ManualList: React.FC = () => {
    return <ManualSearch />;
};

export default ManualList;
