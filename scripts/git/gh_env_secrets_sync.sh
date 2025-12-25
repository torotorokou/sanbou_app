#!/usr/bin/env bash
set -euo pipefail

# Sync .env / JSON / CSV to GitHub Environments Secrets via GitHub CLI (gh)
#
# Features
# - Create or update GitHub Environments (dev/stg/prod etc.) automatically
# - Import from .env file (KEY=VALUE), JSON, or CSV
# - Same secret keys across environments, values switched per env
# - No secrets are printed by default (safe logs); use --dry-run to preview
#
# Requirements
# - gh (GitHub CLI) logged in with repo admin permissions (v2.0+ recommended)
# - jq (for JSON import)
#
# Usage examples
#   Single env from .env file:
#     ./scripts/gh_env_secrets_sync.sh \
#       --repo torotorokou/sanbou_app --env stg --file env/.env.common
#
#   Multi env from JSON (env -> { KEY: VALUE }):
#     ./scripts/gh_env_secrets_sync.sh \
#       --repo torotorokou/sanbou_app --json scripts/examples/secrets.json
#
#   Multi env from CSV (env,key,value):
#     ./scripts/gh_env_secrets_sync.sh \
#       --repo torotorokou/sanbou_app --csv scripts/examples/secrets.csv

SCRIPT_NAME=$(basename "$0")

REPO=""
ENV_NAME=""
DOTENV_FILE=""
JSON_FILE=""
CSV_FILE=""
PREFIX=""
DRY_RUN=0

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
note() { printf "[info] %s\n" "$*"; }
warn() { printf "[warn] %s\n" "$*"; }
err()  { printf "[error] %s\n" "$*" 1>&2; }

usage() {
  cat <<USAGE
${SCRIPT_NAME} - Sync secrets to GitHub Environments

Options:
  -R, --repo <owner/repo>     Target repository (default: current repo from gh)
  -e, --env <name>            Environment name (required for --file)
  -f, --file <path>           .env file to import (KEY=VALUE per line)
      --json <path>           JSON file to import (env -> { KEY: VALUE }) or array of {env,key,value}
      --csv <path>            CSV file to import (headers: env,key,value)
      --prefix <str>          Optional prefix to add to secret keys (e.g., APP_)
      --dry-run               Show actions without applying changes
  -h, --help                  Show this help

Examples:
  ${SCRIPT_NAME} --repo torotorokou/sanbou_app --env stg --file env/.env.common
  ${SCRIPT_NAME} --repo torotorokou/sanbou_app --json scripts/examples/secrets.json
  ${SCRIPT_NAME} --repo torotorokou/sanbou_app --csv scripts/examples/secrets.csv
USAGE
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "Required command not found: $1"
    exit 1
  fi
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -R|--repo) REPO="$2"; shift 2;;
    -e|--env) ENV_NAME="$2"; shift 2;;
    -f|--file) DOTENV_FILE="$2"; shift 2;;
    --json) JSON_FILE="$2"; shift 2;;
    --csv) CSV_FILE="$2"; shift 2;;
    --prefix) PREFIX="$2"; shift 2;;
    --dry-run) DRY_RUN=1; shift;;
    -h|--help) usage; exit 0;;
    *) err "Unknown option: $1"; usage; exit 1;;
  esac
done

# Validate inputs
if [[ ${DRY_RUN:-0} -ne 1 ]]; then
  need_cmd gh
fi

if [[ -z "$REPO" ]]; then
  # Attempt to detect current repo via gh
  if gh repo view --json nameWithOwner >/dev/null 2>&1; then
    REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
  else
    err "--repo is required when not in a GitHub repo directory"
    exit 1
  fi
fi

if [[ -n "$DOTENV_FILE" ]]; then
  if [[ -z "$ENV_NAME" ]]; then
    err "--env is required when using --file"
    exit 1
  fi
  if [[ ! -f "$DOTENV_FILE" ]]; then
    err ".env file not found: $DOTENV_FILE"
    exit 1
  fi
fi

