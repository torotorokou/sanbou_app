# ブロック単価計算 運搬業者選択による単価計算問題 - 調査レポート

**作成日**: 2024年12月2日  
**ブランチ**: `debug/block-unit-price-transport-calculation`  
**優先度**: 🔴 **HIGH** - すべての計算が0円（オネスト）になっている  
**ステータス**: 🔍 **調査中 - 根本原因特定作業**

---

## 📋 問題概要

ブロック単価計算において、フロントエンドから運搬業者を選択して送信しているにもかかわらず、すべての計算が「オネスト（0円）」として処理され、正しい運搬費が適用されていない。

### 症状

- フロントエンドで「エコライン」「澤希」など運搬業者を選択
- バックエンドに選択が送信される
- しかし最終計算では全て運搬費=0円（オネスト）として計算される
- 結果としてブロック単価が不正確になる

---

## 🔍 システムフロー分析

### 1. フロントエンド → バックエンドの流れ

#### フロントエンド: 選択データの構築

```typescript
// features/report/interactive/model/blockUnitPriceHelpers.ts
export const buildSelectionPayload = (
  items: InteractiveItem[],
  selections: Record<string, { index: number; label: string }>,
): Record<string, string> => {
  const payload: Record<string, string> = {};

  items.forEach((item) => {
    const selection = selections[item.id];
    if (!selection) return;

    const transport_vendor =
      item.transport_options[selection.index]?.name ?? selection.label ?? "";
    const entry_id = String(item.rawRow?.entry_id ?? item.id ?? "");

    if (transport_vendor && entry_id) {
      payload[entry_id] = transport_vendor; // entry_id → 運搬業者名
    }
  });

  return payload;
};
```

**送信データ形式**:

```json
{
  "session_id": "bup-20251202xxx",
  "selections": {
    "0": "エコライン",
    "1": "澤希",
    "2": "オネスト"
  }
}
```

#### API: フロントエンドからのリクエスト受信

```python
# api/routers/reports/block_unit_price_interactive.py
@router.post("/finalize", tags=[tag_name])
async def finalize_calculation(request: FinalizeRequest) -> Any:
    user_input = {
        "session_id": request.session_id,
        "selections": request.selections or {},  # 選択を受け取る
    }

    response = service.finalize(generator, request.session_id, user_input)
    return response
```

---

### 2. バックエンド内部処理フロー

#### Step 1: 選択の解決と適用

```python
# usecases/reports/interactive/block_unit_price_main.py
class BlockUnitPriceInteractive:
    def _resolve_and_apply_selections(
        self,
        state: Dict[str, Any],
        selections: Dict[str, Union[int, str]]
    ) -> Dict[str, str]:
        """選択を解決してstateに適用"""

        resolved_entry_map: Dict[str, str] = {}

        for key, value in selections.items():
            entry_id = str(key)

            # value が int の場合、運搬業者リストから選択
            if isinstance(value, int):
                # options から運搬業者名を取得
                label = normalized_options[idx_choice]
            else:
                # 文字列の場合はそのまま使用
                label = str(value)

            resolved_entry_map[entry_id] = label

        # state に保存
        state["selections"] = resolved_entry_map
        return resolved_entry_map
```

#### Step 2: DataFrameへのマージ

```python
# usecases/reports/interactive/block_unit_price_finalize.py
def merge_selected_transport_vendors_with_df(
    df_shipment: pd.DataFrame,
    selection_df: pd.DataFrame
) -> pd.DataFrame:
    """選択された運搬業者をDataFrameにマージ"""

    df_after = df_shipment.copy()
    df_after["entry_id"] = df_after["entry_id"].astype(str)

    sel = selection_df.copy()
    sel["entry_id"] = sel["entry_id"].astype(str)

    # 運搬業者列を探す
    label_col = next((c for c in vendor_label_candidates if c in sel.columns), None)

    # マージ
    merged = df_after.merge(
        sel.rename(columns={label_col: "__selected_vendor"}),
        on="entry_id",
        how="left",
    )

    merged["運搬業者"] = merged["__selected_vendor"].combine_first(merged["運搬業者"])

    return merged
```

#### Step 3: 運搬費の適用

```python
# domain/reports/processors/block_unit_price/process2.py
def apply_transport_fee_by_vendor(
    df_after: DataFrame,
    df_transport: DataFrame
) -> DataFrame:
    """運搬業者ごとの運搬費を適用する関数"""

    # 【重要】業者CDと運搬業者の両方で結合
    updated_target_rows = apply_column_addition_by_keys(
        base_df=target_rows,
        addition_df=df_transport,
        join_keys=["業者CD", "運搬業者"],  # ← ここがキー
        value_col_to_add="運搬費",
        update_target_col="運搬費",
    )

    return updated_target_rows
```

