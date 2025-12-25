#!/bin/bash
# =============================================================================
# セキュリティパターン定義 - 機密情報検出用の共通ライブラリ
# =============================================================================
# Git フックやスクリプトで共通利用する機密情報パターンを一元管理

# =============================================================================
# 機密ファイルパターン（ファイルパスの正規表現）
# =============================================================================
declare -a FORBIDDEN_FILE_PATTERNS=(
    # 環境変数ファイル（テンプレート以外）
    "^env/\.env\."
    # Secretsファイル（テンプレート以外）
    "^secrets/\.env\..*\.secrets$"
    # GCP サービスアカウントキー
    "^secrets/gcp-sa.*\.json$"
    "gcp-sa\.json$"
    "gcs-key.*\.json$"
    # SSL/TLS 証明書と秘密鍵
    "\.pem$"
    "\.key$"
    "\.crt$"
    # SSH 鍵
    "id_rsa$"
    "id_ed25519$"
    # データベースダンプ
    "\.dump$"
    "\.sql\.gz$"
)

# =============================================================================
# 許可されるファイルパターン（例外）
# =============================================================================
declare -a ALLOWED_FILE_PATTERNS=(
    # テンプレートファイル
    "\.example$"
    "\.template$"
    # ドキュメント
    "README\.md$"
    "\.md$"
    # 公開鍵（秘密鍵ではない）
    "\.pub$"
)

# =============================================================================
# 機密情報の内容パターン（ファイル内容の正規表現）
# =============================================================================
declare -a SENSITIVE_CONTENT_PATTERNS=(
    # データベースパスワード（実際の値のみ、変数参照除外）
    "POSTGRES_PASSWORD[[:space:]]*=[[:space:]]*['\"][^\$][^'\"]{3,}['\"]"

    # データベース DSN（接続文字列）
    # PostgreSQL/Postgres DSN (password >= 8 chars)
    "postgresql://[^:]+:[^@[:space:]]{8,}@"
    "postgres://[^:]+:[^@[:space:]]{8,}@"
    # MySQL DSN (password >= 8 chars)
    "mysql://[^:]+:[^@[:space:]]{8,}@"
    # Redis DSN (password >= 8 chars)
    "redis://:[^@[:space:]]{8,}@"
    # docker-compose environment variables with DSN
    "DB_DSN[[:space:]]*[:=][[:space:]]*['\"]?[^'\"[:space:]]*://[^:]+:[^@[:space:]]{8,}@"
    "DATABASE_URL[[:space:]]*[:=][[:space:]]*['\"]?[^'\"[:space:]]*://[^:]+:[^@[:space:]]{8,}@"

    # GCP 秘密鍵
    "BEGIN PRIVATE KEY"
    "BEGIN RSA PRIVATE KEY"
    # API キー（長い英数字文字列）
    "[aA][pP][iI][-_]?[kK][eE][yY][[:space:]]*[:=][[:space:]]*['\"][A-Za-z0-9+/]{20,}['\"]"
    # シークレットトークン
    "[sS][eE][cC][rR][eE][tT][-_]?[tT][oO][kK][eE][nN][[:space:]]*[:=][[:space:]]*['\"][A-Za-z0-9+/]{20,}['\"]"
    # IAP Audience（実際の値のみ）
    "IAP_AUDIENCE[[:space:]]*=[[:space:]]*['\"][^\$][^'\"]{20,}['\"]"
    # GCP Service Account Key（JSON形式）
    "\"type\"[[:space:]]*:[[:space:]]*\"service_account\""
    # AWS アクセスキー
    "AWS_ACCESS_KEY_ID[[:space:]]*=[[:space:]]*['\"]AKIA[A-Z0-9]{16}['\"]"
    # JWT シークレット
    "JWT_SECRET[[:space:]]*=[[:space:]]*['\"][^'\"]{20,}['\"]"
)

