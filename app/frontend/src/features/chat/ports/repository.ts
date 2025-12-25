/**
 * Chat Feature - Ports Layer
 * Repository Interface
 */

import type { ChatAnswerRequest, ChatAnswerResult } from "../domain/types";

export interface IChatRepository {
  postChatAnswer(payload: ChatAnswerRequest): Promise<ChatAnswerResult>;
}
