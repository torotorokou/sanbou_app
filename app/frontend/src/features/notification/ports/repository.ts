/**
 * Notification Feature - Ports Layer
 */

import type { Notification } from "../domain/types/notification.types";

export interface INotificationRepository {
  subscribe(onMessage: (notification: Notification) => void): () => void;
}
