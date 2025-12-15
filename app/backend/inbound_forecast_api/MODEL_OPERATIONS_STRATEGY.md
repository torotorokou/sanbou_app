# 予測モデル運用戦略

## 📊 4つの予測モデル

現在のシステムには以下の予測モデルが存在：

1. **日次モデル (Daily Model)**
   - 用途: 翌日（t+1）の需要予測
   - バンドル: `model_bundle.joblib`
   - 出力: 日次予測値

2. **週次モデル (Weekly Allocation)**
   - 用途: 週単位の需要予測
   - 方式: 月次予測を週別に按分
   - 依存: 月次Gammaモデルの出力

3. **月次モデル (Monthly Gamma + Blend)**
   - 用途: 月次需要予測
   - 構成: Gamma Recency + LGBM ブレンド
   - 出力: 月次予測値

4. **月次着地モデル (Monthly Landing)**
   - 用途: 月末着地予測（月の途中時点から月合計を予測）
   - 方式: Gamma-Poisson + 日次累積
   - タイミング: 14日時点、21日時点

---

## 🎯 運用戦略提案

### アプローチ1: 段階的モデル管理システム（推奨）

#### Phase 1: モデルレジストリの構築
```
app/infra/models/
  registry/
    model_registry.py          # モデルバージョン管理
    model_metadata.py          # メタデータ定義
  storage/
    model_storage.py           # バンドルファイル管理
    version_storage.py         # バージョン履歴管理
  validators/
    model_validator.py         # モデル検証
    performance_validator.py   # 精度検証
```

**特徴**:
- ✅ モデルごとにバージョン管理
- ✅ ロールバック可能
- ✅ A/Bテスト対応
- ✅ 段階的ロールアウト

**実装例**:
```python
class ModelRegistry:
    def register_model(
        self,
        model_type: ModelType,  # DAILY, WEEKLY, MONTHLY, LANDING
        version: str,
        bundle_path: Path,
        metadata: ModelMetadata,
    ) -> str:
        # バンドルを検証
        self.validator.validate(bundle_path, model_type)
        
        # モデルを登録
        model_id = self._store_model(model_type, version, bundle_path)
        
        # メタデータを保存
        self._save_metadata(model_id, metadata)
        
        return model_id
    
    def get_active_model(self, model_type: ModelType) -> ModelBundle:
        # アクティブなモデルを取得
        pass
    
    def rollback_model(self, model_type: ModelType, version: str):
        # 指定バージョンにロールバック
        pass
```

#### Phase 2: モデル更新API
```python
# app/api/routers/model_management.py
@router.post("/api/v1/models/{model_type}/upload")
async def upload_model(
    model_type: ModelType,
    file: UploadFile,
    metadata: ModelMetadata = Depends(),
):
    """
    CSVまたはモデルバンドルをアップロード
    
    - CSVアップロード → 自動再学習 → モデル登録
    - バンドルアップロード → 検証 → モデル登録
    """
    pass

@router.post("/api/v1/models/{model_type}/activate")
async def activate_model(
    model_type: ModelType,
    version: str,
):
    """指定バージョンのモデルをアクティブ化"""
    pass

@router.get("/api/v1/models/{model_type}/versions")
async def list_model_versions(model_type: ModelType):
    """モデルバージョン一覧を取得"""
    pass
```

#### Phase 3: フロントエンド統合
```typescript
// モデル管理画面
interface ModelManagementView {
  // モデル一覧表示
  models: {
    daily: ModelInfo[];
    weekly: ModelInfo[];
    monthly: ModelInfo[];
    landing: ModelInfo[];
  };
  
  // アクション
  uploadCSV(modelType: ModelType, file: File): Promise<void>;
  uploadBundle(modelType: ModelType, file: File): Promise<void>;
  activateVersion(modelType: ModelType, version: string): Promise<void>;
  rollback(modelType: ModelType, version: string): Promise<void>;
}
```

---

### アプローチ2: ジョブベース運用（シンプル）

