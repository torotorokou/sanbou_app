/**
 * sales-pivot/model/types.ts
 * 売上ピボット分析のドメイン型・Query型・DTO型
 *
 * 【概要】
 * このファイルは、売上ピボット分析機能で使用される全ての型定義を含みます。
 *
 * 【設計思想】
 * - ドメイン駆動設計（DDD）に基づいたドメインモデル
 * - FastAPI の Pydantic モデル、PostgreSQL の集計ビューと1対1対応を想定
 * - 型安全性を重視し、不正な状態を型レベルで排除
 *
 * 【将来計画】
 * - バックエンドAPI実装時に FastAPI の Pydantic スキーマと統合
 * - DB の集計マテリアライズドビューとのマッピング
 */

// ========================================
// 基本型定義
// ========================================

/**
 * 年月フォーマット
 * @example "2025-11", "2024-01"
 * @description 月次分析の基準となる年月。YYYY-MM形式の文字列
 */
export type YYYYMM = string;

/**
 * 年月日フォーマット
 * @example "2025-11-21", "2024-01-15"
 * @description 日次分析の基準となる年月日。YYYY-MM-DD形式の文字列
 */
export type YYYYMMDD = string;

/**
 * エンティティ識別子
 * @example "rep_a", "c_alpha", "i_001"
 * @description 各エンティティ（営業、顧客、品名等）を一意に識別するID
 */
export type ID = string;

// ========================================
// 分析モード・ソート関連
// ========================================

/**
 * 分析モード（集約軸）
 *
 * @description ピボット分析の主軸を定義。この軸に沿ってデータが集計される
 *
 * - `customer`: 顧客別集計 - 顧客ごとの売上・数量・件数を分析
 * - `item`: 品名別集計 - 商品ごとの売上・数量・件数を分析
 * - `date`: 日付別集計 - 日次の売上推移を時系列で分析
 *
 * @example
 * mode = 'customer' の場合、各顧客の売上が集計され、
 * Pivotドロワーでは「顧客 → 品名」「顧客 → 日付」の内訳を展開できる
 */
export type Mode = 'customer' | 'item' | 'date';

/**
 * ソートキー
 *
 * @description メトリクス（集計値）のソート基準
 *
 * - `amount`: 売上金額（円）でソート
 * - `qty`: 数量（kg）でソート
 * - `count`: 取引件数でソート
 * - `unit_price`: 単価（円/kg）でソート
 * - `date`: 日付でソート（date モード時のみ使用）
 * - `name`: 名称（顧客名/品名）でソート
 */
export type SortKey = 'amount' | 'qty' | 'count' | 'unit_price' | 'date' | 'name';

/**
 * ソート順
 *
 * @description 昇順・降順の指定
 * - `asc`: 昇順（小さい値から大きい値へ）
 * - `desc`: 降順（大きい値から小さい値へ）
 */
export type SortOrder = 'asc' | 'desc';

/**
 * カテゴリ種別
 *
 * @description 廃棄物/有価物の区分
 * - `waste`: 廃棄物
 * - `valuable`: 有価物
 */
export type CategoryKind = 'waste' | 'valuable';

// ========================================
// エンティティ型（マスタデータ）
// ========================================

/**
 * 売上担当（営業）エンティティ
 *
 * @description 営業担当者のマスタデータ
 * @property id - 営業担当者の一意識別子（例: "rep_a", "rep_001"）
 * @property name - 営業担当者の表示名（例: "営業A", "山田太郎"）
 */
export interface SalesRep {
  id: ID;
  name: string;
}

/**
 * マスタエントリ（顧客 / 品名 / 日付）
 *
 * @description 分析対象となるエンティティの汎用的な表現
 * 顧客マスタ、品名マスタ、日付リストで共通して使用
 *
 * @property id - エンティティの一意識別子
 * @property name - エンティティの表示名（顧客名、品名、日付文字列）
 * @property dateKey - 日付モード時のソート用キー（オプション、YYYY-MM-DD形式）
 *
 * @example
 * // 顧客マスタ
 * { id: 'c_alpha', name: '顧客アルファ' }
 *
 * // 品名マスタ
 * { id: 'i_a', name: '商品A' }
 *
 * // 日付エントリ
 * { id: 'd_2025-11-21', name: '2025-11-21', dateKey: '2025-11-21' }
 */
