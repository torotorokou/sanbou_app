# Wisenet NVR 動画取得 調査手順書

**作成日**: 2025-12-18  
**対象機器**: Wisenet NVR (realm="Wisenet NVR")  
**IP**: 192.168.0.233  
**目的**: CMDベースで動画（リアルタイムストリーム or 録画ファイル）取得の可否を判定

---

## 【前提確認】既知情報のサマリー

| 項目 | 状態 | 備考 |
|------|------|------|
| IP | 192.168.0.233 | 固定 |
| ポート 8080 | **OPEN** | スナップショット取得成功 |
| ポート 80/443/554/8554 | **CLOSED** | 過去スキャン時点 |
| 認証方式 | Digest認証 | realm="Wisenet NVR" |
| スナップショット | ✅ 成功 | `GET /stw-cgi/video.cgi?msubmenu=snapshot&action=view&Channel=0` |
| 動画取得 | ❓ 未確認 | **本調査の目的** |

---

## 1) 最短ルート（10分で判定）

### Step 1: ポート8080で動画エンドポイントを探す（3分）

**理由**: スナップショットが取れているので、同じcgi配下に動画APIがある可能性が高い

```bash
# Ubuntu/Windows(Git Bash/WSL)共通
USER="<YOUR_USER>"
PASS="<YOUR_PASS>"
IP="192.168.0.233"
PORT="8080"

# パターン1: MJPEG ストリーム（よくあるパス）
curl --digest -u $USER:$PASS -m 5 "http://${IP}:${PORT}/stw-cgi/video.cgi?msubmenu=mjpeg&action=view&Channel=0" \
  -D - -o test_mjpeg.mjpeg

# パターン2: streaming パラメータ
curl --digest -u $USER:$PASS -m 5 "http://${IP}:${PORT}/stw-cgi/video.cgi?msubmenu=streaming&action=view&Channel=0" \
  -D - -o test_stream.dat

# パターン3: video (直接)
curl --digest -u $USER:$PASS -m 5 "http://${IP}:${PORT}/stw-cgi/video.cgi?msubmenu=video&action=view&Channel=0" \
  -D - -o test_video.dat
```

**期待結果（成功判定）**:
- `Content-Type: multipart/x-mixed-replace` → MJPEG ストリーム **[成功]**
- `Content-Type: video/mp4` or `video/x-msvideo` → ファイルダウンロード **[成功]**
- `Content-Type: application/vnd.apple.mpegurl` → HLS **[成功]**
- `Content-Type: application/json` + エラーメッセージ → APIは存在するが認証/パラメータ不足
- `404 Not Found` → このパスは使えない

**次のアクション**:
- ✅ 成功 → **Step 4へジャンプ（動画保存確認）**
- ❌ 失敗 → Step 2へ

---

### Step 2: Web UIからヒントを得る（3分）

**理由**: ブラウザでアクセスできる場合、HTML/JSから動画URLが判明することが多い

```bash
# Web UIトップページを取得
curl --digest -u $USER:$PASS "http://${IP}:${PORT}/" -o index.html

# よくあるパス
curl --digest -u $USER:$PASS "http://${IP}:${PORT}/index.php" -o index.html
curl --digest -u $USER:$PASS "http://${IP}:${PORT}/index.html" -o index.html

# HTMLから動画関連URLを抽出（手動確認）
grep -Ei "(video|stream|rtsp|mjpeg|\.m3u8|\.mp4)" index.html
```

**手動作業（Windows推奨）**:
1. ブラウザで `http://192.168.0.233:8080` を開く（認証プロンプトで入力）
2. ライブビューページに遷移
3. **F12（開発者ツール）→ Network タブ → フィルタを "Fetch/XHR" or "Media"**
4. リロードまたは再生開始
5. 動画ストリームのリクエストを **右クリック → Copy → Copy as cURL**
6. 取得したcURLコマンドを端末で実行

**期待結果**:
- 動画URLが判明 → **Step 4へ**
- JS埋め込みで複雑 / ActiveXプラグイン必須 → 次へ

---

### Step 3: RTSPポート再スキャン（2分）

**理由**: 554が閉じていても別ポートでRTSPが動いている可能性

```bash
# Ubuntu
sudo nmap -sV -p 554,8554,10554,37777,8000-8010 192.168.0.233

# Windows (nmapインストール済み)
nmap -sV -p 554,8554,10554,37777,8000-8010 192.168.0.233

# nmapがない場合の簡易確認（nc）
for port in 554 8554 10554 37777; do
  timeout 2 bash -c "echo -n '' > /dev/tcp/${IP}/${port}" 2>/dev/null && \
  echo "Port $port is OPEN" || echo "Port $port is CLOSED"
done
```

