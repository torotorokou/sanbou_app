// features/navi/api/client.ts
// HTTP通信のみを担当（coreApi経由で /core_api/... に統一）

import { coreApi } from '@/shared';
import type {
  ChatAnswerResponseDto,
  ChatQuestionRequestDto,
  QuestionOptionsResponseDto,
} from '../domain/types/dto';

/**
 * Navi機能のAPIクライアント
 * すべての通信は /core_api/... 経由
 */
export const NaviApiClient = {
  /**
   * 質問テンプレート一覧を取得
   * core_api経由でrag_apiにフォワード
   */
  async getQuestionOptions(): Promise<QuestionOptionsResponseDto> {
    return await coreApi.get<QuestionOptionsResponseDto>(
      '/core_api/rag/question-options'
    );
  },

  /**
   * AI回答を生成（質問を送信）
   * core_api経由でrag_apiにフォワード
   */
  async generateAnswer(
    payload: ChatQuestionRequestDto
  ): Promise<ChatAnswerResponseDto> {
    return await coreApi.post<ChatAnswerResponseDto>(
      '/core_api/rag/generate-answer',
      payload
    );
  },
};
