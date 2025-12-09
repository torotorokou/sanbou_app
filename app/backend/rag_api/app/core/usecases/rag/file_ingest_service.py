

# データファイルのロードやカテゴリ抽出など、ファイル入出力関連のサービス群。
"""
データファイルのロードやカテゴリ抽出など、ファイル入出力関連のサービス群。
"""

import os
from pathlib import Path
import json
import yaml
from typing import Dict, Tuple, List
from app.shared.file_utils import PDF_PATH, JSON_PATH, FAISS_PATH, ENV_PATH, YAML_PATH
from backend_shared.core.domain.exceptions import InfrastructureError, NotFoundError


def get_resource_paths() -> Dict[str, str]:
    """
    各種リソースファイルのパスをまとめて返す。
    新しいリソース種別追加時はこの辞書に追記するだけで拡張可能。

    Returns:
        dict: 各種ファイルパス
    """
    return {
        "PDF_PATH": str(PDF_PATH),
        "JSON_PATH": str(JSON_PATH),
        "FAISS_PATH": str(FAISS_PATH),
        "ENV_PATH": str(ENV_PATH),
        "YAML_PATH": str(YAML_PATH),
        # 追加リソースはここに追記
    }



def load_json_data(json_path: str) -> Dict:
    """
    JSONファイルを読み込んで辞書として返す。
    ファイル存在チェック・例外処理付き。

    Args:
        json_path (str or Path): JSONファイルのパス

    Returns:
        dict: パース済みJSONデータ
    """
    if not json_path or not os.path.exists(json_path):
        raise NotFoundError("JSON file", json_path)
    try:
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise InfrastructureError(f"JSONファイルの読み込みに失敗: {json_path}", cause=e)


def load_question_templates() -> List[Dict]:
    """
    質問テンプレート（YAML）を読み込み、必ず List[Dict] で返す。

    優先パス:
      1. 環境変数・paths 由来の YAML_PATH
      2. /backend/config/category_question_templates_with_tags.yaml
      3. /backend/local_data/master/category_question_templates_with_tags.yaml

    いずれも存在しない/読み込み不可の場合は空配列 [] を返却する。

    Returns:
        List[Dict]: テンプレートデータ
    """
    # 候補パスを順に確認
    primary = str(get_resource_paths().get("YAML_PATH")) if get_resource_paths().get("YAML_PATH") else None
    fallbacks = [
        "/backend/config/category_question_templates_with_tags.yaml",
        "/backend/local_data/master/category_question_templates_with_tags.yaml",
    ]

    # 親ディレクトリを遡って repo 直下の config/ を探索（ローカル実行の救済）
    try:
        here = Path(__file__).resolve()
        for parent in list(here.parents)[:6]:
            for name in (
                "category_question_templates_with_tags.yaml",
                "category_question_templates.yaml",
            ):
                p = parent / ".." / ".." / ".." / ".." / ".."  # 安全のため更に遡る
                # 上記は固定ではないので、実際には parent 直下から順に確認
            # 正しくは parent 直下
        for parent in list(here.parents)[:6]:
            for rel in (
                Path("config/category_question_templates_with_tags.yaml"),
                Path("config/category_question_templates.yaml"),
            ):
                fp = (parent / rel).resolve()
                if fp.exists():
                    fallbacks.append(str(fp))
    except Exception:
        pass

    candidates: List[str] = []
    if primary:
        candidates.append(primary)
    candidates.extend(fallbacks)

    for p in candidates:
        try:
            if p and os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict):
                    return [data]
                if isinstance(data, list):
                    return data
        except Exception:
            # ログは上位でまとめて扱う方針のため握りつぶし、次候補へ
            continue

    # どれも見つからない/不正な場合は空で返す（500を避ける）
    return []


def extract_categories_and_titles(data: List[Dict]) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    データからカテゴリとタイトルを抽出する。

    Args:
        data (list): データリスト

    Returns:
        tuple: (カテゴリリスト, サブカテゴリ辞書)
    """
    categories = set()
    subcategories = {}
    for section in data:
        cats = section.get("category", [])
        if isinstance(cats, str):
            cats = [cats]
        for cat in cats:
            categories.add(cat)
            subcategories.setdefault(cat, set()).add(section.get("title"))
    categories = sorted(categories)
    for k in subcategories:
        subcategories[k] = sorted(subcategories[k])
    return categories, subcategories

def group_templates_by_category_and_tags(data: List[Dict]) -> Dict[str, Dict[Tuple[str, ...], List[str]]]:
    """
    テンプレートをカテゴリ・タグごとにグループ化する。

    Args:
        data (list): テンプレートデータ

    Returns:
        dict: グループ化されたテンプレート
    """
    def flatten_tags(tags) -> Tuple[str, ...]:
        """
        ネストしたリストやタプルを再帰的にフラットなタプルに変換
        """
        if isinstance(tags, (list, tuple)):
            result = []
            for t in tags:
                result.extend(flatten_tags(t))
            return tuple(result)
        elif tags is None:
            return tuple()
        else:
            return (str(tags),)

    grouped = {}
    for section in data:
        category = section.get("category")
        tags_raw = section.get("tags", [])
        tags = flatten_tags(tags_raw)
        title = section.get("title")
        grouped.setdefault(category, {}).setdefault(tags, []).append(title)
    return grouped