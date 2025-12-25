/**
 * ReservationInput - 型定義
 *
 * Model (型定義)
 * 規約: UI Componentのprops型をmodel層で一元管理
 */

import type { Dayjs } from 'dayjs';

/**
 * ReservationInputForm コンポーネントのProps
 */
export interface ReservationInputFormProps {
  selectedDate: Dayjs | null;
  totalTrucks: number | null;
  fixedTrucks: number | null;
  note: string;
  onSelectDate: (date: Dayjs | null) => void;
  onChangeTotalTrucks: (value: number | null) => void;
  onChangeFixedTrucks: (value: number | null) => void;
  onChangeNote: (value: string) => void;
  onSubmit: () => void;
  onDelete: () => void;
  isSaving: boolean;
  error: string | null;
  hasManualData: boolean;
}
