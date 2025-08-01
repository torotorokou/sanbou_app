# データファイルのロードやカテゴリ抽出など、ファイル入出力関連のサービス群。
"""
データファイルのロードやカテゴリ抽出など、ファイル入出力関連のサービス群。
"""

import json
import yaml
from app.utils.file_utils import PDF_PATH, JSON_PATH, FAISS_PATH, ENV_PATH, YAML_PATH


def get_resource_paths() -> dict:
    """
    各種リソースファイルのパスをまとめて返す。

    Returns:
        dict: 各種ファイルパス
    """
    return {
        "PDF_PATH": PDF_PATH,
        "JSON_PATH": JSON_PATH,
        "FAISS_PATH": FAISS_PATH,
        "ENV_PATH": ENV_PATH,
        "YAML_PATH": YAML_PATH,
    }


def load_json_data(json_path):
    """
    JSONファイルを読み込んで辞書として返す。

    Args:
        json_path (str or Path): JSONファイルのパス

    Returns:
        dict: パース済みJSONデータ
    """
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def load_question_templates():
    """
    質問テンプレート（YAML）を読み込む。

    Returns:
        dict: テンプレートデータ
    """
    yaml_path = get_resource_paths().get("YAML_PATH")
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_categories_and_titles(data):
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

def group_templates_by_category_and_tags(data):
    """
    テンプレートをカテゴリ・タグごとにグループ化する。

    Args:
        data (list): テンプレートデータ

    Returns:
        dict: グループ化されたテンプレート
    """
    grouped = {}
    for section in data:
        category = section.get("category")
        tags = tuple(section.get("tags", []))
        title = section.get("title")
        grouped.setdefault(category, {}).setdefault(tags, []).append(title)
    return grouped