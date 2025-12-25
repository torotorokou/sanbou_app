/**
 * UploadGuide 用の UI 専用型定義
 * PanelFileItem から UI で必要な情報を抽出して保持
 */

export type FileState = {
  /** CSV種別キー（例: 'shogun_flash_ship'） */
  typeKey: string;
  /** 表示名（例: '将軍_速報版:出荷一覧'） */
  label: string;
  /** 必須ファイルか */
  required: boolean;
  /** 検証状態 */
  status: "unknown" | "valid" | "invalid";
  /** 検証エラー時の欠落ヘッダ一覧（optional） */
  missingHeaders?: string[];
};