if [[ -n "$JSON_FILE" ]]; then
  HAVE_JQ=0
  if command -v jq >/dev/null 2>&1; then
    HAVE_JQ=1
  else
    if ! command -v python3 >/dev/null 2>&1; then
      err "JSON import requires jq or python3, but neither is installed"
      exit 1
    fi
    warn "jq が見つからないため python3 フォールバックで JSON を解析します"
  fi
  [[ -f "$JSON_FILE" ]] || { err "JSON file not found: $JSON_FILE"; exit 1; }
fi

if [[ -n "$CSV_FILE" ]]; then
  [[ -f "$CSV_FILE" ]] || { err "CSV file not found: $CSV_FILE"; exit 1; }
fi

if [[ -z "$DOTENV_FILE" && -z "$JSON_FILE" && -z "$CSV_FILE" ]]; then
  err "One of --file, --json or --csv is required"
  usage
  exit 1
fi

OWNER=${REPO%%/*}
REPO_NAME=${REPO#*/}

ensure_environment() {
  local env="$1"
  if [[ $DRY_RUN -eq 1 ]]; then
    note "[dry-run] ensure environment exists: $env"
    return 0
  fi
  # Create or update environment via REST API
  printf '%s' '{"wait_timer":0}' | gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    -H "Content-Type: application/json" \
    "/repos/$OWNER/$REPO_NAME/environments/$env" \
    --input - \
    >/dev/null
}

set_secret() {
  local env="$1" key="$2" value="$3"
  local full_key="$key"
  if [[ -n "$PREFIX" ]]; then
    full_key="${PREFIX}${key}"
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    note "[dry-run] $env: set $full_key=(redacted)"
    return 0
  fi
  # Use -b to pass the secret body; avoid printing value
  env GH_PAGER=cat gh secret set "$full_key" \
    --repo "$REPO" \
    --env "$env" \
    -b "$value" \
    >/dev/null
}