**期待結果**:
- **OPEN** かつ **rtsp-server** → **Step 4（RTSP接続テスト）へ**
- すべて CLOSED → Step 5へ（詳細ルートへ移行）

---

### Step 4: 動画取得の最終確認（2分）

#### パターンA: MJPEG/HTTPストリーム

```bash
# 5秒間受信してファイルサイズ確認
timeout 5 curl --digest -u $USER:$PASS "http://${IP}:${PORT}/stw-cgi/video.cgi?msubmenu=mjpeg&action=view&Channel=0" \
  -o test_mjpeg_5sec.mjpeg

ls -lh test_mjpeg_5sec.mjpeg
# 期待: 500KB〜5MB（5秒分のJPEGフレーム）
# 失敗: 0バイト or <1KB（エラーメッセージのみ）
```

**成功判定**: ファイルサイズ > 100KB → **動画取得可能 ✅**

#### パターンB: RTSP（ポートが判明した場合）

```bash
# Ubuntu/Windows (ffmpegインストール済み)
ffmpeg -rtsp_transport tcp \
  -i "rtsp://${USER}:${PASS}@${IP}:554/stream1" \
  -t 5 -c copy test_rtsp_5sec.mp4

# または
ffprobe -rtsp_transport tcp \
  "rtsp://${USER}:${PASS}@${IP}:554/stream1" 2>&1 | grep -E "(Stream|Video|Duration)"
```

**成功判定**: 
- ffmpeg → test_rtsp_5sec.mp4 が作成され、サイズ > 0
- ffprobe → `Stream #0:0: Video: h264` のような出力

**失敗時の典型エラー**:
- `401 Unauthorized` → 認証NG（ユーザー名/パスワード/RTSPパス誤り）
- `Connection refused` → ポート/IP誤り
- `Invalid data found` → RTSPではない（HTTPなど）

---

## 2) 詳細ルート（確実に潰し込む）

### Step 5: 全ポートスキャン（安全範囲）

```bash
# 一般的なIPカメラ/NVRポート
sudo nmap -sV -p 80,443,554,8000-9000,10554,37777,8080-8090,1935 192.168.0.233 \
  -oN nvr_portscan.txt

# 結果の解釈
cat nvr_portscan.txt
```

**チェックポイント**:
- **rtsp-server** → RTSP可能
- **http** → Web UI（既知）
- **unknown** → プロプライエタリ（後述）

---

### Step 6: cgiエンドポイント総当たり（低負荷）

```bash
# よくあるcgiパターンをリスト化
cat > cgi_candidates.txt <<EOF
/stw-cgi/video.cgi?msubmenu=mjpeg&action=view&Channel=0
/stw-cgi/video.cgi?msubmenu=stream&action=view&Channel=0
/stw-cgi/video.cgi?msubmenu=video&action=view&Channel=0
/stw-cgi/video.cgi?msubmenu=record&action=view&Channel=0
/cgi-bin/video.cgi?msubmenu=mjpeg&action=view&Channel=0
/cgi-bin/mjpeg
/axis-cgi/mjpg/video.cgi
/api/live/0
/video/mjpeg.cgi
/videostream.cgi?rate=11&user=${USER}&pwd=${PASS}
EOF

# 順次テスト（1秒ごとに実行）
while IFS= read -r path; do
  echo "Testing: $path"
  curl --digest -u $USER:$PASS -m 3 "http://${IP}:${PORT}${path}" -D - -o /dev/null 2>&1 | head -n 10
  sleep 1
done < cgi_candidates.txt
```

**成功判定**: HTTP 200 + Content-Type が動画系

---

### Step 7: ffmpegで複数プロトコル試行

```bash
# HTTP (Digest認証は事前にcurlでCookieを取得するかBasic認証に切り替える)
ffmpeg -headers "Authorization: Digest username=\"${USER}\", ..." \
  -i "http://${IP}:${PORT}/stw-cgi/video.cgi?msubmenu=mjpeg&action=view&Channel=0" \
  -t 5 -c copy test_http.mp4

# RTSP (よくあるパス)
for path in /stream1 /0 /ch0 /cam/realmonitor?channel=1; do
  echo "Testing RTSP path: $path"
  ffprobe -rtsp_transport tcp -i "rtsp://${USER}:${PASS}@${IP}:554${path}" 2>&1 | grep -i stream
done

# HLS (m3u8)
ffprobe -i "http://${IP}:${PORT}/hls/stream.m3u8" 2>&1 | grep -i playlist
```

