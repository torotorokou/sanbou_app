# リファクタリング実例: rag_api の日付処理統一

作成日: 2024-12-04  
ブランチ: feature/env-and-shared-refactoring

## 概要

`rag_api` の日付処理を backend_shared の統一ユーティリティを使用するようリファクタリングした実例です。

## 変更対象ファイル

1. `app/backend/rag_api/app/core/usecases/rag/dummy_response_service.py`
2. `app/backend/rag_api/app/core/usecases/rag/ai_response_service.py`

## Before: 個別実装（問題点）

### dummy_response_service.py (BEFORE)

```python
from zoneinfo import ZoneInfo

class DummyResponseService:
    def generate_response(
        self,
        question: str,
        context_docs: list[str],
        question_type: str
    ) -> str:
        # 毎回 ZoneInfo を生成（パフォーマンスロス）
        jst = ZoneInfo('Asia/Tokyo')  # ❌ タイムゾーン名がハードコード
        now = datetime.now(jst)
        
        # フォーマット文字列もハードコード
        timestamp = now.strftime('%Y年%m月%d日 %H:%M')  # ❌ 個別実装
```

**問題点:**
- `ZoneInfo('Asia/Tokyo')` を毎回生成（キャッシュされない）
- タイムゾーン名がハードコード（環境変数で変更不可）
- フォーマット文字列が散在（統一されていない）

### ai_response_service.py (BEFORE)

```python
from zoneinfo import ZoneInfo

class AiResponseService:
    async def generate_response(
        self,
        question: str,
        context_docs: list[str],
        question_type: str
    ) -> str:
        # 別の実装パターン（微妙に異なる）
        jst = ZoneInfo("Asia/Tokyo")  # ❌ 引用符の種類が違う
        now = datetime.now()
        timestamp = now.astimezone(jst).strftime("%Y年%m月%d日 %H:%M")  # ❌ 別パターン
```

**問題点:**
- `dummy_response_service.py` と微妙に実装が異なる
- コードの重複（DRY原則違反）
- メンテナンス時に修正漏れのリスク

---

## After: backend_shared 統一ユーティリティ使用

### dummy_response_service.py (AFTER)

```python
from backend_shared.utils.datetime_utils import now_in_app_timezone, format_datetime_jp

class DummyResponseService:
    def generate_response(
        self,
        question: str,
        context_docs: list[str],
        question_type: str
    ) -> str:
        # シンプル＆効率的
        timestamp = format_datetime_jp(now_in_app_timezone())  # ✅ 1行で完結
```

### ai_response_service.py (AFTER)

```python
from backend_shared.utils.datetime_utils import now_in_app_timezone, format_datetime_jp

class AiResponseService:
    async def generate_response(
        self,
        question: str,
        context_docs: list[str],
        question_type: str
    ) -> str:
        # 同じパターン（統一された）
        timestamp = format_datetime_jp(now_in_app_timezone())  # ✅ 統一された実装
```

---

## 変更内容の詳細

### dummy_response_service.py

```diff
-from zoneinfo import ZoneInfo
+from backend_shared.utils.datetime_utils import now_in_app_timezone, format_datetime_jp

 class DummyResponseService:
     def generate_response(
         self,
         question: str,
         context_docs: list[str],
         question_type: str
     ) -> str:
-        jst = ZoneInfo('Asia/Tokyo')
-        now = datetime.now(jst)
-        timestamp = now.strftime('%Y年%m月%d日 %H:%M')
+        timestamp = format_datetime_jp(now_in_app_timezone())
```

### ai_response_service.py

```diff
-from zoneinfo import ZoneInfo
+from backend_shared.utils.datetime_utils import now_in_app_timezone, format_datetime_jp

 class AiResponseService:
     async def generate_response(
         self,
         question: str,
         context_docs: list[str],
         question_type: str
     ) -> str:
-        jst = ZoneInfo("Asia/Tokyo")
-        now = datetime.now()
-        timestamp = now.astimezone(jst).strftime("%Y年%m月%d日 %H:%M")
+        timestamp = format_datetime_jp(now_in_app_timezone())
```

---

## 効果

### コード削減

- **削減行数**: 6行（2ファイル × 3行）
- **可読性向上**: 意図が明確な関数名で実装

### パフォーマンス向上

- `ZoneInfo` オブジェクトがキャッシュされる（`@lru_cache` による）
- 毎回の生成コストを削減

### 保守性向上

- タイムゾーン変更時は `.env` を編集するだけ
- フォーマット変更時は `backend_shared` を修正するだけ
- 全サービスに自動的に反映

### テスト容易性向上

```python
# テスト時にタイムゾーンを変更可能
import os
from backend_shared.utils.datetime_utils import get_app_timezone

def test_datetime_format():
    os.environ["APP_TIMEZONE"] = "UTC"
    get_app_timezone.cache_clear()  # キャッシュクリア
    
    # UTC での動作をテスト
    assert get_app_timezone().key == "UTC"
```

---

## 実装手順

### ステップ1: backend_shared に datetime_utils を追加

```bash
# 既に実装済み
ls -la app/backend/backend_shared/src/backend_shared/utils/datetime_utils.py
```

### ステップ2: rag_api の依存関係を確認

```bash
cd app/backend/rag_api
grep -r "from zoneinfo import ZoneInfo" .
```

### ステップ3: rag_api をリファクタリング

```bash
# dummy_response_service.py を修正
# ai_response_service.py を修正
```

### ステップ4: テスト実行

```bash
# rag_api のテスト実行（存在する場合）
pytest app/backend/rag_api/tests/

# 手動テスト: rag_api を起動して動作確認
docker compose -f docker/docker-compose.dev.yml up rag_api
```

### ステップ5: 動作確認

```bash
# API エンドポイントを呼び出して、タイムスタンプが正しく表示されることを確認
curl -X POST http://localhost:8005/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "テスト質問", "question_type": "general"}'
```

---

## 注意事項

### 後方互換性

- 既存の動作は変更されない（JST タイムゾーンのまま）
- デフォルト値は `Asia/Tokyo`（変更不要）

### 環境変数での上書き

```bash
# 必要に応じてタイムゾーンを変更可能
export APP_TIMEZONE=UTC
```

### 他サービスへの展開

同様のパターンで他のサービスもリファクタリング可能:

- `ledger_api`: 日付処理がある場合
- `core_api`: SQL内のタイムゾーン処理を除く
- 新規サービス: 最初から `datetime_utils` を使用

---

## 次のステップ

### 短期（今回のPR）

- ✅ backend_shared に `datetime_utils` を追加
- ✅ rag_api でリファクタリング
- ⬜ テスト実行と動作確認
- ⬜ PR作成とレビュー

### 中期（次回以降）

- ledger_api で同様のリファクタリング
- core_api でエラーハンドリング統一
- manual_api でエラーハンドリング統一

### 長期（将来的）

- 全サービスで backend_shared 活用を標準化
- 新規サービス作成時のテンプレート整備
- ドキュメント・ベストプラクティス集の作成
