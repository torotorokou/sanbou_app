
---

## 各ディレクトリの詳細

### .devcontainer/
- VSCodeのRemote-Containers拡張用設定。
- 開発環境をDockerで統一し、誰でも同じ環境をすぐ構築できるようにします。

### backend/
- Python（FastAPIなど）のバックエンドAPIコード。
- API実装やバッチ処理などサーバー側のロジックが格納されます。

### config/
- 各種設定ファイル置き場。
- 例：`.env`ファイル、YAML/JSON形式の設定、APIキーなど。

### dbdata/
- データベース用のデータ永続化ボリュームやバックアップ用ディレクトリ。
- Docker Compose等でマウントしてDBデータが消えないようにします。

### frontend/
- React（TypeScript）のフロントエンドアプリ本体。
- 画面表示、ユーザー操作、API通信などクライアント側の処理。

### nginx/
- Nginxサーバーの設定ファイル（例：`nginx.conf`など）。
- 本番環境やリバースプロキシ用の設定を管理します。

---

## 注意・補足

- 本プロジェクトは Docker + VSCode DevContainer + Node.js + Python + SQL を前提としています。
- ローカル開発の際は `.devcontainer` 配下の設定を使うことで環境差分を無くせます。
- 環境変数や重要な設定値は `config/` 配下で一元管理してください。
- DBデータやバックアップは `dbdata/` 配下に保存されます（Git管理から除外推奨）。
- 各ディレクトリ内の詳細なREADMEやドキュメントも今後追加してください。

---

## 開発・運用フロー例

1. **VSCode でプロジェクトを開く（DevContainer推奨）**
2. **Docker Composeで各サービスを起動**
3. **`frontend/`でReact開発、`backend/`でAPI開発**
4. **必要に応じて`config/`や`dbdata/`を更新・バックアップ**
5. **本番時はNginx経由でサービスを公開**

---

質問や不明点はチーム内の技術担当までご連絡ください。
