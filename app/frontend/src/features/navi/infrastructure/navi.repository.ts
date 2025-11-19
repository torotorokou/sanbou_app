// features/navi/repository/NaviRepositoryImpl.ts
// Repository実装（API→Domain変換）

import type { NaviRepository } from '../ports/repository';
import { NaviApiClient } from './navi.client';
import type { CategoryDataMap, ChatAnswer } from '../domain/types/types';
import type { ChatQuestionRequestDto } from '../domain/types/dto';

/**
 * Navi機能のリポジトリ実装
 */
export class NaviRepositoryImpl implements NaviRepository {
  /**
   * カテゴリと質問テンプレートのマッピングを取得
   */
  async getQuestionOptions(): Promise<CategoryDataMap> {
    const dto = await NaviApiClient.getQuestionOptions();
    // DTOをそのままDomainとして返す（構造が同じ）
    return dto as CategoryDataMap;
  }

  /**
   * 質問を送信してAI回答を取得
   */
  async generateAnswer(request: ChatQuestionRequestDto): Promise<ChatAnswer> {
    const dto = await NaviApiClient.generateAnswer(request);

    console.log('[NaviRepository] Raw DTO from API:', dto);

    // エラーレスポンスのチェック
    if (dto.status === 'error') {
      const { RagChatError } = await import('../domain/types/types');
      throw new RagChatError(
        dto.code || 'UNKNOWN_ERROR',
        dto.detail || 'エラーが発生しました',
        dto.hint
      );
    }

    // DTOからDomainモデルへの変換
    return {
      answer: dto.answer || '',
      pdfUrl: dto.merged_pdf_url ?? dto.pdf_url ?? null,
    };
  }
}