#### 構成
```
app/
  jobs/
    model_update_job.py        # モデル更新ジョブ
    scheduled_retraining.py    # 定期再学習
  api/
    routers/
      jobs.py                  # ジョブ管理API
```

**特徴**:
- ✅ シンプル、実装が容易
- ✅ スケジューラーと連携しやすい
- ❌ バージョン管理が弱い
- ❌ ロールバック機能なし

**実装例**:
```python
@router.post("/api/v1/jobs/retrain/{model_type}")
async def trigger_retraining(
    model_type: ModelType,
    background_tasks: BackgroundTasks,
):
    """
    モデル再学習をバックグラウンドで実行
    """
    background_tasks.add_task(retrain_model, model_type)
    return {"status": "scheduled", "job_id": job_id}

@router.post("/api/v1/jobs/csv-import/{model_type}")
async def import_training_data(
    model_type: ModelType,
    file: UploadFile,
):
    """
    CSVをインポートして再学習を実行
    """
    pass
```

---

### アプローチ3: ハイブリッド運用（現実的）

**Phase 1-2 (短期: 3ヶ月)**
- ジョブベースで基本機能実装
- CSVアップロード → 再学習 → 自動反映
- 管理画面で手動トリガー可能

**Phase 3-4 (中期: 6ヶ月)**
- モデルレジストリ導入
- バージョン管理機能追加
- A/Bテスト基盤構築

**Phase 5+ (長期: 1年)**
- MLOps基盤統合
- 自動精度モニタリング
- 自動ロールバック

---

## 🔧 具体的な実装計画

### Step 1: モデルメタデータ定義（2週間）

```python
# app/infra/models/model_metadata.py
from enum import Enum
from datetime import datetime
from pydantic import BaseModel

class ModelType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    LANDING = "landing"

class ModelMetadata(BaseModel):
    model_id: str
    model_type: ModelType
    version: str
    created_at: datetime
    trained_on_data_until: datetime  # どの日付までのデータで学習したか
    accuracy_metrics: dict  # MAE, MAPE, R2など
    training_params: dict
    bundle_path: str
    status: str  # "draft", "active", "archived"
    description: Optional[str]
```

### Step 2: モデルストレージ（2週間）

```python
# app/infra/models/storage/model_storage.py
class ModelStorage:
    """
    モデルバンドルファイルの管理
    
    - ローカルファイルシステム
    - 将来的にGCS/S3対応
    """
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
    
    def save_model(
        self,
        model_type: ModelType,
        version: str,
        bundle_file: Path,
    ) -> str:
        """
        モデルバンドルを保存
        
        保存先: {base_path}/{model_type}/{version}/model_bundle.joblib
        """
        dest_dir = self.base_path / model_type.value / version
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = dest_dir / "model_bundle.joblib"
        shutil.copy(bundle_file, dest_path)
        
        return str(dest_path)
    
    def load_model(self, model_type: ModelType, version: str):
        """モデルバンドルを読み込み"""
        bundle_path = self.base_path / model_type.value / version / "model_bundle.joblib"
        return joblib.load(bundle_path)
    
    def list_versions(self, model_type: ModelType) -> List[str]:
        """バージョン一覧を取得"""
        model_dir = self.base_path / model_type.value
        if not model_dir.exists():
            return []
        return [d.name for d in model_dir.iterdir() if d.is_dir()]
```

### Step 3: モデル更新API（3週間）

