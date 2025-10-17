import type { ReactNode } from "react";

export interface ManualItem {
  id: string;
  title: string;
  description?: string;
  flowUrl?: string;
  videoUrl?: string;
  route?: string;
  tags?: string[];
}

export interface ManualSection {
  id: string;
  title: string;
  icon?: ReactNode;
  items: ManualItem[];
}
