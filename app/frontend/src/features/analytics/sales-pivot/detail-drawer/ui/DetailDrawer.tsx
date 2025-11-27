/**
 * detail-drawer/ui/DetailDrawer.tsx
 * 詳細明細行表示用Drawer
 * 
 * PivotDrawerの行をクリックしたときに開き、
 * 最後の軸に応じて「明細行レベル」または「伝票単位サマリ」を表示
 */

import React from 'react';
import { Drawer, Table, Typography, Spin, Empty } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { DetailLine, DetailMode, CategoryKind } from '../../shared/model/types';

const { Title, Text } = Typography;

interface DetailDrawerProps {
  open: boolean;
  loading: boolean;
  mode: DetailMode | null;
  rows: DetailLine[];
  totalCount: number;
  title: string;
  categoryKind: CategoryKind;
  onClose: () => void;
}

/**
 * 金額フォーマット（3桁カンマ区切り）
 */
const formatAmount = (value: number | null | undefined): string => {
  if (value == null) return '-';
  return value.toLocaleString('ja-JP', { maximumFractionDigits: 0 });
};

/**
 * 数量フォーマット（小数点2桁）
 */
const formatQty = (value: number | null | undefined): string => {
  if (value == null) return '-';
  return value.toLocaleString('ja-JP', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

/**
 * 単価フォーマット（小数点2桁）
 */
const formatUnitPrice = (value: number | null | undefined): string => {
  if (value == null) return '-';
  return value.toLocaleString('ja-JP', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

export const DetailDrawer: React.FC<DetailDrawerProps> = ({
  open,
  loading,
  mode,
  rows,
  totalCount,
  title,
  categoryKind,
  onClose,
}) => {
  // ページネーション状態管理
  const [currentPage, setCurrentPage] = React.useState<number>(1);
  const [pageSize, setPageSize] = React.useState<number>(50);

  // Drawer が開いたときにページをリセット
  React.useEffect(() => {
    if (open) {
      setCurrentPage(1);
    }
  }, [open]);

  // カラム定義（モード関係なく統一）
  const columns: ColumnsType<DetailLine> = React.useMemo(() => [
    {
      title: '日付',
      dataIndex: 'salesDate',
      key: 'salesDate',
      width: 110,
      fixed: 'left',
    },
    {
      title: '伝票No',
      dataIndex: 'slipNo',
      key: 'slipNo',
      width: 100,
      fixed: 'left',
    },
    {
      title: '営業名',
      dataIndex: 'repName',
      key: 'repName',
      width: 100,
      ellipsis: true,
    },
    {
      title: '顧客名',
      dataIndex: 'customerName',
      key: 'customerName',
      width: 200,
      ellipsis: true,
    },
    {
      title: '品目名',
      dataIndex: 'itemName',
      key: 'itemName',
      width: 200,
      ellipsis: true,
    },
    {
      title: '明細件数',
      dataIndex: 'lineCount',
      key: 'lineCount',
      width: 100,
      align: 'right',
      render: (value: number | null) => formatAmount(value ?? 1),
    },
    {
      title: '数量(kg)',
      dataIndex: 'qtyKg',
      key: 'qtyKg',
      width: 120,
      align: 'right',
      render: (value: number) => formatQty(value),
    },
    {
      title: '単価(円/kg)',
      dataIndex: 'unitPriceYenPerKg',
      key: 'unitPriceYenPerKg',
      width: 130,
      align: 'right',
      render: (value: number | null) => formatUnitPrice(value),
    },
    {
      title: '金額(円)',
      dataIndex: 'amountYen',
      key: 'amountYen',
      width: 140,
      align: 'right',
      render: (value: number) => formatAmount(value),
    },
  ], []);

  // モード表示ラベル
  const modeLabel = mode === 'item_lines' ? '明細行レベル' : mode === 'slip_summary' ? '伝票単位サマリ' : '';

  return (
    <Drawer
      title={
        <div>
          <Title level={4} style={{ margin: 0 }}>
            {title}
          </Title>
          <Text type="secondary">
            {modeLabel} | {categoryKind === 'waste' ? '廃棄物' : '有価物'}
          </Text>
        </div>
      }
      placement="right"
      width="80%"
      onClose={onClose}
      open={open}
      destroyOnClose
    >
      <Spin spinning={loading}>
        {rows.length === 0 && !loading ? (
          <Empty description="データがありません" />
        ) : (
          <>
            <div style={{ marginBottom: 16 }}>
              <Text strong>総件数: {(totalCount ?? rows.length).toLocaleString()} 件</Text>
            </div>
            <Table<DetailLine>
              columns={columns}
              dataSource={rows}
              rowKey={(record) => `${record.slipNo}-${record.itemId ?? 'sum'}`}
              pagination={{
                current: currentPage,
                pageSize: pageSize,
                total: totalCount ?? rows.length,
                showSizeChanger: true,
                pageSizeOptions: ['20', '50', '100', '200'],
                showTotal: (total) => `全 ${total.toLocaleString()} 件`,
                onChange: (page, size) => {
                  setCurrentPage(page);
                  if (size !== pageSize) {
                    setPageSize(size);
                    setCurrentPage(1); // ページサイズ変更時は1ページ目に戻る
                  }
                },
              }}
              scroll={{ x: 1200, y: 'calc(100vh - 300px)' }}
              size="small"
            />
          </>
        )}
      </Spin>
    </Drawer>
  );
};