```python
# app/api/routers/model_management.py
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from app.infra.models.registry import ModelRegistry
from app.infra.services.training import TrainingService

router = APIRouter(prefix="/api/v1/models", tags=["models"])

@router.post("/{model_type}/csv-upload")
async def upload_training_data(
    model_type: ModelType,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    auto_train: bool = True,
):
    """
    学習データCSVをアップロードして再学習
    
    1. CSVを保存
    2. データ検証
    3. バックグラウンドで再学習実行
    4. 完了後、モデルを自動登録
    """
    # CSVを保存
    csv_path = await save_uploaded_file(file)
    
    # データ検証
    validator = DataValidator()
    validation_result = validator.validate(csv_path, model_type)
    
    if not validation_result.is_valid:
        raise HTTPException(400, detail=validation_result.errors)
    
    # バックグラウンドで再学習
    if auto_train:
        job_id = generate_job_id()
        background_tasks.add_task(
            retrain_model_task,
            model_type=model_type,
            csv_path=csv_path,
            job_id=job_id,
        )
        return {
            "status": "scheduled",
            "job_id": job_id,
            "message": "Model training scheduled"
        }
    
    return {"status": "uploaded", "csv_path": str(csv_path)}

@router.post("/{model_type}/bundle-upload")
async def upload_model_bundle(
    model_type: ModelType,
    file: UploadFile = File(...),
    version: str = Body(...),
    description: Optional[str] = Body(None),
):
    """
    学習済みモデルバンドルをアップロード
    
    1. バンドルファイルを保存
    2. モデルを検証
    3. メタデータを登録
    4. アクティブ化（オプション）
    """
    # バンドルを一時保存
    temp_path = await save_uploaded_file(file)
    
    # モデル検証
    validator = ModelValidator()
    validation_result = validator.validate(temp_path, model_type)
    
    if not validation_result.is_valid:
        raise HTTPException(400, detail=validation_result.errors)
    
    # モデルレジストリに登録
    registry = ModelRegistry()
    model_id = registry.register_model(
        model_type=model_type,
        version=version,
        bundle_path=temp_path,
        metadata=ModelMetadata(
            model_type=model_type,
            version=version,
            description=description,
            accuracy_metrics=validation_result.metrics,
        ),
    )
    
    return {"status": "registered", "model_id": model_id}

@router.post("/{model_type}/{version}/activate")
async def activate_model_version(
    model_type: ModelType,
    version: str,
):
    """
    指定バージョンのモデルをアクティブ化
    """
    registry = ModelRegistry()
    registry.activate_model(model_type, version)
    
    return {"status": "activated", "model_type": model_type, "version": version}

@router.get("/{model_type}/versions")
async def list_model_versions(model_type: ModelType):
    """
    モデルバージョン一覧を取得
    """
    registry = ModelRegistry()
    versions = registry.list_versions(model_type)
    
    return {"model_type": model_type, "versions": versions}

@router.get("/{model_type}/active")
async def get_active_model(model_type: ModelType):
    """
    現在アクティブなモデル情報を取得
    """
    registry = ModelRegistry()
    active_model = registry.get_active_model(model_type)
    
    return active_model.to_dict()
```

### Step 4: 管理画面（3週間）

```typescript
// frontend/src/features/modelManagement/

// モデル管理ページ
export const ModelManagementPage = () => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  
  return (
    <div>
      <h1>予測モデル管理</h1>
      
      <Tabs>
        <Tab label="日次モデル">
          <ModelPanel modelType="daily" />
        </Tab>
        <Tab label="週次モデル">
          <ModelPanel modelType="weekly" />
        </Tab>
        <Tab label="月次モデル">
          <ModelPanel modelType="monthly" />
        </Tab>
        <Tab label="月次着地モデル">
          <ModelPanel modelType="landing" />
        </Tab>
      </Tabs>
    </div>
  );
};

// モデルパネルコンポーネント
const ModelPanel = ({ modelType }: { modelType: ModelType }) => {
  const [versions, setVersions] = useState<ModelVersion[]>([]);
  const [activeVersion, setActiveVersion] = useState<string | null>(null);
  
  return (
    <div>
      {/* CSVアップロード */}
      <Card>
        <h3>学習データアップロード</h3>
        <FileUpload
          accept=".csv"
          onUpload={(file) => handleCSVUpload(modelType, file)}
        />
        <p>CSVをアップロードすると自動的に再学習が開始されます</p>
      </Card>
      
      {/* モデルバンドルアップロード */}
      <Card>
        <h3>学習済みモデルアップロード</h3>
        <FileUpload
          accept=".joblib"
          onUpload={(file) => handleBundleUpload(modelType, file)}
        />
      </Card>
      
      {/* バージョン一覧 */}
      <Card>
        <h3>モデルバージョン</h3>
        <Table>
          <thead>
            <tr>
              <th>バージョン</th>
              <th>作成日時</th>
              <th>精度（MAE）</th>
              <th>ステータス</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {versions.map((v) => (
              <tr key={v.version}>
                <td>{v.version}</td>
                <td>{formatDate(v.created_at)}</td>
                <td>{v.accuracy_metrics.mae}</td>
                <td>
                  {v.version === activeVersion ? (
                    <Badge color="green">アクティブ</Badge>
                  ) : (
                    <Badge color="gray">待機中</Badge>
                  )}
                </td>
                <td>
                  {v.version !== activeVersion && (
                    <Button onClick={() => handleActivate(modelType, v.version)}>
                      アクティブ化
                    </Button>
                  )}
                  <Button onClick={() => handleDelete(modelType, v.version)}>
                    削除
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
    </div>
  );
};
```

