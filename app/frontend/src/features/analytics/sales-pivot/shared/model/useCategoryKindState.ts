/**
 * features/analytics/sales-pivot/shared/model/useCategoryKindState.ts
 * CategoryKind（廃棄物/有価物タブ）の状態管理
 */

import { useState } from "react";
import type { CategoryKind } from "./types";

export function useCategoryKindState(initialValue: CategoryKind = "waste") {
  const [categoryKind, setCategoryKind] = useState<CategoryKind>(initialValue);
  return { categoryKind, setCategoryKind };
}
