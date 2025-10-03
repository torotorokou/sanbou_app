import { create } from 'zustand';

type ScrollState = {
  listScrollY: number;
  setListScrollY: (y: number) => void;
};

export const useManualsStore = create<ScrollState>((set) => ({
  listScrollY: 0,
  setListScrollY: (y) => set({ listScrollY: y }),
}));
