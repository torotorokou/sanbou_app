// features/navi/model/dto.ts
// API通信用のDTO（Data Transfer Object）

/**
 * 質問送信時のリクエストDTO
 */
export interface ChatQuestionRequestDto {
  query: string;
  category: string;
  tags: string[];
}

/**
 * チャット回答レスポンスDTO（バックエンドから受け取る形式）
 */
export interface ChatAnswerResponseDto {
  // 成功時
  answer?: string;
  pdf_url?: string | null;
  merged_pdf_url?: string | null;
  
  // エラー時
  status?: "success" | "error";
  code?: string;
  detail?: string;
  hint?: string;
}

/**
 * カテゴリ・質問テンプレートオプションのレスポンスDTO
 */
export interface QuestionOptionsResponseDto {
  [category: string]: {
    title: string;
    tag: string[];
  }[];
}
