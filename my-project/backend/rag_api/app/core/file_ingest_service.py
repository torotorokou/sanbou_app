

# データファイルのロードやカテゴリ抽出など、ファイル入出力関連のサービス群。
"""
データファイルのロードやカテゴリ抽出など、ファイル入出力関連のサービス群。
"""

import os
import json
import yaml
from typing import Dict, Tuple, List
from app.utils.file_utils import PDF_PATH, JSON_PATH, FAISS_PATH, ENV_PATH, YAML_PATH


def get_resource_paths() -> Dict[str, str]:
    """
    各種リソースファイルのパスをまとめて返す。
    新しいリソース種別追加時はこの辞書に追記するだけで拡張可能。

    Returns:
        dict: 各種ファイルパス
    """
    return {
        "PDF_PATH": PDF_PATH,
        "JSON_PATH": JSON_PATH,
        "FAISS_PATH": FAISS_PATH,
        "ENV_PATH": ENV_PATH,
        "YAML_PATH": YAML_PATH,
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
        raise FileNotFoundError(f"JSONファイルが見つかりません: {json_path}")
    try:
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"JSONファイルの読み込みに失敗: {json_path} ({e})")


from typing import List, Dict

def load_question_templates() -> List[Dict]:
    """
    質問テンプレート（YAML）を読み込み、必ずList[Dict]で返す。

    Returns:
        List[Dict]: テンプレートデータ
    """
    yaml_path = get_resource_paths().get("YAML_PATH")
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
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