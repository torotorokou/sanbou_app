/**
 * shared/ui/styles.ts
 * 売上ピボット機能の共通スタイル定義
 *
 * 【概要】
 * Feature全体で使用される共通CSSスタイルを文字列として提供
 * グローバルCSSまたは <style> タグで注入して使用
 *
 * 【設計思想】
 * - BEM記法ライクなクラス命名（sales-tree-*, app-*）
 * - アクセントカラーによる視覚的階層化
 * - 再利用可能なユーティリティクラス
 *
 * 【使用方法】
 * ```tsx
 * import { salesPivotStyles } from '@/features/analytics/sales-pivot';
 *
 * // グローバルスタイルとして注入（ルートコンポーネント等）
 * <style dangerouslySetInnerHTML={{ __html: salesPivotStyles }} />
 *
 * // コンポーネント内で使用
 * <Card className="sales-tree-accent-card sales-tree-accent-primary">
 *   <div className="sales-tree-card-section-header">セクションタイトル</div>
 *   ...
 * </Card>
 * ```
 *
 * 【主要クラス一覧】
 * - `.app-header` - ヘッダー全体コンテナ
 * - `.app-title` - タイトルテキスト
 * - `.app-title-accent` - アクセント付きタイトル（左縦線）
 * - `.app-header-actions` - ヘッダー右側アクションボタンエリア
 * - `.accent-card` - アクセント付きCard（左ボーダー）
 * - `.accent-primary` - プライマリカラー（緑系）
 * - `.accent-secondary` - セカンダリカラー（明るい緑系）
 * - `.accent-gold` - ゴールドカラー
 * - `.card-section-header` - カード内セクションヘッダー
 * - `.mini-bar-*` - ミニバーチャート用クラス群
 */

export const salesPivotStyles = `
  /* ========================================
   * ヘッダー関連スタイル
   * ======================================== */

  /**
   * ヘッダー全体コンテナ
   * 相対配置でアクションボタンエリアを右上に配置可能にする
   */
  .app-header {
    position: relative;
    padding: 12px 0 4px;
  }

  /**
   * タイトルテキスト（中央揃え）
   */
  .app-title {
    text-align: center;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin: 0;
  }

  /**
   * アクセント付きタイトル
   * 左側に縦の緑色バー（::before疑似要素）を表示
   */
  .app-title-accent {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding-left: 8px;
    color: #000;
    font-weight: 700;
    line-height: 1.2;
    font-size: 1.05em;
  }

  .app-title-accent::before {
    content: "";
    display: inline-block;
    width: 6px;
    height: 22px;
    background: #237804;
    border-radius: 3px;
  }

  /**
   * ヘッダー右側アクションボタンエリア
   * 絶対配置で右上に固定
   */
  .app-header-actions {
    position: absolute;
    right: 0;
    top: 8px;
    display: flex;
    gap: 8px;
  }

  /* ========================================
   * カード・アクセント関連スタイル
   * ======================================== */

  /**
   * アクセント付きCard基底クラス
   * 左側に太いボーダーを表示して視覚的な区別を付ける
   */
  .accent-card {
    border-left: 4px solid #23780410;
    overflow: hidden;
  }

  /**
   * プライマリアクセント（濃い緑）
   * 重要度の高いカードに使用
   */
  .accent-primary {
    border-left-color: #237804;
  }

  /**
   * セカンダリアクセント（明るい緑）
   * サブコンテンツやドロワー内で使用
   */
  .accent-secondary {
    border-left-color: #52c41a;
  }

  /**
   * ゴールドアクセント
   * 特別な情報や注意喚起に使用
   */
  .accent-gold {
    border-left-color: #faad14;
  }

  /**
   * カード内セクションヘッダー
   * セクションの見出しとして使用（緑背景）
   */
  .card-section-header {
    font-weight: 600;
    padding: 6px 10px;
    margin-bottom: 12px;
    border-radius: 6px;
    background: #f3fff4;
    border: 1px solid #e6f7e6;
  }

  /**
   * カード内サブタイトル
   * グレー系の補助テキスト
   */
  .card-subtitle {
    color: rgba(0, 0, 0, 0.55);
    margin-bottom: 6px;
    font-size: 12px;
  }

  /* ========================================
   * ミニバーチャート関連スタイル
   * ======================================== */

  /**
   * ミニバー背景（グレーのバー全体）
   */
  .mini-bar-bg {
    flex: 1;
    height: 6px;
    background: #f6f7fb;
    border-radius: 4px;
    overflow: hidden;
  }

  /**
   * ミニバー本体（進捗バー）
   */
  .mini-bar {
    height: 100%;
  }

  /**
   * 青色バー（プライマリデータ用）
   */
  .mini-bar-blue {
    background: #237804;
  }

  /**
   * 緑色バー（セカンダリデータ用）
   */
  .mini-bar-green {
    background: #52c41a;
  }

  /**
   * ゴールドバー（ハイライト用）
   */
  .mini-bar-gold {
    background: #faad14;
  }

  .zebra-even {
    background: #ffffff;
  }

  .zebra-odd {
    background: #fbfcfe;
  }

  .ant-table-tbody > tr:hover > td {
    background: #f6fff4 !important;
  }

  .ant-table-header {
    box-shadow: inset 0 -1px 0 #f0f0f0;
  }

  .summary-tags {
    font-size: 14px;
  }

  .summary-tags .ant-tag {
    font-size: 14px;
    padding: 0 10px;
  }
`;
