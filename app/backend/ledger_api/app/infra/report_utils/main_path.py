from pathlib import Path
import yaml
import os
from typing import Optional, Union

# 設定ファイルのパスをapp/local_configに変更
MAIN_PATHS = "/backend/app/local_config/main_paths.yaml"
BASE_DIR_PATH = "/backend/app"


class MainPath:
    def __init__(self, config_path: str = MAIN_PATHS):
        self.base_dir = BaseDirProvider().get_base_dir()
        config_dict = YamlLoader(self.base_dir).load(config_path)
        self.resolver = MainPathResolver(config_dict, self.base_dir)

    def get_path(
        self, keys: Union[str, list[str]], section: Optional[str] = None
    ) -> Path:
        return self.resolver.get_path(keys, section)

    def get_config(self) -> dict:
        return self.resolver.config_data


class BaseDirProvider:
    def __init__(self, default_path: str = BASE_DIR_PATH):
        # 環境変数名もBASE_APP_DIRに変更
        self.base_dir = Path(os.getenv("BASE_APP_DIR", default_path))

    def get_base_dir(self) -> Path:
        return self.base_dir


class YamlLoader:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def load(self, relative_path: str) -> dict:
        full_path = self.base_dir / relative_path
        with open(full_path, encoding="utf-8") as f:
            return yaml.safe_load(f)


class MainPathResolver:
    def __init__(self, config_data: dict, base_dir: Path):
        self.config_data = config_data
        self.base_dir = base_dir

    def get_path(
        self, keys: Union[str, list[str]], section: Optional[str] = None
    ) -> Path:
        target = self.config_data
        if section:
            target = target.get(section, {})
            if target is None:
                raise KeyError(f"セクション '{section}' が見つかりません")

        if isinstance(keys, str):
            keys = [keys]

        for key in keys:
            target = target.get(key)
            if target is None:
                raise KeyError(f"キー '{'.'.join(keys)}' が見つかりません")

        if isinstance(target, (str, os.PathLike)):
            return self.base_dir / Path(target)
        # 予期せぬ型（dict など）が来た場合は明示的にエラー
        raise TypeError(
            f"無効なパス型: {type(target)!r} for key '{'.'.join(keys)}'. 値={target!r}"
        )