export interface UniverseEntry {
  id: ID;
  name: string;
  dateKey?: YYYYMMDD; // date モードのソート用（日付エントリの場合のみ使用）
}

// ========================================
// メトリクス・集計データ型
// ========================================

/**
 * メトリクスエントリ（集計結果）
 *
 * @description 売上分析の集計データを表す中心的な型
 * 顧客別・品名別・日付別のいずれの集計でも使用される汎用的な構造
 *
 * @property id - 集計対象エンティティのID
 * @property name - 集計対象の表示名（顧客名 | 品名 | 日付(YYYY-MM-DD)）
 * @property amount - 売上金額（円）
 * @property qty - 数量（kg）
 * @property lineCount - 明細行数（件数） - COUNT(*)
 * @property slipCount - 伝票数（台数） - COUNT(DISTINCT slip_no)
 * @property count - 表示用カウント値（商品軸=lineCount、それ以外=slipCount）
 * @property unitPrice - 単価（円/kg）。計算式: Σ金額 / Σ数量（数量=0の場合はnull）
 * @property dateKey - 日付モード時のソート用キー（オプション、YYYY-MM-DD形式）
 *
 * @example
 * // 顧客別集計の例（台数=slipCount）
 * {
 *   id: 'c_alpha',
 *   name: '顧客アルファ',
 *   amount: 1500000,
 *   qty: 500,
 *   lineCount: 20,  // 明細行数
 *   slipCount: 15,  // 伝票数（台数）
 *   count: 15,       // 表示値=slipCount
 *   unitPrice: 3000.00
 * }
 *
 * // 商品別集計の例（件数=lineCount）
 * {
 *   id: 'i_001',
 *   name: '商品A',
 *   amount: 800000,
 *   qty: 300,
 *   lineCount: 25,  // 明細行数（件数）
 *   slipCount: 18,  // 伝票数
 *   count: 25,       // 表示値=lineCount
 *   unitPrice: 2666.67
 * }
 */
export interface MetricEntry {
  id: ID;
  name: string;
  amount: number;
  qty: number;
  lineCount: number;
  slipCount: number;
  count: number;
  unitPrice: number | null;
  dateKey?: YYYYMMDD;
}

/**
 * サマリ行（営業ごとの TopN メトリクス）
 *
 * @description 営業担当者ごとの集計結果を格納
 * メイン画面のサマリテーブルで使用される
 *
 * @property repId - 営業担当者ID
 * @property repName - 営業担当者名
 * @property topN - その営業のTopNメトリクス配列（顧客Top10、品名Top20等）
 *
 * @example
 * {
 *   repId: 'rep_a',
 *   repName: '営業A',
 *   topN: [
 *     { id: 'c_alpha', name: '顧客アルファ', amount: 1500000, qty: 500, count: 15, unitPrice: 3000 },
 *     { id: 'c_bravo', name: '顧客ブラボー', amount: 1200000, qty: 400, count: 12, unitPrice: 3000 },
 *     // ... 以下TopN件
 *   ]
 * }
 */
export interface SummaryRow {
  repId: ID;
  repName: string;
  topN: MetricEntry[];
}

// ========================================
// クエリ型（Repository層への入力パラメータ）
// ========================================

/**
 * サマリ取得用クエリ（FastAPI / DB 集計ビューに渡す想定）
 *
 * @description サマリテーブル表示用のデータ取得パラメータ
 * メイン画面のフィルタ条件をそのままクエリとして表現
 *
 * @property month - 単月指定（例: "2025-11"）。monthRange と排他的
 * @property monthRange - 期間指定（例: { from: "2025-01", to: "2025-03" }）。month と排他的
 * @property mode - 集約軸（customer | item | date）
 * @property repIds - 対象営業ID配列（空配列の場合は全営業）
 * @property filterIds - フィルタID配列（空配列の場合は全件）。mode によって意味が変わる
 *   - mode='customer' の場合: 顧客IDでフィルタ
 *   - mode='item' の場合: 品名IDでフィルタ
 *   - mode='date' の場合: 未使用（空配列）
 * @property sortBy - ソートキー（amount | qty | count | unit_price | date | name）
 * @property order - ソート順（asc | desc）
 * @property topN - 取得件数（10 | 20 | 50 | 'all'）
 *
 * @example
 * // 2025年11月の顧客別Top10を売上降順で取得
 * {
 *   month: '2025-11',
 *   mode: 'customer',
 *   repIds: ['rep_a', 'rep_b'],
 *   filterIds: [],
 *   sortBy: 'amount',
 *   order: 'desc',
 *   topN: 10
 * }
 *
 * // 2025年1月～3月の品名別全件を数量降順で取得
 * {
 *   monthRange: { from: '2025-01', to: '2025-03' },
 *   mode: 'item',
 *   repIds: [],
 *   filterIds: [],
 *   sortBy: 'qty',
 *   order: 'desc',
 *   topN: 'all'
 * }
 */
