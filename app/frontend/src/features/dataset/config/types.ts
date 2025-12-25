/**
 * データセット設定の型定義
 *
 * すべてのデータセット関連定義（CSV種別、ラベル、色、順序、必須ヘッダ、
 * ファイル名ヒント、プレビュー設定、アップロード先など）を統一管理する。
 */

import type { CsvKind } from "../shared/types/csvKind";

export type DatasetKey =
  | "shogun_flash_debug"
  | "shogun_flash"
  | "shogun_final"
  | "manifest";

export type CsvTypeKey =
  | "receive"
  | "shipment"
  | "yard"
  | CsvKind
  | "manifest_primary"
  | "manifest_secondary";

/**
 * CSV設定（個別CSV種別の定義）
 */
export type CsvConfig = {
  /** CSV種別キー */
  typeKey: CsvTypeKey;
  /** 表示ラベル */
  label: string;
  /** 必須かどうか */
  required: boolean;
  /** タブ表示順序（小さいほど前） */
  order: number;
  /** UIカラー（背景色） */
  color?: string;
  /** ファイル名推定ヒント（部分一致） */
  filenameHints?: string[];
  /** ファイル名推定用の正規表現（文字列で保持、selectors側でRegExpに変換） */
  filenameRegex?: string;
  /** パース設定 */
  parse: {
    encoding: "utf8" | "sjis";
    delimiter: "," | "\t" | ";";
  };
  /** プレビュー表示設定 */
  preview?: {
    columnWidth?: number;
    stickyHeader?: boolean;
  };
  /** 検証設定 */
  validate: {
    /** 必須ヘッダ列名 */
    requiredHeaders: string[];
    /** 行バリデータ識別子（実体は dataset-validate 側で解決） */
    rowSchemaName?: string;
  };
};

/**
 * データセット設定（データセット全体の定義）
 */
export type DatasetConfig = {
  /** データセットキー */
  key: DatasetKey;
  /** 表示ラベル */
  label: string;
  /** CSV設定の配列 */
  csv: CsvConfig[];
  /** アップロード設定 */
  upload: {
    /** アップロード先パス */
    path: string;
    /** ペイロード形式 */
    payloadShape?: "formData" | "json";
    /** 最大ファイル数 */
    maxFiles?: number;
  };
  /** ユーザー向け注意事項 */
  notes?: string[];
  /** スキーマバージョン（将来の拡張用） */
  schemaVersion: number;
};
