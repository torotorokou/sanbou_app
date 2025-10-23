/**
 * CalendarCard.Ukeire Component
 * 受入ダッシュボード用の薄いラッパー - CalendarRepositoryForUkeire を注入
 */

import React from 'react';
import CalendarCard from './CalendarCard';
import { CalendarRepositoryForUkeire } from '../infrastructure/calendar.http.repository';
import { MockCalendarRepositoryForUkeire } from '../infrastructure/calendar.mock.repository';

export type CalendarCardUkeireProps = {
  year: number;
  month: number;
  style?: React.CSSProperties;
  useMock?: boolean;
};

export default function CalendarCardUkeire({ year, month, style, useMock = false }: CalendarCardUkeireProps) {
  const repository = useMock ? new MockCalendarRepositoryForUkeire() : new CalendarRepositoryForUkeire();
  return <CalendarCard year={year} month={month} repository={repository} style={style} />;
}
