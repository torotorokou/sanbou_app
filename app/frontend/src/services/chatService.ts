// src/services/chatService.ts
import { apiPost } from '@shared/infrastructure/http';
import type { ChatAnswerRequest, ChatAnswerResult } from '@/types/chat';

export async function postChatAnswer(payload: ChatAnswerRequest) {
    return apiPost<ChatAnswerResult>('/api/test-answer', payload);
}
