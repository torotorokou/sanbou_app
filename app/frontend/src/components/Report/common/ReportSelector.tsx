// /components/Report/common/ReportSelector.tsx
import React from 'react';
import { Select } from 'antd';

import {
    REPORT_OPTIONS,
    PAGE_REPORT_GROUPS,
    type PageGroupKey
} from '@/constants/reportConfig';

type ReportSelectorProps = {
    reportKey: string;
    onChange: (key: string) => void;
    /** ページ別帳票グループ指定。未指定時は全帳票を表示 */
    pageGroup?: PageGroupKey;
    /** カスタムオプション指定（pageGroupより優先） */
    customOptions?: ReadonlyArray<{ readonly value: string; readonly label: string }>;
};

/**
 * 帳票選択セレクトボックス - ページ別表示対応版
 * 
 * 🎯 リファクタリングの改善点：
 * - ページごとに表示する帳票を制御可能
 * - 保守性の高い設定駆動型アーキテクチャ
 * - 既存のコンポーネントとの互換性を維持
 */
const ReportSelector: React.FC<ReportSelectorProps> = ({
    reportKey,
    onChange,
    pageGroup,
    customOptions,
}) => {
    // 表示オプションの決定ロジック
    const getDisplayOptions = () => {
        // カスタムオプションが最優先
        if (customOptions) {
            return customOptions;
        }

        // ページグループ指定がある場合
        if (pageGroup && PAGE_REPORT_GROUPS[pageGroup]) {
            return PAGE_REPORT_GROUPS[pageGroup];
        }

        // デフォルトは全帳票
        return REPORT_OPTIONS;
    };

    const displayOptions = getDisplayOptions();

    return (
        <Select
            value={reportKey}
            onChange={onChange}
            options={[...displayOptions]}
            size='large'
            style={{
                width: 240,
                fontWeight: 500,
                borderRadius: 12,
                boxShadow: '0 2px 6px rgba(0,0,0,0.06)',
            }}
        />
    );
};

export default ReportSelector;
