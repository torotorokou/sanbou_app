"""
Tests for database URL builder functions.

This module tests the safe construction of PostgreSQL DSN strings,
especially with special characters in passwords.
"""

from __future__ import annotations
import pytest
from backend_shared.infra.db.url_builder import build_postgres_dsn


class TestBuildPostgresDsn:
    """Tests for build_postgres_dsn function"""
    
    def test_basic_dsn_construction(self):
        """基本的なDSN構築のテスト"""
        result = build_postgres_dsn(
            user="myuser",
            password="mypass",
            host="localhost",
            port=5432,
            database="mydb",
            driver="psycopg"
        )
        assert result == "postgresql+psycopg://myuser:mypass@localhost:5432/mydb"
    
    def test_password_with_slash(self):
        """パスワードに / を含む場合のテスト"""
        result = build_postgres_dsn(
            user="app_user",
            password="pass/word",
            host="db.example.com",
            port=5432,
            database="production",
            driver="psycopg"
        )
        # / は %2F にエンコードされる
        assert "pass%2Fword" in result
        assert result == "postgresql+psycopg://app_user:pass%2Fword@db.example.com:5432/production"
    
    def test_password_with_at_sign(self):
        """パスワードに @ を含む場合のテスト"""
        result = build_postgres_dsn(
            user="testuser",
            password="p@ssword",
            host="localhost",
            port=5432,
            database="testdb",
            driver="psycopg"
        )
        # @ は %40 にエンコードされる
        assert "p%40ssword" in result
        assert result == "postgresql+psycopg://testuser:p%40ssword@localhost:5432/testdb"
    
    def test_password_with_colon(self):
        """パスワードに : を含む場合のテスト"""
        result = build_postgres_dsn(
            user="admin",
            password="pass:word",
            host="db",
            port=5432,
            database="admindb",
            driver="psycopg"
        )
        # : は %3A にエンコードされる
        assert "pass%3Aword" in result
        assert result == "postgresql+psycopg://admin:pass%3Aword@db:5432/admindb"
    
    def test_password_with_multiple_special_chars(self):
        """パスワードに複数の特殊文字を含む場合のテスト"""
        result = build_postgres_dsn(
            user="complex_user",
            password="p@ss/w:rd#123",
            host="secure.db.com",
            port=5432,
            database="secure_db",
            driver="psycopg"
        )
        # すべての特殊文字が正しくエンコードされる
        assert "@" not in result.split("//")[1].split("@")[0]  # ユーザー情報部に生の @ がない
        assert "/" not in result.split("//")[1].split("@")[0].split(":")[1]  # パスワード部に生の / がない
        # エンコード結果を検証
        assert "p%40ss%2Fw%3Ard%23123" in result
    
    def test_username_with_special_chars(self):
        """ユーザー名に特殊文字を含む場合のテスト"""
        result = build_postgres_dsn(
            user="user@domain.com",
            password="simple",
            host="localhost",
            port=5432,
            database="mydb",
            driver="psycopg"
        )
        # ユーザー名の @ も正しくエンコードされる
        assert "user%40domain.com" in result
        assert result == "postgresql+psycopg://user%40domain.com:simple@localhost:5432/mydb"
    
    def test_different_drivers(self):
        """異なるドライバーでのテスト"""
        # psycopg
        result_psycopg = build_postgres_dsn(
            user="user",
            password="pass",
            host="localhost",
            port=5432,
            database="db",
            driver="psycopg"
        )
        assert result_psycopg.startswith("postgresql+psycopg://")
        
        # asyncpg
        result_asyncpg = build_postgres_dsn(
            user="user",
            password="pass",
            host="localhost",
            port=5432,
            database="db",
            driver="asyncpg"
        )
        assert result_asyncpg.startswith("postgresql+asyncpg://")
        
        # psycopg2
        result_psycopg2 = build_postgres_dsn(
            user="user",
            password="pass",
            host="localhost",
            port=5432,
            database="db",
            driver="psycopg2"
        )
        assert result_psycopg2.startswith("postgresql+psycopg2://")
    
    def test_port_as_string(self):
        """ポート番号を文字列で指定した場合のテスト"""
        result = build_postgres_dsn(
            user="user",
            password="pass",
            host="localhost",
            port="5433",  # 文字列
            database="db",
            driver="psycopg"
        )
        assert ":5433/" in result
        assert result == "postgresql+psycopg://user:pass@localhost:5433/db"
    
    def test_dsn_format(self):
        """DSNの形式が正しいことを確認"""
        result = build_postgres_dsn(
            user="testuser",
            password="testpass",
            host="testhost",
            port=5432,
            database="testdb",
            driver="psycopg"
        )
        # 形式: postgresql+<driver>://<user>:<password>@<host>:<port>/<database>
        assert result.startswith("postgresql+psycopg://")
        parts = result.split("://")[1].split("@")
        assert len(parts) == 2
        user_pass = parts[0].split(":")
        assert len(user_pass) == 2
        assert user_pass[0] == "testuser"
        assert user_pass[1] == "testpass"
        host_port_db = parts[1].split(":")
        assert len(host_port_db) == 2
        assert host_port_db[0] == "testhost"
        port_db = host_port_db[1].split("/")
        assert len(port_db) == 2
        assert port_db[0] == "5432"
        assert port_db[1] == "testdb"


class TestUrlEncodingSafety:
    """URLエンコードの安全性に関するテスト"""
    
    def test_real_world_complex_password(self):
        """実際にありそうな複雑なパスワードでのテスト"""
        # 実際のVMやK8s環境で生成されるような複雑なパスワード
        complex_passwords = [
            "Abc123!@#$%^&*()",
            "p@ss/w:rd#2024",
            "My$ecur3/P@ssw0rd:)",
            "T3st!ng#2024/12@05",
        ]
        
        for password in complex_passwords:
            result = build_postgres_dsn(
                user="testuser",
                password=password,
                host="localhost",
                port=5432,
                database="testdb",
                driver="psycopg"
            )
            # DSNは正しい形式である
            assert result.startswith("postgresql+psycopg://")
            # 生の特殊文字が残っていない（パスワード部分）
            encoded_part = result.split("://")[1].split("@")[0]
            # @, /, : などがエンコードされている（ただしuser:passの:は残る）
            if "@" in password:
                assert "@" not in encoded_part.split(":")[1]
            if "/" in password:
                assert "/" not in encoded_part.split(":")[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
