"""
GCP ADC認証と権限デバッグ用ヘルパーモジュール

Application Default Credentials (ADC) の状態確認と
Cloud Storage アクセス権限のデバッグログ出力を行います。

使用方法:
    from app.infra.adapters.gcp import debug_log_gcp_adc_and_permissions

    # 起動時に1度だけ呼び出す
    if settings.STAGE in ("stg", "prod") and settings.PERMISSION_DEBUG:
        debug_log_gcp_adc_and_permissions(
            bucket_name=settings.GCS_BUCKET_NAME,
            object_prefix=settings.GCS_DATA_PREFIX
        )
"""

import logging
import os

logger = logging.getLogger(__name__)


def debug_log_gcp_adc_and_permissions(
    bucket_name: str | None = None, object_prefix: str | None = None
) -> bool:
    """
    GCP ADC認証と Cloud Storage 権限をデバッグログに出力

    この関数は起動時に1度だけ呼び出すことを想定しています。
    無限ループや定期ジョブの中では呼ばないでください。

    Args:
        bucket_name: 確認対象のGCSバケット名（省略時は環境変数から取得）
        object_prefix: 確認対象のオブジェクトプレフィックス（省略時は環境変数から取得）

    Returns:
        bool: 認証と権限チェックがすべて成功した場合 True、それ以外は False
    """
    logger.info("=" * 80)
    logger.info("🔍 GCP ADC認証 & Storage権限デバッグ開始")
    logger.info("=" * 80)

    # 環境変数からデフォルト値を取得
    if bucket_name is None:
        bucket_name = os.getenv("GCS_BUCKET_NAME", "object_haikibutu")
    if object_prefix is None:
        object_prefix = os.getenv("GCS_DATA_PREFIX", "master")

    stage = os.getenv("STAGE", "dev")
    logger.info(
        f"📋 環境情報: STAGE={stage}, BUCKET={bucket_name}, PREFIX={object_prefix}"
    )

    # google-auth と google-cloud-storage のインポート確認
    try:
        import google.auth
        from google.api_core import exceptions as gcp_exceptions
        from google.auth import exceptions as auth_exceptions
        from google.cloud import storage
    except ImportError as e:
        logger.error(
            f"🔴 GCP SDKのインポートに失敗しました: {e}",
            extra={"operation": "gcp_debug", "status": "import_error", "error": str(e)},
        )
        logger.error(
            "ヒント: google-auth と google-cloud-storage をインストールしてください"
        )
        logger.info("=" * 80)
        return False

    # ステップ1: ADC認証の確認
    logger.info("📡 ステップ1: ADC (Application Default Credentials) 認証確認")
    try:
        credentials, project_id = google.auth.default()
        logger.info("✅ ADC認証に成功しました")
        logger.info(f"   - 認証情報タイプ: {type(credentials).__name__}")
        logger.info(f"   - プロジェクトID: {project_id or '(未設定)'}")

        # サービスアカウントメールの取得（可能な場合）
        service_account_email = getattr(credentials, "service_account_email", None)
        if service_account_email:
            logger.info(f"   - サービスアカウント: {service_account_email}")
        else:
            logger.info("   - サービスアカウント: (取得不可またはユーザー認証)")

    except auth_exceptions.DefaultCredentialsError as e:
        logger.error(
            "🔴 ADC認証に失敗しました (DefaultCredentialsError)",
            extra={
                "operation": "gcp_debug",
                "status": "auth_failed",
                "error": str(e),
                "error_type": "DefaultCredentialsError",
            },
        )
        logger.error(f"   エラー詳細: {e}")
        logger.error("   ヒント:")
        logger.error(
            "   - ローカル開発: 'gcloud auth application-default login' を実行"
        )
        logger.error(
            "   - GCE/Cloud Run: サービスアカウントがVMにアタッチされているか確認"
        )
        logger.error(
            "   - 環境変数: GOOGLE_APPLICATION_CREDENTIALS が正しく設定されているか確認"
        )
        logger.info("=" * 80)
        return False
    except Exception as e:
        logger.error(
            f"🔴 ADC認証中に予期しないエラーが発生: {type(e).__name__}",
            extra={
                "operation": "gcp_debug",
                "status": "auth_unexpected_error",
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        logger.info("=" * 80)
        return False

    # ステップ2: Cloud Storage クライアントの作成
    logger.info("📦 ステップ2: Cloud Storage クライアント作成")
    try:
        storage_client = storage.Client(project=project_id)
        logger.info("✅ Storage クライアントを作成しました")

        # 注: list_buckets() は storage.buckets.list 権限が必要なため、
        # オブジェクトアクセスのみの権限では失敗します。
        # 代わりに対象バケットの存在確認で権限チェックを行います。

    except Exception as e:
        logger.error(
            f"🔴 Storage クライアント作成/一覧取得中にエラー: {type(e).__name__}",
            extra={
                "operation": "gcp_debug",
                "status": "storage_client_error",
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        logger.info("=" * 80)
        return False

    # ステップ3: 対象バケットの存在確認
    logger.info(f"🗂️  ステップ3: 対象バケット '{bucket_name}' の存在確認")
    try:
        bucket = storage_client.bucket(bucket_name)
        if bucket.exists():
            logger.info(f"✅ 対象バケット '{bucket_name}' は存在します")
        else:
            logger.warning(
                f"⚠️  対象バケット '{bucket_name}' が見つかりません",
                extra={
                    "operation": "gcp_debug",
                    "status": "bucket_not_found",
                    "bucket_name": bucket_name,
                },
            )
            logger.warning("   ヒント: バケット名の設定を確認してください")
            logger.info("=" * 80)
            return False

    except gcp_exceptions.Forbidden as e:
        logger.error(
            f"🛑 バケット '{bucket_name}' の存在確認で権限不足 (403 Forbidden)",
            extra={
                "operation": "gcp_debug",
                "status": "permission_denied",
                "resource": f"bucket:{bucket_name}",
                "error": str(e),
                "error_type": "Forbidden",
            },
        )
        logger.error(f"   エラー詳細: {e}")
        logger.error("   ヒント:")
        logger.error(
            f"   - サービスアカウントにバケット '{bucket_name}' へのアクセス権限がありません"
        )
        logger.info("=" * 80)
        return False
    except gcp_exceptions.NotFound as e:
        logger.error(
            f"🛑 バケット '{bucket_name}' が存在しません (404 NotFound)",
            extra={
                "operation": "gcp_debug",
                "status": "not_found",
                "resource": f"bucket:{bucket_name}",
                "error": str(e),
                "error_type": "NotFound",
            },
        )
        logger.error(f"   エラー詳細: {e}")
        logger.error("   ヒント: バケット名が正しいか確認してください")
        logger.info("=" * 80)
        return False
    except Exception as e:
        logger.error(
            f"🔴 バケット存在確認中にエラー: {type(e).__name__}",
            extra={
                "operation": "gcp_debug",
                "status": "bucket_check_error",
                "bucket_name": bucket_name,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        logger.info("=" * 80)
        return False

    # ステップ4: オブジェクトプレフィックスの確認（オプション）
    if object_prefix:
        logger.info(
            f"📄 ステップ4: オブジェクトプレフィックス '{object_prefix}' の確認"
        )
        try:
            blobs = list(bucket.list_blobs(prefix=object_prefix, max_results=1))
            if blobs:
                logger.info(
                    f"✅ プレフィックス '{object_prefix}' 配下にオブジェクトが存在します"
                )
                logger.info(f"   - 最初のオブジェクト例: {blobs[0].name}")
            else:
                logger.warning(
                    f"⚠️  プレフィックス '{object_prefix}' 配下にオブジェクトが見つかりません",
                    extra={
                        "operation": "gcp_debug",
                        "status": "no_objects_found",
                        "bucket_name": bucket_name,
                        "prefix": object_prefix,
                    },
                )
                logger.warning("   ヒント: データが未アップロードの可能性があります")

        except gcp_exceptions.Forbidden as e:
            logger.error(
                "🛑 オブジェクト一覧取得で権限不足 (403 Forbidden)",
                extra={
                    "operation": "gcp_debug",
                    "status": "permission_denied",
                    "resource": f"bucket:{bucket_name}/prefix:{object_prefix}",
                    "error": str(e),
                    "error_type": "Forbidden",
                },
            )
            logger.error(f"   エラー詳細: {e}")
            logger.info("=" * 80)
            return False
        except Exception as e:
            logger.error(
                f"🔴 オブジェクト一覧取得中にエラー: {type(e).__name__}",
                extra={
                    "operation": "gcp_debug",
                    "status": "list_objects_error",
                    "bucket_name": bucket_name,
                    "prefix": object_prefix,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            logger.info("=" * 80)
            return False

    # すべてのチェック成功
    logger.info("=" * 80)
    logger.info("✅ GCP認証 + Cloud Storage権限はすべて正常です")
    logger.info("=" * 80)
    return True


__all__ = ["debug_log_gcp_adc_and_permissions"]
