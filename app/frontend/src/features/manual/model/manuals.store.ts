// features/manual/model/manuals.store.ts
// Manuals用のスクロールストアを manual 機能下に移動

import { create } from 'zustand';

type ScrollState = {
  listScrollY: number;
  setListScrollY: (y: number) => void;
};

export const useManualsStore = create<ScrollState>((set) => ({
  listScrollY: 0,
  setListScrollY: (y) => set({ listScrollY: y }),
}));
