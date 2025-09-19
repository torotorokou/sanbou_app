// src/services/chatService.ts
import { apiPost } from '@/services/httpClient';
import type { ChatAnswerRequest, ChatAnswerResult } from '@/types/chat';

export async function postChatAnswer(payload: ChatAnswerRequest) {
    return apiPost<ChatAnswerResult>('/api/test-answer', payload);
}
