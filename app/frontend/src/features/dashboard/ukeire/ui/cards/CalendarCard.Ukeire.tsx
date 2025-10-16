/**
 * CalendarCard.Ukeire Component
 * 受入ダッシュボード用の薄いラッパー - HttpCalendarRepository を注入
 * TODO: 本番環境では HttpCalendarRepository に切り替え
 */

import React from 'react';
import CalendarCard from '@/features/calendar/ui/CalendarCard';
// import { HttpCalendarRepository } from '@/features/calendar/repository';
import { MockCalendarRepository } from '@/features/calendar/repository';

export type CalendarCardUkeireProps = {
  year: number;
  month: number;
  style?: React.CSSProperties;
};

export default function CalendarCardUkeire({ year, month, style }: CalendarCardUkeireProps) {
  // 開発中はモックを使用
  return <CalendarCard year={year} month={month} repository={new MockCalendarRepository()} style={style} />;
  // 本番環境では以下に切り替え
  // return <CalendarCard year={year} month={month} repository={new HttpCalendarRepository()} style={style} />;
}
