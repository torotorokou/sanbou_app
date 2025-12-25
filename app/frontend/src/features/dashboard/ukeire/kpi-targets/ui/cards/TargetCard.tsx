/**
 * TargetCard Component
 * 目標達成状況を表示するカード
 */

import React from 'react';
import { Card, Space, Typography, Tooltip, Statistic, Progress, Segmented } from 'antd';
import './TargetCard.overrides.css';
import dayjs from 'dayjs';
import isoWeekPlugin from 'dayjs/plugin/isoWeek';
import { InfoCircleOutlined } from '@ant-design/icons';
import { COLORS } from '@/features/dashboard/ukeire/domain/constants';
import { clamp } from '@/features/dashboard/ukeire/domain/valueObjects';

export type AchievementMode = 'toDate' | 'toEnd';

export type TargetCardRowData = {
  key: string;
  label: string;
  target: number | null;
  actual: number | null;
};

export type TargetCardProps = {
  rows: TargetCardRowData[];
  style?: React.CSSProperties;
  isMobile?: boolean; // Mobile モードでフォントサイズを動的に調整
  isoWeek?: number; // 将来的にはバックグラウンドから取得する想定。指定があればそれを優先して表示する
  achievementMode?: AchievementMode; // 達成率モード（親コンポーネントで管理）
  onModeChange?: (mode: AchievementMode) => void; // モード変更コールバック
};