#### 運搬費マスターデータ (`transport_costs.csv`)

```csv
業者CD,業者名,運搬業者,運搬費,合積
6421,アクトリー,オネスト,0
6421,アクトリー,アクトリー,40000
8215,杉田建材,オネスト,0
8215,杉田建材,エコライン,40000
8327,丸源企業,オネスト,0
8327,丸源企業,シェノンビ,40000
8327,丸源企業,エコライン（ウイング）,41800
8327,丸源企業,エコライン（コンテナ）,35000
```

#### 結合ロジック

```python
# infra/report_utils/dataframe/columns.py
def apply_column_addition_by_keys(
    base_df: pd.DataFrame,
    addition_df: pd.DataFrame,
    join_keys: list[str],  # ["業者CD", "運搬業者"]
    value_col_to_add: str = "運搬費",
    update_target_col: str = "運搬費",
) -> pd.DataFrame:

    # 重複を除いた加算対象データの作成
    unique_add_df = addition_df.drop_duplicates(subset=join_keys)[
        join_keys + [value_col_to_add]
    ]

    # base_df を join_keys に存在するものだけにフィルタ
    valid_keys = unique_add_df[join_keys].drop_duplicates()
    filtered_base_df = base_df.merge(valid_keys, on=join_keys, how="inner")

    # マージして加算
    merged_df = safe_merge_by_keys(
        master_df=filtered_base_df,
        data_df=unique_add_df,
        key_cols=join_keys
    )

    return updated_df
```

---

## 🐛 問題箇所の特定

### 仮説1: 運搬業者名の不一致

**問題**: フロントエンドから送られる運搬業者名と`transport_costs.csv`の運搬業者名が完全一致しない可能性

#### 確認ポイント:

1. **前後の空白**: `"エコライン "` vs `"エコライン"`
2. **全角/半角**: `"エコライン"` vs `"ｴｺﾗｲﾝ"`
3. **大文字/小文字**: 通常は関係ないが念のため
4. **括弧付き**: `"エコライン（ウイング）"` vs `"エコライン"`

**検証方法**:

```python
# フロントエンドから送信される運搬業者名
selected_vendor = "エコライン"

# transport_costs.csv に存在する運搬業者名
df_transport["運搬業者"].unique()
# ['オネスト', 'エコライン', 'エコライン（ウイング）', 'エコライン（コンテナ）', ...]
```

### 仮説2: entry_idのマッピングエラー

**問題**: `entry_id`の生成・照合ロジックに不整合がある

#### 初期ステップでの`entry_id`生成:

```python
# usecases/reports/interactive/block_unit_price_initial.py
def stable_entry_id(row: pd.Series) -> str:
    """安定したentry_idを生成"""
    gyousha_cd = str(row.get("業者CD", ""))
    hinmei = str(row.get("品名", ""))
    meisai = str(row.get("明細備考", ""))
    idx = str(row.name) if hasattr(row, "name") else ""

    return f"{gyousha_cd}_{hinmei}_{meisai}_{idx}"
```

#### フロントエンドでの`entry_id`使用:

```typescript
const entry_id = String(item.rawRow?.entry_id ?? item.id ?? "");
payload[entry_id] = transport_vendor;
```

**検証ポイント**:

- `entry_id`が初期ステップとfinalize時で一致しているか
- DataFrameのindexが変更されていないか
- マージ時に`entry_id`の型が一致しているか（string vs int）

### 仮説3: DataFrameマージ時の列消失

**問題**: マージ処理で「運搬業者」列が正しく更新されていない

#### 疑わしい箇所:

```python
def merge_selected_transport_vendors_with_df(
    df_shipment: pd.DataFrame,
    selection_df: pd.DataFrame
) -> pd.DataFrame:

    # label_col が見つからない場合
    label_col = next((c for c in vendor_label_candidates if c in sel.columns), None)
    if not label_col:
        raise ValueError("selection_df にベンダ名の列が見つかりません")

    # マージ
    merged = df_after.merge(
        sel.rename(columns={label_col: "__selected_vendor"}),
        on="entry_id",
        how="left",  # ← left join のため、一致しないとNaNになる
    )

    # combine_first は NaN の場合のみ元の値を使う
    merged["運搬業者"] = merged["__selected_vendor"].combine_first(merged["運搬業者"])
```

**検証ポイント**:

- `selection_df`に期待する列が存在するか
- `how="left"`で一致しない行が多数ある可能性
- `__selected_vendor`がすべてNaNになっている可能性

### 仮説4: 運搬費適用時のキー不一致

