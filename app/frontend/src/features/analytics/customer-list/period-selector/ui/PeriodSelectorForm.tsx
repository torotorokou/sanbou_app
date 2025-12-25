import React from "react";
import { DatePicker, Typography } from "antd";
import type { Dayjs } from "dayjs";
const { Title } = Typography;

type Props = {
  currentStart: Dayjs | null;
  currentEnd: Dayjs | null;
  previousStart: Dayjs | null;
  previousEnd: Dayjs | null;
  setCurrentStart: (d: Dayjs | null) => void;
  setCurrentEnd: (d: Dayjs | null) => void;
  setPreviousStart: (d: Dayjs | null) => void;
  setPreviousEnd: (d: Dayjs | null) => void;
};

/**
 * Period Selector Form Component
 *
 * 期間選択フォーム
 *
 * ロジック説明：
 * - 対象期間：最近の期間（この期間に取引がなければ「離脱」と判定）
 * - 比較期間：過去の基準期間（この期間に取引があった顧客を基準とする）
 * - 離脱顧客の定義：比較期間に取引があったが、対象期間に取引がない顧客
 *
 * 例：
 * - 対象期間: 2025-01〜2025-11 →  この期間に取引がない
 * - 比較期間: 2024-01〜2024-12 →  この期間に取引があった
 * - 結果: 2024年は取引していたが2025年は取引がない顧客 = 離脱顧客
 */
const PeriodSelectorForm: React.FC<Props> = ({
  currentStart,
  currentEnd,
  previousStart,
  previousEnd,
  setCurrentStart,
  setCurrentEnd,
  setPreviousStart,
  setPreviousEnd,
}) => (
  <>
    <Title
      level={5}
      style={{
        marginBottom: 6,
        fontSize: "clamp(13px, 0.9vw, 16px)",
        lineHeight: 1.3,
      }}
    >
      対象期間
      <br />
      「（この期間に取引なし：離脱」）
    </Title>
    <Typography.Text
      type="secondary"
      style={{
        fontSize: "clamp(11px, 0.75vw, 12px)",
        display: "block",
        marginBottom: 8,
        lineHeight: 1.4,
      }}
    >
      最近の期間を指定してください
      <br />
      「（例：2025-01〜2025-11）
    </Typography.Text>
    <div style={{ marginBottom: 8, fontSize: "clamp(12px, 0.85vw, 14px)" }}>
      <div style={{ marginBottom: 6 }}>
        開始月：
        <DatePicker
          picker="month"
          value={currentStart}
          onChange={setCurrentStart}
          style={{ width: 120, marginLeft: 8 }}
          size="small"
        />
      </div>
      <div>
        終了月：
        <DatePicker
          picker="month"
          value={currentEnd}
          onChange={setCurrentEnd}
          disabledDate={(current) =>
            currentStart
              ? current && current.isBefore(currentStart, "month")
              : false
          }
          style={{ width: 120, marginLeft: 8 }}
          size="small"
        />
      </div>
    </div>
    <Title
      level={5}
      style={{
        margin: "clamp(16px, 1.2vw, 24px) 0 6px 0",
        fontSize: "clamp(13px, 0.9vw, 16px)",
        lineHeight: 1.3,
      }}
    >
      比較期間（過去の基準期間）
    </Title>
    <Typography.Text
      type="secondary"
      style={{
        fontSize: "clamp(11px, 0.75vw, 12px)",
        display: "block",
        marginBottom: 8,
        lineHeight: 1.4,
      }}
    >
      過去の基準期間を指定してください
      <br />
      「（例：2024-01〜2024-12）
      <br />
      ※この期間に取引があり、対象期間に取引がない顧客を「離脱」として抽出
    </Typography.Text>
    <div style={{ marginBottom: 8, fontSize: "clamp(12px, 0.85vw, 14px)" }}>
      <div style={{ marginBottom: 6 }}>
        開始月：
        <DatePicker
          picker="month"
          value={previousStart}
          onChange={setPreviousStart}
          disabled={!currentStart || !currentEnd}
          disabledDate={(current) => {
            if (!currentStart || !currentEnd) return false;
            // 今期の範囲と重複する月を無効化
            return (
              current &&
              !current.isBefore(currentStart, "month") &&
              !current.isAfter(currentEnd, "month")
            );
          }}
          style={{ width: 120, marginLeft: 8 }}
          placeholder={
            !currentStart || !currentEnd ? "今期を先に選択" : undefined
          }
          size="small"
        />
      </div>
      <div>
        終了月：
        <DatePicker
          picker="month"
          value={previousEnd}
          onChange={setPreviousEnd}
          disabled={!previousStart || !currentStart || !currentEnd}
          disabledDate={(current) => {
            if (!currentStart || !currentEnd || !previousStart) return false;
            // 前期開始月より前、または今期と重複する月を無効化
            return (
              current &&
              (current.isBefore(previousStart, "month") ||
                (!current.isBefore(currentStart, "month") &&
                  !current.isAfter(currentEnd, "month")))
            );
          }}
          style={{ width: 120, marginLeft: 8 }}
          placeholder={!previousStart ? "開始月を先に選択" : undefined}
          size="small"
        />
      </div>
    </div>
  </>
);

export default PeriodSelectorForm;