# =============================================================================
# 内容チェックの除外パターン（誤検知を防ぐ）
# =============================================================================
declare -a CONTENT_EXCLUSION_PATTERNS=(
    # Python コード内の環境変数参照
    "os\.getenv"
    "os\.environ"
    # 設定取得関数
    "get_secret"
    "get_iap_audience"
    # Git コマンド例
    "git log -S"
    "git show"
    # コメント行
    "^\+[[:space:]]*#"
    "^[[:space:]]*#"
    # シェル変数参照
    "^\+\$"
    '=[[:space:]]*\$'
    # 空の値
    "=[[:space:]]*$"
    "=[[:space:]]*#"
    # ドキュメント内のコード例（バッククォート） - POSIX準拠
    '\`[^\`]+\`'
    # マークダウンのコードブロック
    '^\+.*```'
    # 説明文
    "例:"
    "Example:"
    "検出対象:"
    "パターン:"
    # DSN内のプレースホルダー
    '\$\{[^}]+\}'  # ${VAR}
    '\$\([^)]+\)'  # $(VAR)
    '<[^>]+>'      # <password>
    '\*\*\*+'      # ****
    'example'      # example_pass
    'your_'        # your_password
    'placeholder'  # placeholder
    # BEGIN PRIVATE KEY を含むログやドキュメント
    "^\+[0-9]+\."
)

# =============================================================================
# ヘルパー関数: ファイルが禁止パターンに一致するかチェック
# =============================================================================
# 引数: $1 = ファイルパス
# 戻り値: 0 = 禁止, 1 = 許可
is_forbidden_file() {
    local file="$1"

    # まず許可パターンをチェック（テンプレート等）
    for pattern in "${ALLOWED_FILE_PATTERNS[@]}"; do
        if [[ "$file" =~ $pattern ]]; then
            return 1  # 許可
        fi
    done

    # 禁止パターンをチェック
    for pattern in "${FORBIDDEN_FILE_PATTERNS[@]}"; do
        if [[ "$file" =~ $pattern ]]; then
            return 0  # 禁止
        fi
    done

    return 1  # 許可
}

# =============================================================================
# ヘルパー関数: ファイル内容に機密情報が含まれるかチェック
# =============================================================================
# 引数: $1 = 検査対象のテキスト（diff出力等）
# 戻り値: 0 = 機密情報あり, 1 = なし
contains_sensitive_content() {
    local content="$1"
    local found=1  # 初期値: なし

    for pattern in "${SENSITIVE_CONTENT_PATTERNS[@]}"; do
        # パターンが空の場合はスキップ
        [ -z "$pattern" ] && continue

        # パターンに一致する行を取得
        local matched_lines
        matched_lines=$(echo "$content" | grep -E "$pattern" 2>/dev/null || true)

        if [ -z "$matched_lines" ]; then
            continue
        fi

        # 除外パターンでフィルタリング
        local filtered_lines="$matched_lines"
        for exclusion in "${CONTENT_EXCLUSION_PATTERNS[@]}"; do
            [ -z "$exclusion" ] && continue
            filtered_lines=$(echo "$filtered_lines" | grep -vE "$exclusion" 2>/dev/null || true)
        done

        # フィルタリング後も残っている行があれば機密情報あり
        if [ -n "$filtered_lines" ]; then
            echo "$filtered_lines"
            found=0
        fi
    done

    return $found
}

# =============================================================================
# ヘルパー関数: .gitignore に必須パターンが含まれるかチェック
# =============================================================================
# 引数: $1 = .gitignore の内容
# 戻り値: 0 = 正常, 1 = 不足
check_gitignore_patterns() {
    local gitignore_content="$1"
    local missing_patterns=()

    # 必須パターンのリスト
    local -a required_patterns=(
        "^/env/"
        "^/secrets/"
        "^\.env$"
        "\.pem$"
        "\.key$"
        "gcp-sa.*\.json"
        "gcs-key.*\.json"
    )

    for pattern in "${required_patterns[@]}"; do
        if ! echo "$gitignore_content" | grep -qE "$pattern"; then
            missing_patterns+=("$pattern")
        fi
    done

    if [ ${#missing_patterns[@]} -gt 0 ]; then
        echo "不足しているパターン:"
        printf '  - %s\n' "${missing_patterns[@]}"
        return 1
    fi

    return 0
}

# =============================================================================
# エクスポート（他のスクリプトから利用可能にする）
# =============================================================================
export -f is_forbidden_file
export -f contains_sensitive_content
export -f check_gitignore_patterns
