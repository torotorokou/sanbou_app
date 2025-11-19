// UI component: Confirmation table for transport vendor selections
import React from 'react';
import type { InteractiveItem } from '@features/report/shared/types/interactive.types';

interface SelectionState {
    index: number;
    label: string;
}

export interface TransportConfirmationTableProps {
    items: InteractiveItem[];
    selections: Record<string, SelectionState>;
}

/**
 * 選択内容確認用テーブル
 */
export const TransportConfirmationTable: React.FC<TransportConfirmationTableProps> = ({
    items,
    selections,
}) => {
    return (
        <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 2px' }}>
            <thead>
                <tr style={{ background: '#fafafa' }}>
                    <th
                        style={{
                            width: 72,
                            textAlign: 'left',
                            padding: '6px 8px',
                            fontSize: 13,
                            borderBottom: '1px solid #eee',
                        }}
                    >
                        No
                    </th>
                    <th
                        style={{
                            textAlign: 'left',
                            padding: '6px 8px',
                            fontSize: 14,
                            borderBottom: '1px solid #eee',
                        }}
                    >
                        処分業者
                    </th>
                    <th
                        style={{
                            textAlign: 'left',
                            padding: '6px 8px',
                            fontSize: 14,
                            borderBottom: '1px solid #eee',
                        }}
                    >
                        商品名
                    </th>
                    <th
                        style={{
                            textAlign: 'left',
                            padding: '6px 8px',
                            fontSize: 14,
                            borderBottom: '1px solid #eee',
                        }}
                    >
                        備考
                    </th>
                    <th
                        style={{
                            width: 160,
                            textAlign: 'left',
                            padding: '6px 8px',
                            fontSize: 14,
                            borderBottom: '1px solid #eee',
                        }}
                    >
                        運搬業者
                    </th>
                </tr>
            </thead>
            <tbody>
                {items.map((item, idx) => {
                    const bgColor = idx % 2 === 0 ? '#f5fbff' : '#fffaf0';
                    const borderColor = idx % 2 === 0 ? '#e6f7ff' : '#fff2cc';
                    return (
                        <tr key={item.id} style={{ background: bgColor }}>
                            <td
                                style={{
                                    padding: '6px',
                                    border: `1px solid ${borderColor}`,
                                    borderRadius: 6,
                                    verticalAlign: 'top',
                                    fontSize: 14,
                                    textAlign: 'center',
                                    width: 72,
                                }}
                            >
                                {idx + 1}
                            </td>
                            <td
                                style={{
                                    padding: '6px',
                                    border: `1px solid ${borderColor}`,
                                    borderRadius: 6,
                                    verticalAlign: 'top',
                                    fontSize: 15,
                                }}
                            >
                                {item.processor_name}
                            </td>
                            <td
                                style={{
                                    padding: '6px',
                                    border: `1px solid ${borderColor}`,
                                    borderRadius: 6,
                                    verticalAlign: 'top',
                                    fontSize: 14,
                                }}
                            >
                                {item.product_name}
                            </td>
                            <td
                                style={{
                                    padding: '6px',
                                    border: `1px solid ${borderColor}`,
                                    borderRadius: 6,
                                    verticalAlign: 'top',
                                    fontSize: 12,
                                    color: '#444',
                                }}
                            >
                                {item.note ?? '（なし）'}
                            </td>
                            <td
                                style={{
                                    padding: '6px',
                                    border: `1px solid ${borderColor}`,
                                    borderRadius: 6,
                                    verticalAlign: 'top',
                                    fontSize: 13,
                                    width: 160,
                                }}
                            >
                                {selections[item.id]?.label || '未選択'}
                            </td>
                        </tr>
                    );
                })}
            </tbody>
        </table>
    );
};
