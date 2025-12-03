# ヘルスチェック機能のプロフェッショナルなリファクタリング

**日付**: 2025-12-03  
**ステータス**: 提案中  
**影響範囲**: フロントエンド、バックエンド監視戦略

## 背景

ログ調査により、以下の問題が発見されました:

1. フロントエンドから30秒ごとにヘルスチェックAPIを呼び出し
2. 大量のログ出力とネットワーク負荷
3. ヘルスチェック(インフラ監視)とエラーハンドリング(UX)の責務混在

## プロフェッショナルな構成

### 3層のヘルスチェック戦略

```
┌─────────────────────────────────────────────────────────────┐
│ 1. インフラレベル (Docker/Kubernetes HEALTHCHECK)         │
│    - 目的: コンテナ生存確認、自動再起動                    │
│    - 実装済み: 各Dockerfile に HEALTHCHECK 設定           │
│    - 間隔: 30秒                                             │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. APM/監視ツール (Prometheus, Grafana, GCP Monitoring)   │
│    - 目的: サービス全体の健全性監視、アラート              │
│    - メトリクス: レスポンスタイム、エラー率、可用性         │
│    - 通知: Slack, メール, PagerDuty                        │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. ユーザー体験 (フロントエンド)                           │
│    - 目的: 実際のAPI呼び出し時のエラーハンドリング         │
│    - 実装: Axios interceptor で統一的にエラー処理          │
│    - 表示: 具体的な操作に関するエラーメッセージ            │
└─────────────────────────────────────────────────────────────┘
```

## 改善内容

### ❌ 削除するもの

1. **App.tsx からの自動ヘルスチェック実行**
   ```tsx
   // Before: 削除
   useSystemHealth({
       enabled: true,  // ← これが問題
       interval: 30000,
       showNotifications: true,
   });
   ```

2. **定期ポーリングロジック**
   - useEffect による setInterval 実行
   - 不要な通知ロジック

### ✅ 維持するもの

1. **バックエンドの /health エンドポイント**
   - Docker HEALTHCHECK が使用
   - 監視ツールのプローブ先として必要

2. **useSystemHealth hook (オンデマンド用)**
   ```tsx
   // 管理画面で手動実行用に残す
   const { status, checkHealth, isChecking } = useSystemHealth();
   
   return (
       <Button onClick={checkHealth} loading={isChecking}>
           システム状態を確認
       </Button>
   );
   ```

### 🆕 追加するもの

1. **Axios interceptor によるエラーハンドリング**
   ```typescript
   // src/shared/api/interceptors.ts
   axios.interceptors.response.use(
       (response) => response,
       (error) => {
           // サービスごとの適切なエラーメッセージ表示
           if (error.response?.status === 503) {
               notifyError('サービス一時停止中', '後ほど再度お試しください');
           }
           return Promise.reject(error);
       }
   );
   ```

2. **管理画面用のシステムステータスページ**
   ```tsx
   // pages/admin/SystemStatus.tsx
   export const SystemStatusPage = () => {
       const { status, checkHealth, isChecking, lastChecked } = useSystemHealth();
       
       return (
           <Card>
               <Button onClick={checkHealth}>今すぐチェック</Button>
               {status && <ServiceStatusTable services={status.services} />}
           </Card>
       );
   };
   ```

## メリット

### パフォーマンス
- ネットワーク負荷: 30秒ごと → オンデマンドのみ
- ログ量: 大幅削減
- サーバーCPU: ポーリング処理削減

### 保守性
- 責務の明確な分離
- それぞれの層で適切なツール使用
- コードの可読性向上

### 拡張性
- 監視ツール(Prometheus等)の導入が容易
- カスタムメトリクスの追加が簡単
- マイクロサービス追加時の対応も明確

## 実装手順

### Phase 1: フロントエンド改善 (即座に実施可能)

1. `App.tsx` から useSystemHealth の自動実行を削除
2. useSystemHealth を手動実行専用にリファクタリング
3. 管理画面にシステムステータスページを追加(オプション)

### Phase 2: 監視基盤整備 (本番環境向け)

1. Prometheus exporter の追加
2. Grafana ダッシュボードの作成
3. アラートルールの設定

### Phase 3: エラーハンドリング強化

1. Axios interceptor の統一実装
2. ユーザー向けエラーメッセージの改善
3. リトライロジックの追加

## 既存のDockerヘルスチェック

すでに実装済みで適切に動作しています:

```dockerfile
# core_api/Dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1
```

**動作確認:**
```bash
# ヘルスチェック状態を確認
docker inspect local_dev-core_api-1 | grep -A 10 Health

# 出力例:
# "Health": {
#     "Status": "healthy",
#     "FailingStreak": 0,
#     "Log": [...]
# }
```

## 参考資料

### ベストプラクティス

- [Google SRE Book - Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [The Twelve-Factor App - Logs](https://12factor.net/logs)
- [Kubernetes Health Checks Best Practices](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

### 推奨監視ツール

| ツール | 用途 | コスト |
|--------|------|--------|
| Prometheus + Grafana | メトリクス収集・可視化 | 無料(セルフホスト) |
| GCP Cloud Monitoring | GCP環境の統合監視 | 従量課金 |
| Datadog | オールインワン監視 | 有料 |
| New Relic | APM・監視 | 有料 |

## 結論

フロントエンドからの定期ヘルスチェックは削除し、以下の構成に変更:

1. **インフラ監視**: Docker HEALTHCHECK (既存)
2. **サービス監視**: Prometheus/Grafana等 (Phase 2で追加)
3. **ユーザー体験**: Axios interceptor (Phase 3で強化)

これにより、プロフェッショナルで保守性の高いシステム監視体制を構築できます。
