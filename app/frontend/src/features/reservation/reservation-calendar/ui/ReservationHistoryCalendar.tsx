/**
 * ReservationHistoryCalendar - 予約履歴カレンダー（右側：表示専用）
 *
 * UI Component (状態レス)
 * 左の入力フォームとは連動しない。履歴表示のみ。
 * 規約: Named Export を使用
 */

import React, { useState } from "react";
import { Card, Button, Space, Typography, Spin, Modal } from "antd";
import {
  LeftOutlined,
  RightOutlined,
  TruckOutlined,
  TeamOutlined,
  CalendarOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import type { Dayjs } from "dayjs";
import dayjs from "dayjs";
import type { ReservationForecastDaily } from "../../shared";
import type { ReservationHistoryCalendarProps } from "../model/types";

const { Title, Text } = Typography;

const WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"];

export const ReservationHistoryCalendar: React.FC<
  ReservationHistoryCalendarProps
> = ({
  historyMonth,
  historyData,
  onChangeHistoryMonth,
  onDeleteDate,
  goToCurrentMonth,
  isLoadingHistory = false,
  isDeletingDate = null,
}) => {
  const [selectedDateForDetail, setSelectedDateForDetail] = useState<
    string | null
  >(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

  const handleDeleteClick = () => {
    setDeleteConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (onDeleteDate && selectedDateForDetail) {
      await onDeleteDate(selectedDateForDetail);
      setDeleteConfirmOpen(false);
      setDetailModalOpen(false);
      setSelectedDateForDetail(null);
    }
  };

  // 月の週データを生成
  const generateWeeks = (month: Dayjs) => {
    const firstDay = month.startOf("month");
    const lastDay = month.endOf("month");
    const startDate = firstDay.startOf("week").add(1, "day"); // 月曜始まり
    const endDate = lastDay.endOf("week").add(1, "day");

    const weeks: Dayjs[][] = [];
    let currentWeek: Dayjs[] = [];
    let current = startDate;

    while (current.isBefore(endDate) || current.isSame(endDate, "day")) {
      currentWeek.push(current);
      if (currentWeek.length === 7) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
      current = current.add(1, "day");
    }

    return weeks;
  };

  const weeks = generateWeeks(historyMonth);

  const goPrevMonth = () => {
    onChangeHistoryMonth(historyMonth.subtract(1, "month"));
  };

  const goNextMonth = () => {
    onChangeHistoryMonth(historyMonth.add(1, "month"));
  };

  // 日付のデータを取得
  const getDataForDate = (date: Dayjs): ReservationForecastDaily | null => {
    const dateStr = date.format("YYYY-MM-DD");
    return historyData.find((d) => d.date === dateStr) || null;
  };

  return (
    <>
      <style>{`
        /* xl付近 (1280-1399px) - コンパクト表示 */
        @media (min-width: 1280px) and (max-width: 1399px) {
          .calendar-responsive .calendar-date {
            font-size: 12px !important;
          }
          .calendar-responsive .calendar-icon {
            font-size: 12px !important;
          }
          .calendar-responsive .calendar-value-large {
            font-size: 14px !important;
          }
          .calendar-responsive .calendar-value-small {
            font-size: 13px !important;
          }
          .calendar-responsive .calendar-cell {
            min-height: 65px !important;
            padding: 4px !important;
          }
        }

        /* 中サイズ (1400-1599px) */
        @media (min-width: 1400px) and (max-width: 1599px) {
          .calendar-responsive .calendar-date {
            font-size: 13px !important;
          }
          .calendar-responsive .calendar-icon {
            font-size: 13px !important;
          }
          .calendar-responsive .calendar-value-large {
            font-size: 16px !important;
          }
          .calendar-responsive .calendar-value-small {
            font-size: 14px !important;
          }
          .calendar-responsive .calendar-cell {
            min-height: 70px !important;
            padding: 5px !important;
          }
        }

        /* 大サイズ (1600px以上) */
        @media (min-width: 1600px) {
          .calendar-responsive .calendar-date {
            font-size: 14px !important;
          }
          .calendar-responsive .calendar-icon {
            font-size: 14px !important;
          }
          .calendar-responsive .calendar-value-large {
            font-size: 18px !important;
          }
          .calendar-responsive .calendar-value-small {
            font-size: 15px !important;
          }
          .calendar-responsive .calendar-cell {
            min-height: 75px !important;
            padding: 6px !important;
          }
        }
      `}</style>

      <Card
        className="calendar-responsive"
        title={
          <Space direction="vertical" size={0} style={{ width: "100%" }}>
            <Title level={5} style={{ margin: 0, fontSize: 16 }}>
              📅 予約履歴カレンダー
            </Title>
          </Space>
        }
        size="small"
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
        }}
        styles={{
          body: { flex: 1, overflow: "auto", padding: "12px", width: "100%" },
        }}
      >
        {/* 月移動ヘッダー */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 12,
          }}
        >
          <div style={{ width: 80 }}>
            {goToCurrentMonth && !historyMonth.isSame(dayjs(), "month") && (
              <Button
                type="default"
                icon={<CalendarOutlined />}
                onClick={goToCurrentMonth}
                size="small"
                disabled={isLoadingHistory}
              >
                今月
              </Button>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Button
              type="text"
              icon={<LeftOutlined />}
              onClick={goPrevMonth}
              size="small"
              disabled={isLoadingHistory}
            />
            <Text
              strong
              style={{ fontSize: 20, minWidth: 180, textAlign: "center" }}
            >
              {historyMonth.format("YYYY年MM月")}
            </Text>
            <Button
              type="text"
              icon={<RightOutlined />}
              onClick={goNextMonth}
              size="small"
              disabled={isLoadingHistory}
            />
          </div>
          <div style={{ width: 80 }} />
        </div>

        {/* 凡例 */}
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 16,
            marginBottom: 12,
            padding: "8px",
            background: "#f5f5f5",
            borderRadius: 4,
            fontSize: 13,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <TruckOutlined style={{ color: "#1890ff", fontSize: 14 }} />
            <span>合計台数</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <TeamOutlined style={{ color: "#52c41a", fontSize: 14 }} />
            <span>固定客数</span>
          </div>
        </div>

        {/* カレンダー本体 */}
        <Spin spinning={isLoadingHistory}>
          <div style={{ opacity: isLoadingHistory ? 0.5 : 1 }}>
            {/* 曜日ヘッダー */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(7, 1fr)",
                gap: 2,
                marginBottom: 4,
              }}
            >
              {WEEKDAYS.map((day, idx) => (
                <div
                  key={idx}
                  style={{
                    textAlign: "center",
                    fontSize: 13,
                    fontWeight: "bold",
                    color:
                      idx === 5 ? "#1890ff" : idx === 6 ? "#f5222d" : "#666",
                    padding: "6px 0",
                  }}
                >
                  {day}
                </div>
              ))}
            </div>

            {/* 日付グリッド */}
            {weeks.map((week, weekIdx) => (
              <div
                key={weekIdx}
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(7, 1fr)",
                  gap: 2,
                  marginBottom: 2,
                }}
              >
                {week.map((date, dayIdx) => {
                  const isCurrentMonth = date.month() === historyMonth.month();
                  const isToday = date.isSame(dayjs(), "day");
                  const data = getDataForDate(date);
                  const dateStr = date.format("YYYY-MM-DD");
                  const isDeleting = isDeletingDate === dateStr;

                  const handleCellClick = () => {
                    if (data && onDeleteDate) {
                      setSelectedDateForDetail(dateStr);
                      setDetailModalOpen(true);
                    }
                  };

                  return (
                    <div
                      key={dayIdx}
                      className="calendar-cell"
                      style={{
                        minHeight: 75,
                        padding: 6,
                        border: "1px solid #f0f0f0",
                        borderRadius: 4,
                        background: isToday
                          ? "#e6f7ff"
                          : isCurrentMonth
                            ? "#fff"
                            : "#fafafa",
                        opacity: isCurrentMonth ? (isDeleting ? 0.5 : 1) : 0.4,
                        cursor: data ? "pointer" : "default",
                        position: "relative",
                        transition: "all 0.2s",
                      }}
                      onClick={handleCellClick}
                      title={
                        data
                          ? `クリックで詳細確認 - 合計: ${data.reserve_trucks}台, 固定: ${data.reserve_fixed_trucks}台`
                          : undefined
                      }
                    >
                      <div
                        className="calendar-date"
                        style={{
                          fontSize: 14,
                          fontWeight: isToday ? "bold" : "normal",
                          marginBottom: 4,
                        }}
                      >
                        {date.date()}
                      </div>
                      {data && (
                        <div style={{ fontSize: 12 }}>
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              marginBottom: 4,
                            }}
                          >
                            <TruckOutlined
                              className="calendar-icon"
                              style={{
                                fontSize: 14,
                                color: "#1890ff",
                                marginRight: 4,
                              }}
                            />
                            <span
                              className="calendar-value-large"
                              style={{
                                fontSize: 18,
                                fontWeight: "bold",
                                color: "#000",
                              }}
                            >
                              {data.reserve_trucks}
                            </span>
                          </div>
                          <div
                            style={{ display: "flex", alignItems: "center" }}
                          >
                            <TeamOutlined
                              className="calendar-icon"
                              style={{
                                fontSize: 14,
                                color: "#52c41a",
                                marginRight: 4,
                              }}
                            />
                            <span
                              className="calendar-value-small"
                              style={{
                                fontSize: 15,
                                fontWeight: "500",
                                color: "#000",
                              }}
                            >
                              {data.reserve_fixed_trucks}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </Spin>

        {/* 詳細確認モーダル */}
        <Modal
          title="予約データの詳細確認"
          open={detailModalOpen}
          onCancel={() => {
            setDetailModalOpen(false);
            setSelectedDateForDetail(null);
          }}
          footer={[
            <Button
              key="cancel"
              onClick={() => {
                setDetailModalOpen(false);
                setSelectedDateForDetail(null);
              }}
            >
              閉じる
            </Button>,
            <Button
              key="delete"
              type="primary"
              danger
              icon={<DeleteOutlined />}
              onClick={handleDeleteClick}
            >
              削除する
            </Button>,
          ]}
        >
          {selectedDateForDetail &&
            (() => {
              const data = historyData.find(
                (d) => d.date === selectedDateForDetail,
              );
              return (
                <div>
                  <div
                    style={{
                      background: "#f5f5f5",
                      padding: 12,
                      borderRadius: 4,
                    }}
                  >
                    <p style={{ margin: "4px 0" }}>
                      <strong>日付:</strong>{" "}
                      {dayjs(selectedDateForDetail).format(
                        "YYYY年MM月DD日 (dd)",
                      )}
                    </p>
                    {data && (
                      <>
                        <p style={{ margin: "4px 0" }}>
                          <strong>合計台数:</strong> {data.reserve_trucks}台
                        </p>
                        <p style={{ margin: "4px 0" }}>
                          <strong>固定客台数:</strong>{" "}
                          {data.reserve_fixed_trucks}台
                        </p>
                        <p style={{ margin: "8px 0 4px 0" }}>
                          <strong>備考:</strong>
                          <br />
                          <span style={{ whiteSpace: "pre-wrap" }}>
                            {data.note || "（なし）"}
                          </span>
                        </p>
                      </>
                    )}
                  </div>
                </div>
              );
            })()}
        </Modal>

        {/* 削除最終確認モーダル */}
        <Modal
          title="削除の最終確認"
          open={deleteConfirmOpen}
          onCancel={() => setDeleteConfirmOpen(false)}
          footer={[
            <Button key="cancel" onClick={() => setDeleteConfirmOpen(false)}>
              キャンセル
            </Button>,
            <Button
              key="delete"
              type="primary"
              danger
              icon={<DeleteOutlined />}
              loading={isDeletingDate === selectedDateForDetail}
              onClick={handleConfirmDelete}
            >
              削除する
            </Button>,
          ]}
        >
          {selectedDateForDetail &&
            (() => {
              const data = historyData.find(
                (d) => d.date === selectedDateForDetail,
              );
              return (
                <div>
                  <p>以下の手入力データを削除してもよろしいですか？</p>
                  <div
                    style={{
                      background: "#f5f5f5",
                      padding: 12,
                      borderRadius: 4,
                      marginTop: 12,
                    }}
                  >
                    <p style={{ margin: "4px 0" }}>
                      <strong>日付:</strong>{" "}
                      {dayjs(selectedDateForDetail).format(
                        "YYYY年MM月DD日 (dd)",
                      )}
                    </p>
                    {data && (
                      <>
                        <p style={{ margin: "4px 0" }}>
                          <strong>合計台数:</strong> {data.reserve_trucks}台
                        </p>
                        <p style={{ margin: "4px 0" }}>
                          <strong>固定客台数:</strong>{" "}
                          {data.reserve_fixed_trucks}台
                        </p>
                        <p style={{ margin: "8px 0 4px 0" }}>
                          <strong>備考:</strong>
                          <br />
                          <span style={{ whiteSpace: "pre-wrap" }}>
                            {data.note || "（なし）"}
                          </span>
                        </p>
                      </>
                    )}
                  </div>
                  <p style={{ marginTop: 12, color: "#ff4d4f" }}>
                    <strong>注意:</strong> この操作は取り消せません。
                  </p>
                </div>
              );
            })()}
        </Modal>
      </Card>
    </>
  );
};