parse_and_apply_env_file() {
  local env="$1" file="$2"
  ensure_environment "$env"
  note "Importing from $file into environment '$env' on $REPO"
  # Secure summary of keys (names only; no values)
  local -a summary_keys=()
  while IFS= read -r line || [[ -n "$line" ]]; do
    # Trim leading/trailing spaces
    line="${line%%$'\r'}"
    # Skip empty or commented lines
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    # Support inline comments only when not quoted
    if [[ "$line" != *\"* && "$line" != *\'* ]]; then
      line="${line%%#*}"
    fi
    # Split KEY=VALUE (first '=')
    if [[ "$line" != *"="* ]]; then
      continue
    fi
    local key="${line%%=*}"
    local value="${line#*=}"
    # Trim whitespace
    key="$(echo -n "$key" | awk '{$1=$1;print}')"
    value="$(echo -n "$value" | sed -e 's/^\s*//' -e 's/\s*$//')"
    # Strip surrounding quotes if present
    if [[ "$value" =~ ^\".*\"$ ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "$value" =~ ^\'.*\'$ ]]; then
      value="${value:1:${#value}-2}"
    fi
    [[ -z "$key" ]] && continue
    set_secret "$env" "$key" "$value"
    # collect key for summary (dedupe)
    local seen=0 k
    for k in "${summary_keys[@]}"; do [[ "$k" == "$key" ]] && seen=1 && break; done
    [[ $seen -eq 0 ]] && summary_keys+=("$key")
  done < "$file"
  if [[ ${#summary_keys[@]} -gt 0 ]]; then
    note "Applied keys from $file (${#summary_keys[@]}):"
    for k in "${summary_keys[@]}"; do
      note "  - $k"
    done
  else
    warn "No applicable keys found in $file"
  fi
}

apply_from_json() {
  local json_path="$1"
  note "Importing from JSON: $json_path into $REPO"
  local -a summary_pairs=()
  if [[ $HAVE_JQ -eq 1 ]]; then
    # jq path (original behavior)
    if jq -e 'type=="object" and (to_entries|length) > 0' "$json_path" >/dev/null 2>&1; then
      while IFS=, read -r env key value; do
        ensure_environment "$env"
        set_secret "$env" "$key" "$value"
        summary_pairs+=("$env:$key")
      done < <(jq -r 'to_entries[] as $e | $e.value|to_entries[] | "\u0001",$e.key,",",.key,",",(.value|tostring),"\u0002"' "$json_path" \
        | tr -d '\n' \
        | sed $'s/\u0001/\n/g' \
        | sed $'s/\u0002/\n/g' \
        | sed '/^$/d' \
        | sed '1d')
    else
      while IFS=, read -r env key value; do
        ensure_environment "$env"
        set_secret "$env" "$key" "$value"
        summary_pairs+=("$env:$key")
      done < <(jq -r '.[] | "\u0001",.env,",",.key,",",(.value|tostring),"\u0002"' "$json_path" \
        | tr -d '\n' \
        | sed $'s/\u0001/\n/g' \
        | sed $'s/\u0002/\n/g' \
        | sed '/^$/d')
    fi
  else
    # python3 fallback (supports object schema and array schema)
    while IFS=, read -r env key value; do
      ensure_environment "$env"
      set_secret "$env" "$key" "$value"
      summary_pairs+=("$env:$key")
    done < <(python3 - "$json_path" <<'PY'
import json, sys
path = sys.argv[1]
with open(path,'r',encoding='utf-8') as f:
    data = json.load(f)
rows = []
if isinstance(data, dict):
    for env, kv in data.items():
        if isinstance(kv, dict):
            for k, v in kv.items():
                rows.append((env, k, str(v)))
elif isinstance(data, list):
    for item in data:
        if isinstance(item, dict) and {'env','key','value'} <= item.keys():
            rows.append((str(item['env']), str(item['key']), str(item['value'])))
for r in rows:
    # emit env,key,value CSV-ish (no commas inside fields assumption)
    print(f"{r[0]},{r[1]},{r[2]}")
PY
  )
  fi
  if [[ ${#summary_pairs[@]} -gt 0 ]]; then
    note "Applied keys from JSON (${#summary_pairs[@]}):"
    for p in "${summary_pairs[@]}"; do
      note "  - $p"
    done
  else
    warn "No applicable keys found in JSON"
  fi
}

apply_from_csv() {
  local csv_path="$1"
  note "Importing from CSV: $csv_path into $REPO"
  local header=1
  local -a summary_pairs=()
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%$'\r'}"
    [[ -z "$line" ]] && continue
    if [[ $header -eq 1 ]]; then
      header=0
      continue
    fi
    # naive CSV split (no quotes support). For robust cases prefer JSON.
    IFS=, read -r env key value <<< "$line"
    env="$(echo -n "$env" | awk '{$1=$1;print}')"
    key="$(echo -n "$key" | awk '{$1=$1;print}')"
    # value may contain commas; best-effort: take rest of line after env,key
    if [[ "$line" == *","*","* ]]; then
      value="${line#*,}"
      value="${value#*,}"
    fi
    # trim spaces
    value="$(echo -n "$value" | sed -e 's/^\s*//' -e 's/\s*$//')"
    ensure_environment "$env"
    set_secret "$env" "$key" "$value"
    summary_pairs+=("$env:$key")
  done < "$csv_path"
  if [[ ${#summary_pairs[@]} -gt 0 ]]; then
    note "Applied keys from CSV (${#summary_pairs[@]}):"
    for p in "${summary_pairs[@]}"; do
      note "  - $p"
    done
  else
    warn "No applicable keys found in CSV"
  fi
}

bold "GitHub Environments Secrets Sync"
note "Repository: $REPO"
[[ -n "$ENV_NAME" ]] && note "Environment: $ENV_NAME"
[[ -n "$PREFIX" ]] && note "Key prefix: $PREFIX"
[[ $DRY_RUN -eq 1 ]] && warn "Dry-run enabled: no changes will be applied"

if [[ -n "$DOTENV_FILE" ]]; then
  parse_and_apply_env_file "$ENV_NAME" "$DOTENV_FILE"
fi

if [[ -n "$JSON_FILE" ]]; then
  apply_from_json "$JSON_FILE"
fi

if [[ -n "$CSV_FILE" ]]; then
  apply_from_csv "$CSV_FILE"
fi

bold "Done"