**注意**: ffmpegはDigest認証を直接サポートしていないため、HTTPの場合は以下の方法が必要：
1. curlでセッションCookieを取得 → ffmpegに渡す
2. NVR側でBasic認証を有効化（非推奨）
3. RTSP経由に切り替え

---

### Step 8: 録画ファイルダウンロードAPI探索

```bash
# よくあるダウンロードcgi
curl --digest -u $USER:$PASS "http://${IP}:${PORT}/stw-cgi/record.cgi?action=list&Channel=0" -o record_list.json
curl --digest -u $USER:$PASS "http://${IP}:${PORT}/stw-cgi/media.cgi?action=list" -o media_list.json

# ファイル名が判明した場合
curl --digest -u $USER:$PASS "http://${IP}:${PORT}/stw-cgi/media.cgi?action=download&file=20251218_120000.mp4" \
  -o downloaded_video.mp4
```

---

## 3) 実行ログを貼る場所（報告すべき情報）

調査結果を以下のフォーマットで記録してください：

```markdown
## 調査結果レポート

### 環境
- OS: [Ubuntu 22.04 / Windows 11]
- 実行日時: [YYYY-MM-DD HH:MM]
- NVR IP: 192.168.0.233
- テスト実施者: [名前]

### Step 1: 動画エンドポイント探索
[curl コマンドの出力をここに貼り付け]

### Step 2: Web UI調査
[HTMLソース or Network タブのスクリーンショット]

### Step 3: ポートスキャン
```
[nmap 出力]
```

### Step 4: 動画取得テスト
[成功/失敗の判定とファイルサイズ]

### 結論
- [ ] 動画取得可能（方法: MJPEG / RTSP / HLS / ファイルDL）
- [ ] 動画取得不可（理由: 認証NG / APIなし / ポート閉じ）
- [ ] 追加調査必要（詳細: ）

### 次アクション
[管理画面確認 / RTSP有効化 / カメラ直接アクセス検討 など]
```

---

## 【動画取得パターン一覧と確認方法】

| パターン | プロトコル | 確認コマンド | 期待レスポンス |
|----------|------------|--------------|----------------|
| **MJPEGストリーム** | HTTP | `curl -m 5 <URL>` | `Content-Type: multipart/x-mixed-replace` |
| **HLS** | HTTP | `curl <URL.m3u8>` | `#EXTM3U` プレイリスト |
| **RTSPストリーム** | RTSP | `ffprobe rtsp://<URL>` | `Stream #0:0: Video: h264` |
| **MP4ダウンロード** | HTTP | `curl <download_URL>` | `Content-Type: video/mp4` |
| **プロプライエタリ** | 独自 | ベンダーSDK必須 | - |

---

## 【成功判定基準】

### ✅ 明確な成功
1. **MJPEGストリーム**: 5秒間受信してファイルサイズ > 100KB
2. **RTSPストリーム**: ffmpegで5秒保存 → mp4ファイル作成 > 0バイト
3. **HLSプレイリスト**: .m3u8取得成功 + .ts セグメント取得成功
4. **録画ファイル**: mp4/aviファイルダウンロード完了（再生可能）

### ⚠️ 部分成功（追加作業必要）
- APIエンドポイントは見つかったが認証エラー（401）→ パラメータ調整
- RTSPポートは開いているが接続拒否 → 管理画面でRTSP有効化必要

### ❌ 失敗
- すべてのポート CLOSED + cgiエンドポイントすべて 404
- NVR管理画面で「ストリーミング無効」設定が変更不可

---

## 【失敗時の次アクション】

### A. 管理画面でRTSP有効化
1. ブラウザで `http://192.168.0.233:8080` にログイン
2. **設定 → ネットワーク → RTSP** を探す
3. 「RTSPサービス有効」にチェック
4. ポート番号を確認（デフォルト 554 or 8554）
5. 認証方式を「Digest」に設定
6. 保存 → NVR再起動
7. 再度 Step 3 を実行

### B. カメラ直接アクセスを検討
- **判断基準**: NVR経由で動画APIがなく、NVRは録画のみの用途
- **方法**: 
  1. NVR管理画面でカメラのIPアドレスを確認
  2. カメラに直接アクセス（例: `http://192.168.0.101`）
  3. カメラ自体のRTSP/MJPEGストリームを使用

### C. ベンダーサポートに問い合わせ
- **質問例**: 「Wisenet NVR 経由でプログラムから動画ストリームを取得したい。APIドキュメントはあるか？」
- **必要情報**: 機種名、ファームウェアバージョン、現在の設定状況