export interface SummaryQuery {
  month?: YYYYMM;
  monthRange?: { from: YYYYMM; to: YYYYMM };
  dateFrom?: YYYYMMDD;
  dateTo?: YYYYMMDD;
  mode: Mode;
  categoryKind: CategoryKind;
  repIds: ID[];
  filterIds: ID[];
  sortBy: SortKey;
  order: SortOrder;
  topN: 10 | 20 | 50 | 'all';
}

/**
 * Pivot取得用クエリ（詳細ドリルダウン用）
 *
 * @description ピボットドロワーでの詳細展開用クエリ
 * 1つの軸を固定し、別の軸でデータを展開する（例: 「顧客A」の「品名別内訳」）
 *
 * @property month - 単月指定（例: "2025-11"）
 * @property monthRange - 期間指定（例: { from: "2025-01", to: "2025-03" }）
 * @property baseAxis - 固定軸（例: 'customer' - 顧客を固定）
 * @property baseId - 固定値のID（例: 'c_alpha' - 顧客アルファを固定）
 * @property repIds - 対象営業ID配列
 * @property targetAxis - 展開軸（例: 'item' - 品名別に展開）
 * @property sortBy - ソートキー
 * @property order - ソート順
 * @property topN - 取得件数
 * @property cursor - ページネーション用カーソル（次ページ取得時に使用）
 *
 * @example
 * // 顧客アルファの品名別内訳Top20を売上降順で取得
 * {
 *   month: '2025-11',
 *   baseAxis: 'customer',
 *   baseId: 'c_alpha',
 *   repIds: ['rep_a'],
 *   targetAxis: 'item',
 *   sortBy: 'amount',
 *   order: 'desc',
 *   topN: 20,
 *   cursor: null
 * }
 */
export interface PivotQuery {
  month?: YYYYMM;
  monthRange?: { from: YYYYMM; to: YYYYMM };
  dateFrom?: YYYYMMDD;
  dateTo?: YYYYMMDD;
  baseAxis: Mode;
  baseId: ID;
  categoryKind: CategoryKind;
  repIds: ID[];
  targetAxis: Mode;
  sortBy: SortKey;
  order: SortOrder;
  topN: 10 | 20 | 50 | 'all';
  cursor?: string | null;
}

/**
 * カーソルベースページネーション結果
 *
 * @description ページネーションのレスポンス型
 * @property rows - 取得されたデータ行配列
 * @property nextCursor - 次ページのカーソル（最終ページの場合はnull）
 *
 * @template T - ページネーション対象のデータ型（通常は MetricEntry）
 */
export interface CursorPage<T> {
  rows: T[];
  nextCursor: string | null;
}

/**
 * 日次推移取得用クエリ
 *
 * @description 日次推移グラフ（折れ線グラフ）用のデータ取得パラメータ
 *
 * @property month - 単月指定
 * @property monthRange - 期間指定
 * @property repId - 営業ID（オプション）
 * @property customerId - 顧客ID（オプション）
 * @property itemId - 品名ID（オプション）
 *
 * @example
 * // 営業Aの2025年11月の日次推移
 * { month: '2025-11', repId: 'rep_a' }
 *
 * // 顧客アルファの2025年1月～3月の日次推移
 * { monthRange: { from: '2025-01', to: '2025-03' }, customerId: 'c_alpha' }
 */
export interface DailySeriesQuery {
  month?: YYYYMM;
  monthRange?: { from: YYYYMM; to: YYYYMM };
  dateFrom?: YYYYMMDD;
  dateTo?: YYYYMMDD;
  categoryKind: CategoryKind;
  repId?: ID;
  customerId?: ID;
  itemId?: ID;
}

