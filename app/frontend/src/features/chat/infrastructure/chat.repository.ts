/**
 * Chat Feature - Infrastructure Layer
 * HTTP Repository Implementation (IChatRepository)
 */

import { apiPost } from '@shared/infrastructure/http';
import type { ChatAnswerRequest, ChatAnswerResult } from '../domain/types';

export class ChatRepository {
  async postChatAnswer(payload: ChatAnswerRequest): Promise<ChatAnswerResult> {
    return apiPost<ChatAnswerResult>('/core_api/chat/test-answer', payload);
  }
}

// Legacy export for backward compatibility
export async function postChatAnswer(payload: ChatAnswerRequest) {
  const repo = new ChatRepository();
  return repo.postChatAnswer(payload);
}
