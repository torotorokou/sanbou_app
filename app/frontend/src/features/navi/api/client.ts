// features/navi/api/client.ts
// HTTP通信のみを担当（apiGet/apiPostのラッパー）

import { apiGet, apiPost } from '@shared/infrastructure/http';
import type {
  ChatAnswerResponseDto,
  ChatQuestionRequestDto,
  QuestionOptionsResponseDto,
} from '../model/dto';

/**
 * Navi機能のAPIクライアント
 */
export const NaviApiClient = {
  /**
   * 質問テンプレート一覧を取得
   */
  async getQuestionOptions(): Promise<QuestionOptionsResponseDto> {
    return await apiGet<QuestionOptionsResponseDto>(
      '/rag_api/api/question-options'
    );
  },

  /**
   * AI回答を生成（質問を送信）
   */
  async generateAnswer(
    payload: ChatQuestionRequestDto
  ): Promise<ChatAnswerResponseDto> {
    return await apiPost<ChatAnswerResponseDto>(
      '/rag_api/api/generate-answer',
      payload
    );
  },
};