/**
 * 日次推移データポイント
 *
 * @description 日次推移グラフの1日分のデータ
 * @property date - 日付（YYYY-MM-DD）
 * @property amount - その日の売上金額
 * @property qty - その日の数量
 * @property lineCount - その日の明細行数（件数） - COUNT(*)
 * @property slipCount - その日の伝票数（台数） - COUNT(DISTINCT slip_no)
 * @property count - 表示用カウント値（現状は slipCount を使用）
 * @property unitPrice - その日の平均単価
 */
export interface DailyPoint {
  date: YYYYMMDD;
  amount: number;
  qty: number;
  lineCount: number;
  slipCount: number;
  count: number;
  unitPrice: number | null;
}

// ========================================
// CSV エクスポート関連
// ========================================

/**
 * CSV エクスポートオプション
 *
 * @description CSV出力時の詳細設定
 * Excel読み込み時のパフォーマンス対策や、データ構造のカスタマイズが可能
 *
 * @property excludeZero - 0実績行を除外するか（Excel負荷対策）
 *   - true: 売上・数量・件数が全て0の行を出力しない
 *   - false: 全ての行を出力（大量データの場合Excelが重くなる可能性）
 *
 * @property splitBy - 出力ファイルの分割方法
 *   - 'none': 単一ファイルに全営業のデータを出力
 *   - 'rep': 営業ごとに個別ファイルを出力
 *
 * @property addAxisB - 残りモード1を列に追加
 *   - 例: mode='customer'の場合、品名(item)を追加列として出力
 *   - 3次元データ（顧客 × 品名 × 日付）の一部を平面化
 *
 * @property addAxisC - 残りモード2を列に追加
 *   - 例: mode='customer'の場合、日付(date)を追加列として出力
 *
 * @example
 * // Excel負荷対策：0実績を除外し、営業ごとに分割
 * {
 *   excludeZero: true,
 *   splitBy: 'rep',
 *   addAxisB: false,
 *   addAxisC: false
 * }
 *
 * // 全データ出力：3次元データを完全展開
 * {
 *   excludeZero: false,
 *   splitBy: 'none',
 *   addAxisB: true,
 *   addAxisC: true
 * }
 */
export interface ExportOptions {
  excludeZero: boolean;
  splitBy: 'none' | 'rep';
  addAxisB: boolean;
  addAxisC: boolean;
}

/**
 * デフォルトエクスポートオプション
 *
 * @description 初期値として推奨される設定
 * - 0実績を除外してExcelパフォーマンスを確保
 * - 単一ファイル出力
 * - 追加列なし（シンプルな2次元データ）
 */
export const DEFAULT_EXPORT_OPTIONS: ExportOptions = {
  excludeZero: true,
  splitBy: 'none',
  addAxisB: false,
  addAxisC: false,
};

/**
 * CSV エクスポート用クエリ
 *
 * @description CSV出力時に Repository に渡すクエリ
 * SummaryQuery を継承し、出力オプションと対象営業を追加
 *
 * @property options - エクスポートオプション
 * @property targetRepIds - 出力対象の営業ID配列（repIds のサブセット）
 */
export interface ExportQuery extends SummaryQuery {
  options: ExportOptions;
  targetRepIds: ID[];
}

// ========================================
// UI状態管理型
// ========================================

/**
 * Drawer状態（閉じている or 開いている）
 *
 * @description Pivotドロワーの状態を型安全に管理
 * Discriminated Union型により、開閉状態で利用可能なプロパティが変わる
 *
 * @example
 * // ドロワーが閉じている場合
 * const drawer: DrawerState = { open: false };
 * // この場合、他のプロパティにはアクセスできない（型エラー）
 *
 * // ドロワーが開いている場合
 * const drawer: DrawerState = {
 *   open: true,
 *   baseAxis: 'customer',
 *   baseId: 'c_alpha',
 *   baseName: '顧客アルファ',
 *   month: '2025-11',
 *   repIds: ['rep_a'],
 *   targets: [
 *     { axis: 'item', label: '品名' },
 *     { axis: 'date', label: '日付' }
 *   ],
 *   activeAxis: 'item',
 *   sortBy: 'amount',
 *   order: 'desc',
 *   topN: 20
 * };
 *
 * @property open - ドロワーの開閉状態
 *
 * --- open が true の場合のみ以下のプロパティが存在 ---
 * @property baseAxis - 固定軸（例: 'customer' - 顧客を固定してドリルダウン）
 * @property baseId - 固定エンティティのID（例: 'c_alpha'）
 * @property baseName - 固定エンティティの表示名（例: '顧客アルファ'）
 * @property month - 単月指定（monthRange と排他的）
 * @property monthRange - 期間指定（month と排他的）
 * @property repIds - 対象営業ID配列
 * @property targets - 展開可能な軸の配列（例: [{ axis: 'item', label: '品名' }]）
 * @property activeAxis - 現在選択されている展開軸（タブ切り替え用）
 * @property sortBy - ソートキー
 * @property order - ソート順
 * @property topN - 表示件数
 */
