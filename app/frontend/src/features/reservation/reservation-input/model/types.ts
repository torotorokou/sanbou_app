/**
 * ReservationInput - 型定義
 *
 * Model (型定義)
 * 規約: UI Componentのprops型をmodel層で一元管理
 */

import type { Dayjs } from "dayjs";

/**
 * ReservationInputForm コンポーネントのProps
 */
export interface ReservationInputFormProps {
  selectedDate: Dayjs | null;
  totalTrucks: number | null;
  totalCustomerCount: number | null;
  fixedCustomerCount: number | null;
  note: string;
  onSelectDate: (date: Dayjs | null) => void;
  onChangeTotalTrucks: (value: number | null) => void;
  onChangeTotalCustomerCount: (value: number | null) => void;
  onChangeFixedCustomerCount: (value: number | null) => void;
  onChangeNote: (value: string) => void;
  onSubmit: () => void;
  onDelete: () => void;
  isSaving: boolean;
  error: string | null;
  hasManualData: boolean;
}
