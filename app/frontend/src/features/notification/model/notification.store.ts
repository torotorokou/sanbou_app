import { create } from 'zustand';
import type { Notification, CreateNotificationData } from './notification.types';

const DEFAULT_DURATION_MS = 3000;
const MAX_COUNT = 5;
const DEDUP_WINDOW_MS = 800;

const timeouts = new Map<string, ReturnType<typeof setTimeout>>();
const lastKeyAt = new Map<string, number>();

const newId = () =>
  (globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`);

const dedupKey = (d: Pick<CreateNotificationData, 'type' | 'title' | 'message'>) =>
  `${d.type}|${d.title}|${d.message}`;

interface NotificationState {
  notifications: Notification[];
  addNotification: (data: CreateNotificationData) => string;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;

  success: (title: string, message?: string, duration?: number | null) => string;
  error:   (title: string, message?: string, duration?: number | null) => string;
  info:    (title: string, message?: string, duration?: number | null) => string;
  warning: (title: string, message?: string, duration?: number | null) => string;
}

export const useNotificationStore = create<NotificationState>()((set, get) => ({
  notifications: [],

  addNotification: (data: CreateNotificationData) => {
    const now = Date.now();
    const key = dedupKey(data);
    const last = lastKeyAt.get(key);
    if (last && now - last < DEDUP_WINDOW_MS) {
      return '';
    }
    lastKeyAt.set(key, now);

    const id = newId();
    const duration = data.duration ?? DEFAULT_DURATION_MS;

    const n: Notification = {
      id,
      type: data.type,
      title: data.title,
      message: data.message,
      createdAt: new Date(),
      duration,
    };

    set((state) => {
      const next = [n, ...state.notifications].slice(0, MAX_COUNT);
      return { notifications: next };
    });

    if (duration && duration > 0) {
      const t = setTimeout(() => {
        get().removeNotification(id);
      }, duration);
      timeouts.set(id, t);
    }

    return id;
  },

  removeNotification: (id: string) => {
    const t = timeouts.get(id);
    if (t) {
      clearTimeout(t);
      timeouts.delete(id);
    }
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  clearAllNotifications: () => {
    for (const [, t] of timeouts) clearTimeout(t);
    timeouts.clear();
    set({ notifications: [] });
  },

  success: (title, message, duration) =>
    get().addNotification({ type: 'success', title, message: message ?? '', duration }),
  error: (title, message, duration) =>
    get().addNotification({ type: 'error', title, message: message ?? '', duration }),
  info: (title, message, duration) =>
    get().addNotification({ type: 'info', title, message: message ?? '', duration }),
  warning: (title, message, duration) =>
    get().addNotification({ type: 'warning', title, message: message ?? '', duration }),
}));

export type { NotificationState };
