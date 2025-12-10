"""
Environment Variable Validator - 環境変数の検証とセキュリティチェック

【概要】
全サービスで必須となる環境変数を厳密に検証し、
起動時にエラーを早期検出します。

【主な機能】
1. 必須環境変数の存在チェック
2. パスワード強度の検証
3. URL形式の検証
4. 環境別（dev/stg/prod）の設定検証

【セキュリティ強化】
- パスワードの最小長（12文字以上）
- 本番環境でのデバッグモード禁止
- AUTH_MODEの環境整合性チェック

【使用例】
```python
from backend_shared.config.env_validator import validate_environment

# アプリ起動時に実行
try:
    validate_environment()
except ValueError as e:
    logger.error(f"Environment validation failed: {e}")
    sys.exit(1)
```
"""

import os
import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """データベース接続設定"""
    
    POSTGRES_HOST: str = Field(..., min_length=1)
    POSTGRES_PORT: int = Field(default=5432, ge=1, le=65535)
    POSTGRES_USER: str = Field(..., min_length=1)
    POSTGRES_PASSWORD: str = Field(..., min_length=12)  # 最低12文字
    POSTGRES_DB: str = Field(..., min_length=1)
    
    @field_validator("POSTGRES_PASSWORD")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """パスワード強度の検証"""
        if len(v) < 12:
            raise ValueError("POSTGRES_PASSWORD must be at least 12 characters")
        
        # 本番環境では追加の強度チェック
        stage = os.getenv("APP_ENV", "dev")
        if stage in ["prod", "vm_prod"]:
            has_upper = any(c.isupper() for c in v)
            has_lower = any(c.islower() for c in v)
            has_digit = any(c.isdigit() for c in v)
            
            if not (has_upper and has_lower and has_digit):
                raise ValueError(
                    "POSTGRES_PASSWORD for production must contain "
                    "uppercase, lowercase, and digits"
                )
        
        return v
    
    @property
    def database_url(self) -> str:
        """DATABASE_URLを生成"""
        from urllib.parse import quote_plus
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql://{self.POSTGRES_USER}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


class AppEnvironmentConfig(BaseSettings):
    """アプリケーション環境設定"""
    
    APP_ENV: Literal["local_dev", "local_demo", "vm_stg", "vm_prod"] = "local_dev"
    AUTH_MODE: Literal["dev_bypass", "vpn_dummy", "iap"] = "dev_bypass"
    DEBUG: bool = True
    
    @model_validator(mode="after")
    def validate_environment_consistency(self):
        """環境設定の整合性チェック"""
        
        # 本番環境でのデバッグモード禁止
        if self.APP_ENV in ["vm_prod"] and self.DEBUG:
            raise ValueError("DEBUG must be False in production (vm_prod)")
        
        # 環境とAUTH_MODEの整合性
        env_auth_mapping = {
            "local_dev": ["dev_bypass"],
            "local_demo": ["dev_bypass", "vpn_dummy"],
            "vm_stg": ["vpn_dummy"],
            "vm_prod": ["iap"],
        }
        
        allowed_modes = env_auth_mapping.get(self.APP_ENV, [])
        if self.AUTH_MODE not in allowed_modes:
            raise ValueError(
                f"AUTH_MODE '{self.AUTH_MODE}' is not allowed for "
                f"APP_ENV '{self.APP_ENV}'. Allowed: {allowed_modes}"
            )
        
        return self
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class ServiceEndpointsConfig(BaseModel):
    """サービスエンドポイント設定"""
    
    RAG_API_BASE: str = Field(default="http://rag_api:8000")
    LEDGER_API_BASE: str = Field(default="http://ledger_api:8000")
    MANUAL_API_BASE: str = Field(default="http://manual_api:8000")
    AI_API_BASE: str = Field(default="http://ai_api:8000")
    
    @field_validator("RAG_API_BASE", "LEDGER_API_BASE", "MANUAL_API_BASE", "AI_API_BASE")
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        """URL形式の検証"""
        pattern = r"^https?://[a-zA-Z0-9._-]+(:[0-9]{1,5})?(/.*)?$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid URL format: {v}")
        return v


def validate_environment() -> dict:
    """
    環境変数を検証し、設定辞書を返す
    
    Returns:
        dict: 検証済みの設定辞書
    
    Raises:
        ValueError: 環境変数が不正な場合
        
    Examples:
        >>> config = validate_environment()
        >>> print(config["database"]["database_url"])
        postgresql://user:password@localhost:5432/db
    """
    
    # データベース設定の検証
    db_config = DatabaseConfig(
        POSTGRES_HOST=os.getenv("POSTGRES_HOST", "db"),
        POSTGRES_PORT=int(os.getenv("POSTGRES_PORT", "5432")),
        POSTGRES_USER=os.getenv("POSTGRES_USER", ""),
        POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD", ""),
        POSTGRES_DB=os.getenv("POSTGRES_DB", ""),
    )
    
    # アプリ環境設定の検証
    app_config = AppEnvironmentConfig()
    
    # サービスエンドポイント設定の検証
    endpoints_config = ServiceEndpointsConfig(
        RAG_API_BASE=os.getenv("RAG_API_BASE", "http://rag_api:8000"),
        LEDGER_API_BASE=os.getenv("LEDGER_API_BASE", "http://ledger_api:8000"),
        MANUAL_API_BASE=os.getenv("MANUAL_API_BASE", "http://manual_api:8000"),
        AI_API_BASE=os.getenv("AI_API_BASE", "http://ai_api:8000"),
    )
    
    return {
        "database": db_config.model_dump(),
        "app": app_config.model_dump(),
        "endpoints": endpoints_config.model_dump(),
    }


def validate_environment_or_exit() -> dict:
    """
    環境変数を検証し、失敗時はエラーログを出力してプロセスを終了
    
    アプリ起動時に使用することを想定。
    
    Returns:
        dict: 検証済みの設定辞書
    """
    import sys
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        config = validate_environment()
        logger.info("✅ Environment validation passed")
        return config
    except ValueError as e:
        logger.error(f"❌ Environment validation failed: {e}")
        logger.error("Please check your .env files and secrets configuration")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during environment validation: {e}")
        sys.exit(1)
