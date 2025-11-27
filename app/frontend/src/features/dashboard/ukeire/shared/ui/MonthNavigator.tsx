/**
 * MonthNavigator - 月ナビゲーションUI
 * 
 * 責務：
 * - タイトル表示（月表示含む）
 * - 月選択DatePicker
 * - 前月/翌月ボタン
 * - 今日バッジ表示
 * - モバイル/デスクトップレスポンシブ対応
 * 
 * 状態管理なし・純UIコンポーネント
 */

import React from "react";
import { Row, Col, Typography, DatePicker, Space, Badge, Button, Tooltip } from "antd";
import { LeftOutlined, RightOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import type { Dayjs } from "dayjs";

export type MonthNavigatorProps = {
  /** ページタイトル */
  title: string;
  /** 現在の月（YYYY-MM形式） */
  month: string | null;
  /** 月表示（日本語） */
  monthJP?: string;
  /** 今日バッジのテキスト */
  todayBadge?: string;
  /** モバイルレイアウトかどうか */
  isMobile?: boolean;
  /** 月変更時のコールバック */
  onMonthChange: (month: string) => void;
  /** 前月ボタン押下時のコールバック */
  onPrevMonth: () => void;
  /** 翌月ボタン押下時のコールバック */
  onNextMonth: () => void;
};

export const MonthNavigator: React.FC<MonthNavigatorProps> = ({
  title,
  month,
  monthJP,
  todayBadge,
  isMobile = false,
  onMonthChange,
  onPrevMonth,
  onNextMonth,
}) => {
  const handleDatePickerChange = (d: Dayjs | null, s: string | string[]) => {
    if (d && d.isValid && d.isValid() && typeof s === "string" && s) {
      onMonthChange(s);
    }
  };

  const controls = (
    <Space size={8} wrap>
      <Tooltip title="先月へ">
        <Button size="small" icon={<LeftOutlined />} onClick={onPrevMonth} />
      </Tooltip>
      <DatePicker
        picker="month"
        value={month ? dayjs(month, "YYYY-MM") : null}
        onChange={handleDatePickerChange}
        className="dashboard-month-picker"
        size="small"
      />
      <Tooltip title="翌月へ">
        <Button size="small" icon={<RightOutlined />} onClick={onNextMonth} />
      </Tooltip>
      {todayBadge && <Badge count={todayBadge} style={{ backgroundColor: "#1677ff" }} />}
    </Space>
  );

  if (isMobile) {
    return (
      <>
        <Row align="middle">
          <Col span={24} style={{ textAlign: "center" }}>
            <Typography.Title level={4} style={{ margin: 0 }}>
              {title}
            </Typography.Title>
          </Col>
        </Row>
        <Row>
          <Col span={24} style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
            {controls}
          </Col>
        </Row>
      </>
    );
  }

  return (
    <Row align="middle">
      <Col flex="1" />
      <Col flex="none" style={{ textAlign: "center" }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          {title}
          {monthJP && ` — ${monthJP}`}
        </Typography.Title>
      </Col>
      <Col flex="1" style={{ display: "flex", justifyContent: "flex-end" }}>
        {controls}
      </Col>
    </Row>
  );
};
