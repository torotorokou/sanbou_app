import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useNotificationStore } from '@features/notification';

describe('notificationStore', () => {
  beforeEach(() => {
    // reset store state before each test
    useNotificationStore.setState({ notifications: [] });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('addNotification returns id', () => {
    const id = useNotificationStore.getState().addNotification({
      type: 'info', title: 't', message: 'm', duration: 10,
    });
    expect(typeof id).toBe('string');
    expect(id.length).toBeGreaterThan(0);
  });

  it('auto removes after duration', async () => {
    vi.useFakeTimers();
  const { addNotification } = useNotificationStore.getState();
  addNotification({ type: 'success', title: 'auto', message: 'x', duration: 10 });
    expect(useNotificationStore.getState().notifications.length).toBe(1);
    vi.advanceTimersByTime(11);
    expect(useNotificationStore.getState().notifications.length).toBe(0);
  });

  it('removeNotification clears timer safely', () => {
    vi.useFakeTimers();
    const { addNotification, removeNotification } = useNotificationStore.getState();
    const id = addNotification({ type: 'info', title: 'a', message: 'b', duration: 1000 });
    removeNotification(id);
    // calling again should not throw
    removeNotification(id);
    expect(useNotificationStore.getState().notifications.find(n => n.id === id)).toBeUndefined();
  });

  it('deduplicates within 800ms window', () => {
    vi.useFakeTimers();
    const { addNotification } = useNotificationStore.getState();
  addNotification({ type: 'error', title: 'same', message: 'm', duration: 10 });
  const id2 = addNotification({ type: 'error', title: 'same', message: 'm', duration: 10 });
    expect(id2).toBe('');
    expect(useNotificationStore.getState().notifications.length).toBe(1);
  });
});
