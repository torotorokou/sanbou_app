// src/features/chat/index.ts
// Public API for Chat Feature

// ============================================================================
// Model (Types)
// ============================================================================

export type {
  ChatMessage,
  ChatAnswerResult,
  ChatAnswerRequest,
} from './model/chat.types';

// ============================================================================
// API
// ============================================================================

export { postChatAnswer } from './api/chatService';

// ============================================================================
// UI Components
// ============================================================================

// Main components (exported for external use)
export { default as ChatAnswerSection } from './ui/ChatAnswerSection';
export { default as ChatQuestionSection } from './ui/ChatQuestionSection';
export { default as ChatSendButtonSection } from './ui/ChatSendButtonSection';
export { default as PdfPreviewModal } from './ui/PdfPreviewModal';

// Supporting components (can be exported if needed)
export { default as AnswerViewer } from './ui/AnswerViewer';
export { default as ChatMessageCard } from './ui/ChatMessageCard';
export { default as PdfCardList } from './ui/PdfCardList';
export { default as QuestionPanel } from './ui/QuestionPanel';
