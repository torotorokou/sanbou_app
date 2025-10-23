// features/navi/repository/NaviRepository.ts
// Repositoryインターフェース定義

import type { CategoryDataMap, ChatAnswer } from '../domain/types/types';
import type { ChatQuestionRequestDto } from '../domain/types/dto';

/**
 * Navi機能のリポジトリインターフェース
 */
export interface NaviRepository {
  /**
   * カテゴリと質問テンプレートのマッピングを取得
   */
  getQuestionOptions(): Promise<CategoryDataMap>;

  /**
   * 質問を送信してAI回答を取得
   */
  generateAnswer(request: ChatQuestionRequestDto): Promise<ChatAnswer>;
}
