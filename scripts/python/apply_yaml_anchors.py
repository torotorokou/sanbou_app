#!/usr/bin/env python3
"""
docker-compose.{stg,prod}.yml に YAML アンカーを適用して DRY にする
"""
import sys
from collections import OrderedDict

import yaml


def represent_ordereddict(dumper, data):
    """OrderedDict を YAML にシリアライズ"""
    return dumper.represent_dict(data.items())


yaml.add_representer(OrderedDict, represent_ordereddict)


def apply_anchors(input_file: str, env_type: str):
    """
    docker-compose ファイルに YAML アンカーを適用

    Args:
        input_file: 入力ファイルパス
        env_type: 'stg' or 'prod'
    """
    with open(input_file) as f:
        data = yaml.safe_load(f)

    # アンカー定義を追加
    if env_type == "stg":
        env_files = ["../env/.env.common", "../env/.env.vm_stg", "../secrets/.env.vm_stg.secrets"]
    else:  # prod
        env_files = ["../env/.env.common", "../env/.env.vm_prod", "../secrets/.env.vm_prod.secrets"]

    common_logging = {"driver": "json-file", "options": {"max-size": "10m", "max-file": "3"}}

    common_healthcheck_base = {"interval": "30s", "timeout": "5s", "retries": 3}

    # 各サービスに適用
    services = data.get("services", {})

    for service_name, service_config in services.items():
        # env_file を統一
        if "env_file" in service_config:
            service_config["env_file"] = env_files

        # logging を統一
        if "logging" in service_config:
            service_config["logging"] = common_logging.copy()

        # environment の TZ を整理
        if "environment" in service_config:
            env = service_config["environment"]
            if isinstance(env, list):
                # リスト形式の場合
                new_env = OrderedDict()
                new_env["TZ"] = "Asia/Tokyo"
                for item in env:
                    if isinstance(item, str):
                        if "=" in item:
                            k, v = item.split("=", 1)
                            if k.strip() != "TZ":
                                new_env[k.strip()] = v
                        elif item.strip() != "TZ=Asia/Tokyo":
                            # 単独の文字列（環境変数名のみ）
                            new_env[item.strip()] = None
                    elif isinstance(item, dict):
                        for k, v in item.items():
                            if k != "TZ":
                                new_env[k] = v
                service_config["environment"] = new_env
            elif isinstance(env, dict):
                # 辞書形式の場合
                if "TZ" not in env:
                    env_ordered = OrderedDict()
                    env_ordered["TZ"] = "Asia/Tokyo"
                    env_ordered.update(env)
                    service_config["environment"] = env_ordered

        # healthcheck の共通部分を適用
        if "healthcheck" in service_config:
            hc = service_config["healthcheck"]
            if "interval" not in hc:
                hc["interval"] = common_healthcheck_base["interval"]
            if "timeout" not in hc:
                hc["timeout"] = common_healthcheck_base["timeout"]
            if "retries" not in hc:
                hc["retries"] = common_healthcheck_base["retries"]

    # 出力
    output_file = input_file
    with open(output_file, "w") as f:
        # ヘッダーコメントを保持
        f.write("## " + "=" * 61 + "\n")
        if env_type == "stg":
            f.write("## docker-compose.stg.yml (GCP VM ステージング環境 - ENV=vm_stg 用)\n")
            f.write("## - Makefile 経由で起動: make up ENV=vm_stg\n")
            f.write(
                "## - 使用する env ファイル: env/.env.common + env/.env.vm_stg + secrets/.env.vm_stg.secrets\n"
            )
            f.write("## - 特徴:\n")
            f.write("##   * VPN / Tailscale 経由でのアクセス（IAP なし）\n")
            f.write("##   * AUTH_MODE=vpn_dummy (固定ユーザーでのダミー認証)\n")
            f.write("##   * Artifact Registry のイメージを利用（pull のみ、build なし)\n")
            f.write("##   * 3層ネットワーク分離（edge/app/data）\n")
            f.write(
                "## - イメージ: asia-northeast1-docker.pkg.dev/honest-sanbou-app-stg/sanbou-app/*:stg-latest\n"
            )
        else:
            f.write("## docker-compose.prod.yml (GCP VM 本番環境 - ENV=vm_prod 用)\n")
            f.write("## - Makefile 経由で起動: make up ENV=vm_prod\n")
            f.write(
                "## - 使用する env ファイル: env/.env.common + env/.env.vm_prod + secrets/.env.vm_prod.secrets\n"
            )
            f.write("## - 特徴:\n")
            f.write("##   * LB + IAP 経由での外部公開（HTTPS → HTTP）\n")
            f.write("##   * AUTH_MODE=iap (IAP ヘッダ検証必須)\n")
            f.write("##   * Artifact Registry のイメージを利用（pull のみ、build なし）\n")
            f.write("##   * 3層ネットワーク分離（edge/app/data）\n")
            f.write("##   * nginx のみ外部公開（80/443）、backend は内部ネットワークのみ\n")
            if env_type == "prod":
                f.write(
                    "## - イメージ: asia-northeast1-docker.pkg.dev/honest-sanbou-app-prod/sanbou-app/*:prod-latest\n"
                )
            else:
                f.write(
                    "## - イメージ: asia-northeast1-docker.pkg.dev/honest-sanbou-app-stg/sanbou-app/*:stg-latest\n"
                )
        f.write("## " + "=" * 61 + "\n\n")

        # YAML アンカー定義
        f.write("# " + "=" * 77 + "\n")
        f.write("# YAML アンカー定義（共通設定の再利用）\n")
        f.write("# " + "=" * 77 + "\n")
        f.write("x-common-env: &common-env-files\n")
        for ef in env_files:
            f.write(f"  - {ef}\n")
        f.write("\n")
        f.write("x-common-logging: &common-logging\n")
        f.write("  driver: json-file\n")
        f.write("  options:\n")
        f.write('    max-size: "10m"\n')
        f.write('    max-file: "3"\n')
        f.write("\n")
        f.write("x-common-healthcheck: &common-healthcheck\n")
        f.write("  interval: 30s\n")
        f.write("  timeout: 5s\n")
        f.write("  retries: 3\n")
        f.write("\n")
        f.write("x-tz-env: &tz-environment\n")
        f.write('  TZ: "Asia/Tokyo"\n')
        f.write("\n")

        # services 以降
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"✓ {output_file} に YAML アンカーを適用しました")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python apply_yaml_anchors.py <file> <stg|prod>")
        sys.exit(1)

    apply_anchors(sys.argv[1], sys.argv[2])
