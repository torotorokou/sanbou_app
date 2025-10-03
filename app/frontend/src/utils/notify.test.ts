import { describe, it, expect, beforeEach, vi } from 'vitest';
import { notifySuccess, notifyError, notifyPersistent, notifyApiError, useNotificationStore } from '@features/notification';

function resetStore() {
  useNotificationStore.setState({ notifications: [] });
}

describe('notify utils', () => {
  beforeEach(() => resetStore());

  it('notifySuccess/notifyError return id', () => {
    const id1 = notifySuccess('ok', 'done');
    const id2 = notifyError('ng', 'bad');
    expect(typeof id1).toBe('string');
    expect(typeof id2).toBe('string');
    expect(id1.length).toBeGreaterThan(0);
    expect(id2.length).toBeGreaterThan(0);
  });

  it('notifyPersistent does not auto remove', () => {
    const id = notifyPersistent('info', 'hold', 'wait');
    const exists = useNotificationStore.getState().notifications.some(n => n.id === id);
    expect(exists).toBe(true);
  });

  it('notifyApiError with ApiError and ProblemDetails', () => {
    // ApiError-like
    class ApiError extends Error {
      code: string; status: number; userMessage: string;
      constructor(code: string, status: number, userMessage: string) { super(userMessage); this.code = code; this.status = status; this.userMessage = userMessage; }
    }
    const id1 = notifyApiError(new ApiError('E001', 400, 'bad request'), '失敗');
    expect(typeof id1).toBe('string');

    // ProblemDetails-like
    const id2 = notifyApiError({ title: 'タイトル', userMessage: '詳細' }, '失敗');
    expect(typeof id2).toBe('string');
  });
});
