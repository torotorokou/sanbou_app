/**
 * SSE（Server-Sent Events）通知クライアント
 *
 * 目的:
 * - サーバーからの通知イベントをリアルタイム受信
 * - 自動再接続
 */

import type { NotificationEvent } from "@features/notification/domain/types/contract";
import {
  notifySuccess,
  notifyError,
  notifyWarning,
  notifyInfo,
} from "@features/notification";

// 相対パスを使用（dev: Vite proxy、stg/prod: Nginx reverse proxy）
// BFF統一: core_api経由でアクセス
const SSE_URL = "/core_api/notifications/stream";

let eventSource: EventSource | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let isManuallyDisconnected = false;

/**
 * 通知イベントを処理
 */
function handleNotificationEvent(event: MessageEvent) {
  try {
    const notification: NotificationEvent = JSON.parse(event.data);

    console.log("[SSE] Received notification:", notification);

    // severity に応じて通知を表示
    switch (notification.severity) {
      case "success":
        notifySuccess(
          notification.title,
          notification.message,
          notification.duration ?? undefined,
        );
        break;
      case "error":
        notifyError(
          notification.title,
          notification.message,
          notification.duration ?? undefined,
        );
        break;
      case "warning":
        notifyWarning(
          notification.title,
          notification.message,
          notification.duration ?? undefined,
        );
        break;
      case "info":
      default:
        notifyInfo(
          notification.title,
          notification.message,
          notification.duration ?? undefined,
        );
        break;
    }
  } catch (error) {
    console.error("[SSE] Failed to parse notification event:", error);
  }
}

/**
 * SSE接続を確立
 */
function connect() {
  if (isManuallyDisconnected) {
    console.log("[SSE] Manually disconnected, skip reconnect");
    return;
  }

  if (eventSource && eventSource.readyState !== EventSource.CLOSED) {
    console.log("[SSE] Already connected");
    return;
  }

  console.log("[SSE] Connecting to", SSE_URL);
  eventSource = new EventSource(SSE_URL);

  // 通知イベントを受信
  eventSource.addEventListener("notification", handleNotificationEvent);

  // 接続確立
  eventSource.onopen = () => {
    console.log("[SSE] Connected");
  };

  // エラー発生時
  eventSource.onerror = (error) => {
    console.error("[SSE] Connection error:", error);
    eventSource?.close();

    // 自動再接続（5秒後）
    if (!isManuallyDisconnected) {
      console.log("[SSE] Reconnecting in 5 seconds...");
      reconnectTimer = setTimeout(() => {
        connect();
      }, 5000);
    }
  };
}

/**
 * SSE接続を切断
 */
function disconnect() {
  console.log("[SSE] Disconnecting");
  isManuallyDisconnected = true;

  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
}

/**
 * SSE接続を開始（アプリ起動時に呼び出す）
 */
export function startSSE() {
  isManuallyDisconnected = false;
  connect();
}

/**
 * SSE接続を停止（アプリ終了時に呼び出す）
 */
export function stopSSE() {
  disconnect();
}

/**
 * SSE接続状態を取得
 */
export function getSSEState(): "connecting" | "open" | "closed" {
  if (!eventSource) return "closed";

  switch (eventSource.readyState) {
    case EventSource.CONNECTING:
      return "connecting";
    case EventSource.OPEN:
      return "open";
    case EventSource.CLOSED:
    default:
      return "closed";
  }
}
