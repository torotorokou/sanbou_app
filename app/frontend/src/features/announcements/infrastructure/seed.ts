/**
 * Seed Data - お知らせのダミーデータ
 * 
 * MVP用のフロント固定データ。後でAPIからの取得に差し替え予定。
 * 
 * 【テストケース】
 * - ann-001: critical + publishToあり + audience=all + attachments(pdf) + notification(email, sendOnPublish)
 * - ann-002: info + audience=all + notification無し（互換確認：inApp扱い）
 * - ann-003: critical + audience=all + attachments(link) + notification(inApp, email)
 * - ann-004: info + audience=all + タグあり
 * - ann-005: info + audience=all
 * - ann-006: warn + audience=all + notification(line, scheduledAt)
 * - ann-007: info + audience=site:narita（対象限定テスト）
 * - ann-008: info + audience=site:shinkiba（対象限定テスト）
 * - ann-009: info + audience=internal + タグあり + attachments
 * - ann-010: info + 期限切れ（表示されない確認用）
 * - ann-011: info + 未来開始（表示されない確認用）
 */

import type { Announcement } from '../domain/announcement';

/**
 * サンプルお知らせデータ
 */
export const ANNOUNCEMENT_SEEDS: Announcement[] = [
  {
    id: 'ann-001',
    title: 'システムメンテナンスのお知らせ',
    bodyMd: `## システムメンテナンス実施のお知らせ

**実施日時**: 2025年12月28日（土） 02:00 〜 05:00

上記時間帯にてシステムメンテナンスを実施いたします。

### 影響範囲
- 全サービスが一時的に利用不可となります
- メンテナンス終了後、正常に復旧予定です

### お願い
- メンテナンス開始前に作業中のデータを保存してください
- 緊急のお問い合わせは管理者までご連絡ください

ご不便をおかけしますが、ご理解のほどよろしくお願いいたします。`,
    severity: 'warn',
    tags: ['メンテナンス', 'システム'],
    publishFrom: '2024-12-01T00:00:00Z',
    publishTo: '2025-12-31T23:59:59Z',
    audience: 'all',
    attachments: [
      {
        label: 'メンテナンス詳細資料',
        url: 'https://example.com/maintenance-detail.pdf',
        kind: 'pdf',
      },
    ],
    notification: {
      channels: ['inApp', 'email'],
      sendOnPublish: true,
    },
  },
  {
    id: 'ann-002',
    title: '新機能リリースのお知らせ',
    bodyMd: `## 新機能リリースのお知らせ

本日、以下の新機能をリリースいたしました。

### 追加機能
1. **ダッシュボード改善** - 表示速度が向上しました
2. **CSVインポート機能強化** - 大容量ファイルに対応
3. **帳票出力** - PDF出力オプションを追加

### 改善点
- ユーザーインターフェースの改善
- パフォーマンスの最適化

ぜひご活用ください！`,
    severity: 'info',
    publishFrom: '2024-12-01T00:00:00Z',
    publishTo: null,
    audience: 'all',
    // notification無し: inApp扱い（互換確認）
  },
  {
    id: 'ann-003',
    title: '【重要】セキュリティアップデートのお知らせ',
    bodyMd: `## 重要なセキュリティアップデート

セキュリティ強化のため、以下の対応を実施しました。

### 対応内容
- 認証システムの強化
- パスワードポリシーの更新
- ログイン監視機能の追加

### ユーザーへのお願い
- 定期的なパスワード変更をお願いします
- 不審なログイン通知があった場合は管理者へ連絡してください

セキュリティ向上にご協力をお願いいたします。`,
    severity: 'critical',
    tags: ['セキュリティ', '重要'],
    publishFrom: '2024-12-01T00:00:00Z',
    publishTo: '2025-12-31T23:59:59Z',
    audience: 'all',
    attachments: [
      {
        label: 'セキュリティガイドライン',
        url: 'https://example.com/security-guideline',
        kind: 'link',
      },
    ],
    notification: {
      channels: ['inApp', 'email'],
      sendOnPublish: true,
      templateHint: 'security-alert',
    },
  },
  {
    id: 'ann-004',
    title: '年末年始の営業時間のお知らせ',
    bodyMd: `## 年末年始の営業時間について

年末年始の営業時間をお知らせいたします。

### 営業日時
- 12月29日（金）まで: 通常営業
- 12月30日（土）〜1月3日（水）: 休業
- 1月4日（木）より: 通常営業

緊急のお問い合わせは緊急連絡先までご連絡ください。`,
    severity: 'info',
    tags: ['営業時間', '年末年始'],
    publishFrom: '2024-12-01T00:00:00Z',
    publishTo: null,
    audience: 'all',
  },
  {
    id: 'ann-005',
    title: 'サーバー増強作業完了のお知らせ',
    bodyMd: `## サーバー増強作業完了

サーバー増強作業が完了しました。

### 改善内容
- レスポンス速度が約30%向上
- 同時接続数の上限を拡大
- データ処理性能の向上

快適にご利用いただけるようになりました。`,
    severity: 'info',
    publishFrom: '2024-12-01T00:00:00Z',
    publishTo: null,
    audience: 'all',
  },
  {
    id: 'ann-006',
    title: '【注意】不正アクセスに関する注意喚起',
    bodyMd: `## 不正アクセスに関する注意喚起

最近、フィッシング詐欺が増加しています。

### 注意点
- 不審なメールのリンクをクリックしない
- パスワードを他人に教えない
- 定期的なパスワード変更を実施

セキュリティ意識を高めてご利用ください。`,
    severity: 'warn',
    tags: ['セキュリティ', '注意喚起'],
    publishFrom: '2024-12-01T00:00:00Z',
    publishTo: null,
    audience: 'all',
    notification: {
      channels: ['inApp', 'line'],
      sendOnPublish: false,
      scheduledAt: '2025-12-25T09:00:00Z',
    },
  },
  {
    id: 'ann-007',
    title: '【成田】成田拠点向けお知らせ',
    bodyMd: `## 成田拠点向けお知らせ

成田拠点のユーザーのみに表示されるテスト用お知らせです。

### 内容
- 成田拠点限定の情報
- ローカルイベント案内

対象拠点のみ表示されます。`,
    severity: 'info',
    tags: ['成田', '拠点限定'],
    publishFrom: '2024-12-01T00:00:00Z',
    publishTo: null,
    audience: 'site:narita',
    notification: {
      channels: ['inApp'],
      sendOnPublish: false,
    },
  },
  {
    id: 'ann-008',
    title: '【新木場】新木場拠点向けお知らせ',
    bodyMd: `## 新木場拠点向けお知らせ

新木場拠点のユーザーのみに表示されるテスト用お知らせです。

### 内容
- 新木場拠点限定の情報
- ローカルイベント案内

対象拠点のみ表示されます。`,
    severity: 'info',
    tags: ['新木場', '拠点限定'],
    publishFrom: '2024-12-01T00:00:00Z',
    publishTo: null,
    audience: 'site:shinkiba',
    notification: {
      channels: ['inApp'],
      sendOnPublish: false,
    },
  },
  {
    id: 'ann-009',
    title: '社内向けドキュメント更新のお知らせ',
    bodyMd: `## ヘルプドキュメント更新

マニュアルとFAQを更新しました。

新機能の使い方や、よくある質問への回答を追加しています。
ぜひご参照ください。`,
    severity: 'info',
    tags: ['ドキュメント', '更新'],
    publishFrom: '2024-12-01T00:00:00Z',
    publishTo: null,
    audience: 'internal',
    attachments: [
      {
        label: 'マニュアル（PDF）',
        url: 'https://example.com/manual.pdf',
        kind: 'pdf',
      },
      {
        label: 'FAQページ',
        url: 'https://example.com/faq',
        kind: 'link',
      },
    ],
  },
  {
    id: 'ann-010',
    title: '【期限切れテスト】このお知らせは表示されません',
    bodyMd: `## 期限切れテスト

このお知らせは期限切れのため、一覧に表示されないはずです。`,
    severity: 'info',
    publishFrom: '2024-01-01T00:00:00Z',
    publishTo: '2024-11-30T23:59:59Z', // 過去の日付
    audience: 'all',
  },
  {
    id: 'ann-011',
    title: '【未来開始テスト】このお知らせは表示されません',
    bodyMd: `## 未来開始テスト

このお知らせは公開開始前のため、一覧に表示されないはずです。`,
    severity: 'info',
    publishFrom: '2099-01-01T00:00:00Z', // 未来の日付
    publishTo: null,
    audience: 'all',
  },
];
