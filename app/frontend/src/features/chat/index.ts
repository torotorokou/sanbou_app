/**
 * Chat Feature - Public API
 * MVVM+SOLID アーキテクチャに準拠した barrel export
 */

// ============================================================================
// Domain (Types)
// ============================================================================

export type {
  ChatMessage,
  ChatAnswerResult,
  ChatAnswerRequest,
} from './domain/types';

// ============================================================================
// Ports
// ============================================================================

export type { IChatRepository } from './ports/repository';

// ============================================================================
// Infrastructure (Repository)
// ============================================================================

export { postChatAnswer, ChatRepository } from './infrastructure/chat.repository';

// ============================================================================
// UI Components
// ============================================================================

// Cards
export { default as ChatAnswerSection } from './ui/cards/ChatAnswerSection';
export { default as ChatQuestionSection } from './ui/cards/ChatQuestionSection';
export { default as ChatSendButtonSection } from './ui/cards/ChatSendButtonSection';

// Components
export { default as AnswerViewer } from './ui/components/AnswerViewer';
export { default as ChatMessageCard } from './ui/components/ChatMessageCard';
export { default as PdfCardList } from './ui/components/PdfCardList';
export { default as PdfPreviewModal } from './ui/components/PdfPreviewModal';
export { default as QuestionPanel } from './ui/components/QuestionPanel';
export { default as References } from './ui/components/References';
