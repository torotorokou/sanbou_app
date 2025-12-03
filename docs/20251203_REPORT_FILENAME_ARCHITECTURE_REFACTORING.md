# 帳票ファイル名アーキテクチャのリファクタリング

**日付**: 2025-12-03  
**担当**: GitHub Copilot  
**ブランチ**: fix/report-issues

## 概要

帳票ダウンロード機能において、日本語ファイル名をバックエンドからフロントエンドへ移行する包括的なアーキテクチャ変更を実施。HTTPヘッダーのエンコーディング制約と国際化対応を改善。

## 問題の背景

### 旧アーキテクチャの課題

1. **HTTPヘッダー制約**
   - HTTPヘッダーは`latin-1`エンコーディングのみサポート
   - 日本語文字を含むファイル名でUnicodeEncodeError発生
   - RFC 5987エンコーディングが必要（複雑な実装）

2. **ファイルシステム依存**
   - OS依存の文字コード問題
   - パス区切り文字の違い（Windows/Unix）
   - ファイル名の正規化が困難

3. **保守性の問題**
   - バックエンドで日本語ラベルをYAMLから取得
   - エンコーディング処理が複数箇所に分散
   - エラーハンドリングが複雑

4. **国際化対応の困難**
   - ユーザー言語設定に応じた切替が不可能
   - 翻訳管理がバックエンドとフロントエンドに分散

## 新アーキテクチャ

### 設計方針

**責務の分離原則（Separation of Concerns）に基づく設計:**

| レイヤー | 責務 | 使用文字セット |
|---------|------|--------------|
| **バックエンド** | ファイル保存・配信 | ASCII安全な英語キー |
| **フロントエンド** | ファイル名変換・ダウンロード | 日本語（Unicode） |

### メリット

#### バックエンド側
- ✅ HTTPヘッダー制約の完全回避（ASCII文字のみ）
- ✅ ファイルシステムの互換性向上
- ✅ シンプルなコード（エンコーディング処理不要）
- ✅ パフォーマンス改善（文字列変換処理削減）

#### フロントエンド側
- ✅ ブラウザAPIの完全活用（BlobAPI、URLオブジェクト）
- ✅ 国際化（i18n）との自然な統合
- ✅ ユーザー言語設定に応じた柔軟な切替
- ✅ 翻訳管理の一元化

## 実装内容

### 1. バックエンド修正

#### artifact_service.py

**変更前:**
```python
def allocate(self, report_key: str, report_date: str) -> ArtifactLocation:
    token = f"{report_date.replace('-', '')}_{time.strftime('%H%M%S')}-{secrets.token_hex(4)}"
    # 日本語ラベルを取得してファイル名に使用
    japanese_label = self._get_japanese_label(report_key)
    file_base = _sanitize_segment(f"{japanese_label}-{report_date}")
    ...
```

**変更後:**
```python
def allocate(self, report_key: str, report_date: str) -> ArtifactLocation:
    token = f"{report_date.replace('-', '')}_{time.strftime('%H%M%S')}-{secrets.token_hex(4)}"
    # 英語キーをそのまま使用（ASCII安全、フロントエンドで日本語変換）
    file_base = _sanitize_segment(f"{report_key}-{report_date}")
    ...
```

**削除した機能:**
- `_get_japanese_label()` メソッド
- `ReportTemplateConfigLoader` インポート
- YAML設定からの日本語ラベル取得ロジック

#### report_artifacts.py

**変更前:**
```python
# RFC 5987に準拠した日本語ファイル名のエンコーディング
try:
    filename.encode('ascii')
    response.headers["Content-Disposition"] = f'{disposition_value}; filename="{filename}"'
except UnicodeEncodeError:
    encoded_filename = quote(filename, safe='')
    response.headers["Content-Disposition"] = f"{disposition_value}; filename*=UTF-8''{encoded_filename}"

# X-Report-Artifact ヘッダーもエンコードが必要
try:
    artifact_path.encode('ascii')
    response.headers["X-Report-Artifact"] = artifact_path
except UnicodeEncodeError:
    response.headers["X-Report-Artifact"] = quote(artifact_path, safe='/')
```

**変更後:**
```python
# バックエンドは英語キーのみ使用（ASCII安全）
disposition_value = "inline" if disposition == "inline" else "attachment"
response.headers["Content-Disposition"] = f'{disposition_value}; filename="{resolved_path.name}"'
response.headers["X-Report-Artifact"] = artifact_path
```

**削除した機能:**
- RFC 5987エンコーディング処理
- try-exceptによるUnicodeエラーハンドリング
- `urllib.parse.quote` インポート

### 2. フロントエンド実装

#### reportKeyTranslation.ts（新規作成）

```typescript
/**
 * 帳票キーの英語・日本語変換ユーティリティ
 */

export const REPORT_KEY_TO_JAPANESE: Record<string, string> = {
    factory_report: '工場日報',
    balance_sheet: '収支表',
    average_sheet: '平均表',
    management_sheet: '管理表',
    block_unit_price: 'ブロック単価表',
    ledger_book: '台帳',
    factory_report2: '工場実績報告書',
} as const;

export const translateReportKeyToJapanese = (reportKey: string): string => {
    return REPORT_KEY_TO_JAPANESE[reportKey] || reportKey;
};

export const generateJapaneseFilename = (
    reportKey: string,
    reportDate: string,
    extension: string = '.xlsx'
): string => {
    const japaneseLabel = translateReportKeyToJapanese(reportKey);
    return `${japaneseLabel}-${reportDate}${extension}`;
};
```