**問題**: `apply_column_addition_by_keys`で`["業者CD", "運搬業者"]`の両方が一致しないと運搬費が適用されない

#### 結合条件:

```python
join_keys=["業者CD", "運搬業者"]
```

**検証ポイント**:

1. `df_shipment`の「業者CD」が正しく設定されているか
2. `df_shipment`の「運搬業者」が選択されたベンダ名になっているか
3. `transport_costs.csv`に該当する組み合わせが存在するか

**デバッグ方法**:

```python
# df_shipment の状態確認
print(df_shipment[["業者CD", "運搬業者", "entry_id"]].head())

# transport_costs.csv との照合
print(df_transport[["業者CD", "運搬業者", "運搬費"]].head())

# マージ結果確認
merged = df_shipment.merge(
    df_transport[["業者CD", "運搬業者", "運搬費"]],
    on=["業者CD", "運搬業者"],
    how="left",
    indicator=True
)
print(merged["_merge"].value_counts())
```

---

## 🔄 旧Streamlitアプリとの比較

### Streamlitでの処理フロー

```python
# domain/reports/processors/block_unit_price/process1.py
def create_transport_selection_form(
    df_after: pd.DataFrame,
    df_transport: pd.DataFrame
) -> pd.DataFrame:
    """Streamlit UI で運搬業者を選択"""

    # セッション状態に選択を保存
    st.session_state.block_unit_price_transport_map = {}

    for idx, row in target_rows.iterrows():
        gyousha_cd = row["業者CD"]

        # 運搬業者の選択肢を取得
        options = df_transport[df_transport["業者CD"] == gyousha_cd]["運搬業者"].tolist()

        # セレクトボックス
        selected = st.selectbox(
            label="🚚 運搬業者を選択してください",
            options=options,
            key=f"select_block_unit_price_row_{idx}",
        )

        # 選択を保存（indexをキーとする）
        selected_map[idx] = selected

    # 選択結果をDataFrameに反映
    selected_df = pd.DataFrame.from_dict(
        st.session_state.block_unit_price_transport_map,
        orient="index",
        columns=["運搬業者"],
    )
    selected_df.index.name = df_after.index.name

    # マージ（indexベース）
    df_after = df_after.merge(
        selected_df,
        left_index=True,
        right_index=True,
        how="left",
        suffixes=("_old", "")
    )

    return df_after
```

### 新Reactアプリでの処理フロー

```python
# usecases/reports/interactive/block_unit_price_finalize.py
def merge_selected_transport_vendors_with_df(
    df_shipment: pd.DataFrame,
    selection_df: pd.DataFrame
) -> pd.DataFrame:
    """entry_id ベースでマージ"""

    df_after["entry_id"] = df_after["entry_id"].astype(str)
    sel["entry_id"] = sel["entry_id"].astype(str)

    # entry_id でマージ
    merged = df_after.merge(
        sel.rename(columns={label_col: "__selected_vendor"}),
        on="entry_id",
        how="left",
    )

    merged["運搬業者"] = merged["__selected_vendor"].combine_first(merged["運搬業者"])

    return merged
```

### 主な違い

| 項目             | Streamlit (旧)                      | React (新)                         |
| ---------------- | ----------------------------------- | ---------------------------------- |
| **マージキー**   | DataFrameの`index`                  | `entry_id`列                       |
| **選択の保存**   | セッション状態(dict)                | state["selections"] + selection_df |
| **マージ方法**   | `left_index=True, right_index=True` | `on="entry_id"`                    |
| **データの流れ** | 同一プロセス内で完結                | API経由で複数ステップ              |

---

## 🎯 推定される根本原因

### 最も可能性が高い原因

**`entry_id`ベースのマージが失敗している**

#### 理由:

1. **entry_idの不一致**
   - 初期ステップで生成した`entry_id`とfinalize時の`entry_id`が一致しない
   - DataFrameの処理過程で`entry_id`が変更・消失している
2. **selection_dfの構造問題**

   - フロントエンドから送られる`selections`が正しく`selection_df`に変換されていない
   - `selection_df`に期待する列名が存在しない

3. **マージの失敗**
   - `how="left"`でマージした結果、`__selected_vendor`列がすべてNaNになる
   - `combine_first`が実質的に元の「運搬業者」列を保持するだけになる
   - 元の「運搬業者」列がデフォルトで「オネスト」になっている

#### 証拠:

```python
logger.debug(
    "DBG merge selection_df: "
    f"sel_cols={list(selection_df.columns)} | before_cols={list(df_shipment.columns)} | "
    f"after_cols={list(merged.columns)} | applied_count={int(merged['運搬業者'].notna().sum())}"
)
```

このログで`applied_count`が0または期待より少ない場合、マージが失敗している。