---

## 📊 DB設計

```sql
-- モデルメタデータテーブル
CREATE TABLE forecast.model_metadata (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_type VARCHAR(50) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'landing'
    version VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- 'draft', 'active', 'archived'
    bundle_path TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    activated_at TIMESTAMP,
    archived_at TIMESTAMP,
    trained_on_data_until DATE,
    accuracy_metrics JSONB,  -- {"mae": 56.3, "mape": 2.44, "r2": 0.85}
    training_params JSONB,
    description TEXT,
    created_by VARCHAR(100),
    UNIQUE(model_type, version)
);

-- アクティブモデル管理テーブル
CREATE TABLE forecast.active_models (
    model_type VARCHAR(50) PRIMARY KEY,
    active_model_id UUID NOT NULL REFERENCES forecast.model_metadata(model_id),
    activated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    activated_by VARCHAR(100)
);

-- モデル学習ジョブテーブル
CREATE TABLE forecast.training_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    csv_path TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    result_model_id UUID REFERENCES forecast.model_metadata(model_id)
);

-- インデックス
CREATE INDEX idx_model_metadata_type_status ON forecast.model_metadata(model_type, status);
CREATE INDEX idx_training_jobs_status ON forecast.training_jobs(status);
```

---

## 🚀 ロードマップ

### Sprint 1-2 (2週間): 基盤構築
- [ ] ModelType, ModelMetadata定義
- [ ] ModelStorage実装
- [ ] DB設計・マイグレーション

### Sprint 3-4 (2週間): コア機能
- [ ] ModelRegistry実装
- [ ] ModelValidator実装
- [ ] 基本的なAPI実装

### Sprint 5-6 (2週間): API統合
- [ ] CSVアップロードAPI
- [ ] モデルバンドルアップロードAPI
- [ ] バージョン管理API

### Sprint 7-9 (3週間): フロントエンド
- [ ] モデル管理画面
- [ ] アップロードUI
- [ ] バージョン一覧・切り替えUI

### Sprint 10 (1週間): テスト・調整
- [ ] 統合テスト
- [ ] パフォーマンステスト
- [ ] ドキュメント整備

---

## 💡 ベストプラクティス

### 1. バージョン命名規則
```
{YYYYMMDD}_{model_type}_{iteration}
例: 20251215_daily_v1, 20251215_monthly_v2
```

### 2. モデル検証チェックリスト
- ✅ バンドルファイルの整合性
- ✅ 必須キーの存在確認
- ✅ テストデータでの精度検証
- ✅ 予測値の範囲チェック

### 3. ロールバック戦略
- 常に直前2バージョンを保持
- 自動精度モニタリング
- 閾値を下回ったら自動アラート

### 4. セキュリティ
- ファイルアップロードのサイズ制限
- ファイル形式の検証
- アクセス権限の管理

---

**作成日**: 2025-12-15
**ブランチ**: `refactor/inbound-forecast-api-structure`
