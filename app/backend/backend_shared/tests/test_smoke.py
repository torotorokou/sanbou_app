"""
Smoke Tests for backend_shared package

パッケージの基本的なインポートと後方互換性を確認します。
"""


def test_import_package():
    """パッケージがインポート可能であることを確認"""
    import importlib

    m = importlib.import_module("backend_shared")
    assert m is not None
    assert hasattr(m, "__version__")


def test_new_paths_import():
    """新しいパス構造でインポート可能であることを確認"""
    # adapters
    from backend_shared import utils

    # infrastructure
    from backend_shared.config import config_loader
    from backend_shared.core.usecases.csv_formatter import formatter_config

    # usecases
    from backend_shared.core.usecases.csv_validator import validation_result
    from backend_shared.core.usecases.report_checker import check_csv_files

    # domain & utils
    from backend_shared.domain import contract
    from backend_shared.infra.adapters.fastapi import error_handlers
    from backend_shared.infra.adapters.middleware import request_id
    from backend_shared.infra.adapters.presentation import response_base
    from backend_shared.infra.frameworks.logging_utils import access_log

    assert response_base is not None
    assert request_id is not None
    assert error_handlers is not None
    assert validation_result is not None
    assert formatter_config is not None
    assert check_csv_files is not None
    assert config_loader is not None
    assert access_log is not None
    assert contract is not None
    assert utils is not None


def test_legacy_paths_compatibility():
    """旧パスとの後方互換性を確認"""
    # 旧パスでのインポートが動作すること
    from backend_shared.api import error_handlers
    from backend_shared.api_response import response_base
    from backend_shared.config import config_loader
    from backend_shared.csv_formatter import formatter_config
    from backend_shared.csv_validator import validation_result
    from backend_shared.logging_utils import access_log
    from backend_shared.middleware import request_id
    from backend_shared.report_checker import check_csv_files

    assert response_base is not None
    assert request_id is not None
    assert error_handlers is not None
    assert validation_result is not None
    assert formatter_config is not None
    assert check_csv_files is not None
    assert config_loader is not None
    assert access_log is not None


def test_module_structure():
    """パッケージ構造が正しいことを確認"""
    import os

    import backend_shared

    # src layout が正しく機能していることを確認
    pkg_path = backend_shared.__file__
    assert pkg_path is not None
    assert (
        "src/backend_shared" in pkg_path or "site-packages/backend_shared" in pkg_path
    )

    # パッケージのルートディレクトリを取得
    pkg_dir = os.path.dirname(pkg_path)

    # 主要なサブパッケージが存在することを確認
    expected_dirs = ["adapters", "usecases", "infrastructure", "domain", "utils"]
    for dirname in expected_dirs:
        dir_path = os.path.join(pkg_dir, dirname)
        assert os.path.isdir(dir_path), f"{dirname} directory should exist"