---

## 🔬 検証すべきポイント

### 1. entry_idの一貫性確認

```python
# 初期ステップでの生成
initial_entry_ids = df_shipment["entry_id"].tolist()

# finalize時の確認
finalize_entry_ids = df_shipment["entry_id"].tolist()

# 一致確認
assert initial_entry_ids == finalize_entry_ids
```

### 2. selection_dfの内容確認

```python
# フロントエンドから受信したselections
print("Received selections:", selections)

# selection_dfへの変換
selection_df = pd.DataFrame([
    {"entry_id": k, "selected_vendor": v}
    for k, v in selections.items()
])
print("selection_df:")
print(selection_df)

# 列名の確認
print("Columns:", selection_df.columns.tolist())
```

### 3. マージ結果の検証

```python
# マージ前
print("Before merge:")
print(df_shipment[["entry_id", "業者CD", "業者名", "運搬業者"]].head())

# マージ後
merged = merge_selected_transport_vendors_with_df(df_shipment, selection_df)
print("After merge:")
print(merged[["entry_id", "業者CD", "業者名", "運搬業者"]].head())

# 運搬業者の値分布
print("運搬業者 value counts:")
print(merged["運搬業者"].value_counts())
```

### 4. 運搬費適用の検証

```python
# 運搬費適用前
print("Before transport fee:")
print(df_after[["業者CD", "運搬業者", "運搬費"]].head())

# 運搬費適用後
df_with_fee = apply_transport_fee_by_vendor(df_after, df_transport)
print("After transport fee:")
print(df_with_fee[["業者CD", "運搬業者", "運搬費"]].head())

# 運搬費の統計
print("運搬費 statistics:")
print(df_with_fee["運搬費"].describe())
```

---

## 📝 次のアクション

### 優先度1: ログ追加とデバッグ

```python
# block_unit_price_finalize.py に詳細ログを追加
def merge_selected_transport_vendors_with_df(...):
    logger.debug(f"=== MERGE DEBUG START ===")
    logger.debug(f"df_shipment.shape: {df_shipment.shape}")
    logger.debug(f"df_shipment.entry_id sample: {df_shipment['entry_id'].head().tolist()}")
    logger.debug(f"selection_df.shape: {selection_df.shape}")
    logger.debug(f"selection_df content:\n{selection_df}")

    # マージ実行
    merged = df_after.merge(...)

    logger.debug(f"merged.shape: {merged.shape}")
    logger.debug(f"__selected_vendor null count: {merged['__selected_vendor'].isna().sum()}")
    logger.debug(f"運搬業者 before combine: {merged['運搬業者'].value_counts().to_dict()}")

    # combine_first実行
    merged["運搬業者"] = merged["__selected_vendor"].combine_first(merged["運搬業者"])

    logger.debug(f"運搬業者 after combine: {merged['運搬業者'].value_counts().to_dict()}")
    logger.debug(f"=== MERGE DEBUG END ===")

    return merged
```

### 優先度2: entry_id生成の見直し

`entry_id`の生成ロジックが複雑すぎる可能性。より単純で安定した方法に変更:

```python
def stable_entry_id(row: pd.Series, df_index: int) -> str:
    """シンプルなentry_id生成"""
    gyousha_cd = str(row.get("業者CD", ""))
    # indexを含めることで一意性を保証
    return f"{gyousha_cd}_{df_index}"
```

### 優先度3: フロントエンドとの連携確認

フロントエンドから送信されるペイロードを実際に確認:

```python
@router.post("/finalize")
async def finalize_calculation(request: FinalizeRequest):
    logger.info(f"=== FINALIZE REQUEST ===")
    logger.info(f"session_id: {request.session_id}")
    logger.info(f"selections type: {type(request.selections)}")
    logger.info(f"selections content: {request.selections}")
    logger.info(f"selections keys: {list(request.selections.keys()) if request.selections else []}")
    logger.info(f"=== END REQUEST ===")

    # ... 処理続行
```

---

## 📌 まとめ

**推定される根本原因**: `entry_id`ベースのマージが失敗し、選択された運搬業者がDataFrameに反映されていない。そのため、デフォルト値の「オネスト（0円）」がそのまま使用されている。

**検証が必要な項目**:

1. `entry_id`の生成と保持の一貫性
2. `selection_df`への正しい変換
3. マージ処理の成功確認
4. 運搬費マスターとの結合条件

**次のステップ**:

1. 詳細ログを追加してデバッグ情報を収集
2. 実際のデータフローを追跡
3. entry_id生成ロジックの見直し
4. 旧Streamlitアプリとの動作比較

---

**報告者**: GitHub Copilot  
**確認者**: （レビュー担当者名を記入）