export type DrawerState =
  | { open: false }
  | {
      open: true;
      baseAxis: Mode;
      baseId: ID;
      baseName: string;
      month?: YYYYMM;
      monthRange?: { from: YYYYMM; to: YYYYMM };
      dateFrom?: YYYYMMDD;
      dateTo?: YYYYMMDD;
      repIds: ID[];
      targets: { axis: Mode; label: string }[];
      activeAxis: Mode;
      sortBy: SortKey;
      order: SortOrder;
      topN: 10 | 20 | 50 | 'all';
    };

// ========================================
// 詳細明細行関連型（Detail Lines）
// ========================================

/**
 * 詳細表示モード
 *
 * @description 詳細テーブルの粒度を定義
 * - `item_lines`: 品名明細行レベル（最後の軸が item の場合）
 * - `slip_summary`: 伝票単位サマリ（最後の軸が item 以外の場合）
 */
export type DetailMode = 'item_lines' | 'slip_summary';

/**
 * 集計軸種別
 *
 * @description 集計パスの各階層で使用される軸の種別
 * - `rep`: 営業
 * - `customer`: 顧客
 * - `date`: 日付
 * - `item`: 品名
 */
export type GroupBy = 'rep' | 'customer' | 'date' | 'item';

/**
 * 詳細明細行（またはサマリ行）
 *
 * @description 集計行クリック時に表示する詳細データの1行
 * mode により内容が変わる:
 * - item_lines: 明細行そのまま（品名まで含む）
 * - slip_summary: 伝票単位の集約（品名は含まない）
 *
 * @property mode - 詳細表示モード
 * @property salesDate - 売上日
 * @property slipNo - 伝票No（receive_no）
 * @property slipTypeName - 伝票種別（売上/仕入など）
 * @property itemId - 品目ID（item_lines時のみ）
 * @property itemName - 品目名（item_lines時のみ）
 * @property lineCount - 明細行数（slip_summary時のみ）
 * @property qtyKg - 数量（kg）
 * @property unitPriceYenPerKg - 単価（円/kg）
 * @property amountYen - 金額（円）
 */
export interface DetailLine {
  mode: DetailMode;
  salesDate: string;
  slipNo: number;
  repName: string;
  customerName: string;
  itemId: number | null;
  itemName: string | null;
  lineCount: number | null;
  qtyKg: number;
  unitPriceYenPerKg: number | null;
  amountYen: number;
}

/**
 * 詳細明細行取得リクエスト
 *
 * @description 詳細テーブル表示のためのフィルタ条件
 *
 * @property dateFrom - 集計開始日（YYYY-MM-DD）
 * @property dateTo - 集計終了日（YYYY-MM-DD）
 * @property lastGroupBy - 最後の集計軸（rep, customer, date, item）
 * @property categoryKind - カテゴリ種別（waste, valuable）
 * @property repId - 営業IDフィルタ
 * @property customerId - 顧客IDフィルタ
 * @property itemId - 品目IDフィルタ
 * @property dateValue - 日付フィルタ（YYYY-MM-DD）
 */
export interface DetailLinesFilter {
  dateFrom: string;
  dateTo: string;
  lastGroupBy: GroupBy;
  categoryKind: CategoryKind;
  repId?: number;
  customerId?: string;
  itemId?: number;
  dateValue?: string;
}

/**
 * 詳細明細行取得レスポンス
 *
 * @description 詳細テーブル表示用データ
 *
 * @property mode - 返却データのモード
 * @property rows - 詳細明細行リスト
 * @property totalCount - 総行数
 */
export interface DetailLinesResponse {
  mode: DetailMode;
  rows: DetailLine[];
  totalCount: number;
}