#### useReportArtifact.ts

**変更前:**
```typescript
const downloadExcel = useCallback(() => {
    if (state.excelUrl) {
        window.open(state.excelUrl, '_blank', 'noopener');
    } else {
        notifyInfo('ダウンロード不可', 'Excel ダウンロード URL がありません。');
    }
}, [state.excelUrl]);
```

**変更後:**
```typescript
const downloadExcel = useCallback(async () => {
    if (!state.excelUrl) {
        notifyInfo('ダウンロード不可', 'Excel ダウンロード URL がありません。');
        return;
    }

    try {
        // URLからファイルをダウンロード
        const response = await fetch(state.excelUrl);
        if (!response.ok) throw new Error('ダウンロードに失敗しました');
        
        const blob = await response.blob();
        
        // report_keyから日本語ファイル名を生成
        let filename = 'report.xlsx';
        if (state.reportKey && state.reportDate) {
            filename = generateJapaneseFilename(state.reportKey, state.reportDate, '.xlsx');
        }
        
        // Blob URLを作成してダウンロード
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        notifyError(
            'ダウンロード失敗',
            error instanceof Error ? error.message : 'Excelのダウンロードに失敗しました'
        );
    }
}, [state.excelUrl, state.reportKey, state.reportDate]);
```

**追加機能:**
- Blob APIによるファイル取得
- 日本語ファイル名の動的生成
- エラーハンドリングの改善
- リソースクリーンアップ（URL.revokeObjectURL）

## ファイル変更一覧

### バックエンド
- ✏️ `app/backend/ledger_api/app/infra/adapters/artifact_storage/artifact_service.py`
  - `allocate()`: 英語キーでファイル名生成
  - `_get_japanese_label()`: 削除
  - `ReportTemplateConfigLoader`: インポート削除

- ✏️ `app/backend/ledger_api/app/api/routers/report_artifacts.py`
  - RFC 5987エンコーディング処理削除
  - try-exceptブロック削減
  - `urllib.parse.quote`: インポート削除

### フロントエンド
- ✨ `app/frontend/src/features/report/shared/lib/reportKeyTranslation.ts`（新規）
  - 帳票キー翻訳ユーティリティ
  - 日本語ファイル名生成関数

- ✏️ `app/frontend/src/features/report/preview/model/useReportArtifact.ts`
  - `downloadExcel()`: Blob APIによるダウンロード実装
  - 日本語ファイル名の動的生成
  - エラーハンドリング改善

## テスト計画

### 動作確認項目

1. **ファイル名検証**
   - [ ] 工場日報: `工場日報-2024-12-03.xlsx`
   - [ ] 収支表: `収支表-2024-12-03.xlsx`
   - [ ] 平均表: `平均表-2024-12-03.xlsx`
   - [ ] 管理表: `管理表-2024-12-03.xlsx`
   - [ ] ブロック単価表: `ブロック単価表-2024-12-03.xlsx`

2. **ブラウザ互換性**
   - [ ] Chrome（最新版）
   - [ ] Firefox（最新版）
   - [ ] Safari（最新版）
   - [ ] Edge（最新版）

3. **エラーハンドリング**
   - [ ] ネットワークエラー時の通知
   - [ ] 404エラー時の処理
   - [ ] タイムアウト時の処理

4. **パフォーマンス**
   - [ ] 大容量ファイル（>10MB）のダウンロード
   - [ ] 連続ダウンロード時のメモリリーク確認

## 今後の拡張

### 国際化対応（将来実装）

```typescript
// i18n統合例
import { useTranslation } from 'react-i18next';

const { t } = useTranslation('reports');
const japaneseLabel = t(`reportKeys.${reportKey}`);
```

### 設定ファイル連携

```typescript
// YAML設定との自動同期
import reportConfig from '@config/manage_report_masters.yaml';

export const REPORT_KEY_TO_JAPANESE = Object.fromEntries(
    Object.entries(reportConfig).map(([key, config]) => [key, config.label])
);
```

## 参考資料

- [RFC 5987: Character Set and Language Encoding for HTTP Header Field Parameters](https://datatracker.ietf.org/doc/html/rfc5987)
- [MDN: Blob API](https://developer.mozilla.org/en-US/docs/Web/API/Blob)
- [MDN: URL.createObjectURL()](https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL)
- [Clean Architecture: Separation of Concerns](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

## まとめ

本リファクタリングにより、以下の改善を達成:

1. **技術的負債の解消**: HTTPヘッダーエンコーディングの複雑な処理を排除
2. **保守性の向上**: 責務の明確な分離によるコードの簡潔化
3. **拡張性の確保**: 国際化対応への道筋を確立
4. **パフォーマンス改善**: 不要な文字列変換処理を削減

プロフェッショナルなアーキテクチャ設計により、長期的な保守性と拡張性を実現。