export const TargetCard: React.FC<TargetCardProps> = ({
  rows,
  style,
  isMobile = false,
  isoWeek,
  achievementMode = 'toDate',
  onModeChange,
}) => {
  // isoWeek プラグインを拡張
  dayjs.extend(isoWeekPlugin);
  // 画面サイズに応じて動的にフォントサイズを調整（xl: 1280px付近では小さめ）
  const headerFontSize = isMobile ? 'clamp(10px, 2.8vw, 12px)' : 'clamp(13px, 0.9vw, 16px)';
  const labelFontSize = isMobile ? 'clamp(10px, 2.5vw, 12px)' : 'clamp(10px, 0.7vw, 13px)';
  const valueFontSize = isMobile ? 'clamp(12px, 3.2vw, 15px)' : 'clamp(14px, 1.1vw, 20px)';
  const pctFontSize = isMobile ? 'clamp(10px, 2.5vw, 13px)' : 'clamp(14px, 1vw, 18px)';

  // Mobile モードでは行の高さを確保（複数行ラベル対応）
  const minRowHeight = isMobile ? 44 : 44;
  const gridPadding = isMobile ? 6 : 8;
  const rowGap = isMobile ? 4 : 6;

  return (
    <Card
      variant="outlined"
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        ...style,
      }}
      styles={{
        body: {
          padding: isMobile ? 8 : 12,
          display: 'flex',
          flexDirection: 'column',
          gap: isMobile ? 4 : 8,
          flex: 1,
          minHeight: 0,
          overflow: 'visible',
        },
      }}
    >
      {/* ヘッダー: タイトル・ツールチップ・モード切り替え */}
      <div
        style={{
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          gap: isMobile ? 2 : 4,
        }}
      >
        <Space align="baseline" size={isMobile ? 4 : 8}>
          <Typography.Title level={5} style={{ margin: 0, fontSize: isMobile ? '14px' : '16px' }}>
            目標カード
          </Typography.Title>
          <Tooltip title="週目標は当月の営業日配分で按分。日目標は平日/土/日祝の重みで配分。">
            <InfoCircleOutlined
              style={{ color: '#8c8c8c', fontSize: isMobile ? '12px' : '14px' }}
            />
          </Tooltip>
        </Space>

        {/* 達成率モード切り替え（親のコールバックを呼び出す） */}
        {onModeChange && (
          <div
            style={{
              display: 'flex',
              justifyContent: isMobile ? 'flex-start' : 'flex-end',
            }}
          >
            <Segmented
              className="customSegmented"
              value={achievementMode}
              onChange={(value) => onModeChange(value as AchievementMode)}
              options={[
                { label: isMobile ? '累計' : '昨日まで', value: 'toDate' },
                { label: isMobile ? '期末' : '月末・週末', value: 'toEnd' },
              ]}
              size={isMobile ? 'small' : 'small'}
              style={{ width: isMobile ? 'auto' : 'auto' }}
            />
          </div>
        )}
      </div>

      <div
        style={{
          border: '1px solid #f0f0f0',
          borderRadius: 8,
          background: '#fff',
          padding: gridPadding,
          display: 'grid',
          gridTemplateColumns: isMobile ? '1fr auto auto 1.2fr' : 'auto auto auto 1fr',
          gridTemplateRows: `repeat(${1 + rows.length}, minmax(${minRowHeight}px, auto))`,
          columnGap: isMobile ? 6 : 12,
          rowGap: rowGap,
          alignItems: isMobile ? 'start' : 'center',
          boxSizing: 'border-box',
          flex: 1,
          overflow: 'visible',
        }}
      >
        {/* ヘッダ行 */}
        <div style={{ color: '#8c8c8c', fontSize: headerFontSize }} />
        <div
          style={{
            color: '#8c8c8c',
            fontSize: headerFontSize,
            fontWeight: 700,
            textAlign: 'center',
            justifySelf: 'center',
          }}
        >
          目標
        </div>
        <div
          style={{
            color: '#8c8c8c',
            fontSize: headerFontSize,
            fontWeight: 700,
            textAlign: 'center',
            justifySelf: 'center',
          }}
        >
          実績
        </div>
        <div
          style={{
            color: '#8c8c8c',
            fontSize: headerFontSize,
            fontWeight: 700,
            textAlign: 'center',
            justifySelf: 'center',
          }}
        >
          達成率
        </div>

        {/* データ行 */}
        {rows.map((r) => {
          // NULL値をチェックして達成率を計算
          const ratioRaw =
            r.target !== null && r.actual !== null && r.target > 0 ? r.actual / r.target : 0;
          const pct =
            r.target !== null && r.actual !== null && r.target > 0 ? Math.round(ratioRaw * 100) : 0;
          const barPct = clamp(pct, 0, 100);
          const pctColor =
            ratioRaw >= 1 ? COLORS.ok : ratioRaw >= 0.9 ? COLORS.warn : COLORS.danger;

          // NULL値の場合は達成率を非表示にするかどうか
          const hasValidData = r.target !== null && r.actual !== null;

          // determine iso week to show: prefer prop on the component; fallback to computing from today
          let isoWeekToShow: number | undefined = typeof isoWeek === 'number' ? isoWeek : undefined;
          if (isoWeekToShow === undefined) {
            isoWeekToShow = dayjs().isoWeek();
          }

          return (
            <React.Fragment key={r.key}>
              <div
                style={{
                  color: '#595959',
                  fontSize: labelFontSize,
                  fontWeight: 800,
                  lineHeight: isMobile ? 1.2 : 1.2,
                  minWidth: 0,
                  wordBreak: 'break-word',
                }}
              >
                {/* 今週のラベルにはW##を表示 */}
                {(() => {
                  const label = r.label ?? '';
                  // allow labels to include explicit newline markers ("\n") and render them stacked
                  const lines = String(label).split('\n');
                  const isThisWeekLabel = label.startsWith('今週');

                  if (isThisWeekLabel && typeof isoWeekToShow === 'number') {
                    const w = String(isoWeekToShow).padStart(2, '0');
                    if (isMobile) {
                      // Mobile: 縦並びで全て表示（途切れないように）
                      return (
                        <div
                          style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 1,
                            lineHeight: 1.2,
                          }}
                        >
                          {lines.map((ln, idx) => (
                            <span
                              key={idx}
                              style={{
                                fontSize: idx > 0 ? '0.85em' : '1em',
                                color: idx > 0 ? '#8c8c8c' : 'inherit',
                              }}
                            >
                              {ln}
                            </span>
                          ))}
                          <span
                            style={{
                              color: '#1890ff',
                              fontWeight: 700,
                              fontSize: '0.85em',
                            }}
                          >{`W${w}`}</span>
                        </div>
                      );
                    }
                    // Desktop: ラベル（複数行可）を表示し、下段に W## を表示
                    return (
                      <div
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 2,
                        }}
                      >
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          {lines.map((ln, idx) => (
                            <span key={idx}>{ln}</span>
                          ))}
                        </div>
                        <span
                          style={{
                            color: '#1890ff',
                            fontWeight: 700,
                            fontSize: '0.85em',
                          }}
                        >{`W${w}`}</span>
                      </div>
                    );
                  }

                  // 非週次ラベル：改行があれば縦に並べて表示
                  if (lines.length > 1) {
                    return (
                      <div
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 2,
                        }}
                      >
                        {lines.map((ln, idx) => (
                          <span key={idx}>{ln}</span>
                        ))}
                      </div>
                    );
                  }

                  return <>{label}</>;
                })()}
              </div>
              <div>
                {r.target !== null ? (
                  <Statistic
                    value={Math.round(r.target)}
                    suffix="t"
                    valueStyle={{
                      color: COLORS.primary,
                      fontSize: valueFontSize,
                      fontWeight: 800,
                      lineHeight: 1,
                    }}
                    style={{ lineHeight: 1 }}
                  />
                ) : (
                  <div
                    style={{
                      color: '#8c8c8c',
                      fontSize: valueFontSize,
                      fontWeight: 800,
                      lineHeight: 1,
                      textAlign: 'center',
                    }}
                  >
                    —
                  </div>
                )}
              </div>
              <div>
                {r.actual !== null ? (
                  <Statistic
                    value={Math.round(r.actual)}
                    suffix="t"
                    valueStyle={{
                      color: '#222',
                      fontSize: valueFontSize,
                      fontWeight: 800,
                      lineHeight: 1,
                    }}
                    style={{ lineHeight: 1 }}
                  />
                ) : (
                  <div
                    style={{
                      color: '#8c8c8c',
                      fontSize: valueFontSize,
                      fontWeight: 800,
                      lineHeight: 1,
                      textAlign: 'center',
                    }}
                  >
                    —
                  </div>
                )}
              </div>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 2,
                  minWidth: 0,
                }}
              >
                {hasValidData ? (
                  <>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'flex-end',
                        alignItems: 'baseline',
                      }}
                    >
                      <Statistic
                        value={pct}
                        suffix="%"
                        valueStyle={{
                          color: pctColor,
                          fontSize: pctFontSize,
                          fontWeight: 700,
                          lineHeight: 1,
                        }}
                        style={{ lineHeight: 1 }}
                      />
                    </div>
                    <Progress
                      percent={barPct}
                      showInfo={false}
                      strokeColor={pctColor}
                      size={['100%', 8]}
                      style={{ margin: 0 }}
                    />
                  </>
                ) : (
                  <div
                    style={{
                      color: '#8c8c8c',
                      fontSize: pctFontSize,
                      fontWeight: 700,
                      lineHeight: 1,
                      textAlign: 'right',
                    }}
                  >
                    —
                  </div>
                )}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </Card>
  );
};