### D. Cookie認証への切り替え
- Digest認証ではなく、セッションログインが必要な場合：
  ```bash
  # ログインしてCookieを保存
  curl -c cookies.txt --digest -u $USER:$PASS "http://${IP}:${PORT}/login"
  
  # Cookieを使って動画取得
  curl -b cookies.txt "http://${IP}:${PORT}/stw-cgi/video.cgi?msubmenu=mjpeg&action=view&Channel=0" \
    -o test_with_cookie.mjpeg
  ```

---

## 【重要な注意点】

### セキュリティ
- ✅ パスワードはコマンド履歴に残るため、検証後は `history -c` で削除
- ✅ ポートスキャンは自社ネットワーク内のみ（外部は違法）
- ❌ パスワード総当たり（Brute Force）は絶対に行わない

### 負荷
- ✅ curl の `-m` オプションでタイムアウト設定（5秒程度）
- ✅ 連続リクエストは `sleep 1` を挟む
- ❌ 並列大量リクエストは避ける（NVRが応答不能になる可能性）

### ログ
- NVRのログイン失敗ログに記録される可能性
- セキュリティポリシーで「3回失敗でロック」がある場合は慎重に

### プラットフォーム互換性
- **Ubuntu 22.04**: すべてのコマンド動作
- **Windows (WSL2)**: Ubuntuと同等
- **Windows (PowerShell)**: curlは使えるがbashスクリプトは不可
  - 代替: Git Bash or コマンドをPowerShell風に書き換え
- **Docker (dev container)**: `apt install -y curl nmap ffmpeg` で準備

---

## 【実装への移行（本調査完了後）】

調査で動画取得が確認できたら、以下の順で実装：

1. **FastAPI エンドポイント設計**
   - `/api/nvr/stream/{channel}` → プロキシ経由でストリーム配信
   - `/api/nvr/snapshot/{channel}` → 既存のスナップショット（実装済み）

2. **ストリーミングプロキシ実装**
   - MJPEGの場合: `StreamingResponse` で multipart/x-mixed-replace
   - RTSPの場合: ffmpeg でトランスコード → HLS/FLV
   - HLSの場合: プレイリスト + セグメントをプロキシ

3. **React フロントエンド**
   - `<img src="/api/nvr/stream/0">` （MJPEG）
   - `<video>` + hls.js （HLS）
   - WebRTC（低遅延が必要な場合）

4. **認証処理**
   - FastAPIでDigest認証をラップ（クライアントからはBearerトークン）
   - セッション管理（長時間ストリーム用）

---

## 【クイックリファレンス】

```bash
# 環境変数設定（コピペ用）
export NVR_USER="<YOUR_USER>"
export NVR_PASS="<YOUR_PASS>"
export NVR_IP="192.168.0.233"
export NVR_PORT="8080"

# MJPEG 5秒テスト
timeout 5 curl --digest -u $NVR_USER:$NVR_PASS \
  "http://${NVR_IP}:${NVR_PORT}/stw-cgi/video.cgi?msubmenu=mjpeg&action=view&Channel=0" \
  -o test_mjpeg.mjpeg && ls -lh test_mjpeg.mjpeg

# RTSP テスト（ポート554が開いている場合）
ffmpeg -rtsp_transport tcp -i "rtsp://${NVR_USER}:${NVR_PASS}@${NVR_IP}:554/stream1" \
  -t 5 -c copy test_rtsp.mp4 && ls -lh test_rtsp.mp4

# ポート再スキャン
nmap -sV -p 554,8554,10554,37777 $NVR_IP
```

---

## 【よくある質問】

**Q: ffmpegで「Digest authentication is not supported」と出る**  
A: HTTPストリームの場合、ffmpegは直接Digest認証を扱えません。以下の回避策：
- RTSPプロトコルに切り替え（RTSPはDigest対応）
- curlでストリームを取得 → ffmpegにパイプ
  ```bash
  curl --digest -u $USER:$PASS <URL> | ffmpeg -i pipe:0 -t 5 output.mp4
  ```

**Q: Web UIはログインできるが、curlでは401が出る**  
A: セッション/Cookie認証の可能性。以下を試す：
```bash
# ログインページにPOST
curl -c cookies.txt -X POST -d "username=${USER}&password=${PASS}" "http://${IP}:${PORT}/login"
# Cookieを使用
curl -b cookies.txt "http://${IP}:${PORT}/stw-cgi/video.cgi?..."
```

**Q: NVRではなくカメラ直接アクセスすべき？**  
A: 以下の場合はカメラ直接が有効：
- NVRがストリーミング機能を持たない（録画専用）
- カメラ台数が少ない（<4台）
- NVR経由だと遅延が大きい

---

**調査成功を祈ります！結果を上記フォーマットで報告してください。**
