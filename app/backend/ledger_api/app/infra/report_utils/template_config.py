import pandas as pd
import yaml
from backend_shared.config.config_loader import (
    ReportTemplateConfigLoader,
    ShogunCsvConfigLoader,
)
from backend_shared.utils.dataframe_utils import clean_na_strings

from .main_path import MainPath


def resolve_dtype(dtype_str: str):
    """型文字列をpandas dtypeに変換する"""
    dtype_map = {
        "str": str,
        "int": "Int64",
        "float": float,
        "datetime": "datetime64[ns]",
        "object": object,
    }
    return dtype_map.get(dtype_str, object)


def get_path_from_yaml(key: str | list[str], section: str | None = None) -> str:
    mainpath = MainPath()
    path = mainpath.get_path(key, section)
    return str(path)


def load_yaml(key_or_path: str, section: str | None = None) -> dict:
    """
    YAMLファイルを辞書形式で読み込む。

    Parameters:
        key_or_path (str): 相対パスまたはmain_paths.yamlのキー名
        section (str, optional): キーが格納されているmain_paths.yamlのセクション名（例: 'config_files'）

    Returns:
        dict: YAMLから読み込まれた辞書データ
    """
    mainpath = MainPath()
    path = mainpath.get_path(key_or_path, section)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_expected_dtypes() -> dict:
    """
    全テンプレートの型定義を取得

    ShogunCsvConfigLoaderを使用してshogun_csv_masters.yamlから
    型情報を取得します。

    Returns:
        dict: テンプレートごと、CSV種別ごとの型定義
    """
    return get_expected_dtypes_from_shogun()


def get_template_config() -> dict:
    """
    backend_sharedのReportTemplateConfigLoaderを使用してテンプレート設定を読み込む

    Returns:
        dict: 全ての帳票設定の辞書
    """
    loader = ReportTemplateConfigLoader()
    return loader.get_all_config()


def get_unit_price_table_csv() -> pd.DataFrame:
    """
    単価表CSVを読み込んでDataFrameとして返す。
    """
    mainpath = MainPath()
    csv_path = mainpath.get_path("unit_price_table", section="csv")

    # <NA>文字列をfloat変換エラーから守るため、na_valuesを指定
    na_values = ["<NA>", "NaN", "nan", "None", "NULL", "null", "#N/A", "#NA"]
    df = pd.read_csv(
        csv_path, encoding="utf-8-sig", na_values=na_values, keep_default_na=False
    )

    # 全カラムに対してNA文字列をクリーンアップ
    for col in df.columns:
        df[col] = df[col].apply(clean_na_strings)

    return df


def get_required_files_map() -> dict:
    """
    各テンプレートに必要なファイル（required_files）を辞書形式で取得。

    Returns:
        dict: テンプレートキー → 必須ファイルリスト
    """
    config = get_template_config()
    return {key: value.get("required_files", []) for key, value in config.items()}


def get_file_keys_map() -> dict:
    """
    各テンプレートに必要・任意ファイルを辞書形式で取得。

    Returns:
        dict: テンプレートキー → {'required': [...], 'optional': [...]}
    """
    config = get_template_config()
    return {
        key: {
            "required": value.get("required_files", []),
            "optional": value.get("optional_files", []),
        }
        for key, value in config.items()
    }


def get_template_descriptions() -> dict:
    config = get_template_config()
    return {key: value.get("description", []) for key, value in config.items()}


def get_template_dict() -> dict:
    """
    テンプレートの表示ラベル → テンプレートキー の辞書を返す。

    Returns:
        dict: 例 {"工場日報": "factory_report", ...}
    """
    config = get_template_config()
    return {value["label"]: key for key, value in config.items()}


def get_expected_dtypes_by_template(template_key: str) -> dict:
    """
    指定されたテンプレートキーに対応するCSVファイルごとの
    カラム型定義（expected_dtypes）を返す。

    この関数は expected_dtypes.yaml を読み込んだ結果から、
    指定テンプレートに対応する型定義だけを抽出して返します。

    Parameters:
        template_key (str): テンプレート名（例: "average_sheet", "factory_report"）

    Returns:
        dict: ファイルキーごとのカラム名と型の辞書。
              例:
              {
                  "receive": {
                      "金額": float,
                      "正味重量": int,
                      "伝票日付": "datetime64[ns]"
                  },
                  "yard": {
                      "品名": str,
                      ...
                  }
              }
              対応テンプレートが存在しない場合は空の辞書を返します。
    """
    config = get_expected_dtypes()
    return config.get(template_key, {})


def get_required_columns_definition(template_name: str) -> dict:
    """
    テンプレートに必要なカラムを取得

    ShogunCsvConfigLoaderを使用してshogun_csv_masters.yamlから
    カラム情報を取得します。

    Args:
        template_name (str): テンプレート名（factory_report, balance_sheetなど）

    Returns:
        dict: CSV種別ごとの日本語カラム名リスト
              例: {'shipment': ['伝票日付', '品名', ...], 'yard': [...]}
    """
    return get_required_columns_from_shogun(template_name)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 新実装: ShogunCsvConfigLoaderを使用（YAML削除後に有効化）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def get_required_columns_from_shogun(template_name: str) -> dict:
    """
    ShogunCsvConfigLoaderを使用して、テンプレートに必要なカラムを取得

    shogun_csv_masters.yamlからカラム情報を取得するため、
    required_columns_definition.yamlは不要になります。

    Args:
        template_name (str): テンプレート名（factory_report, balance_sheetなど）

    Returns:
        dict: CSV種別ごとの日本語カラム名リスト
              例: {'shipment': ['伝票日付', '品名', ...], 'yard': [...]}
    """
    # テンプレート設定から必要なCSV種別を取得
    template_config = get_template_config().get(template_name, {})
    required_files = template_config.get("required_files", [])
    optional_files = template_config.get("optional_files", [])
    all_files = required_files + optional_files

    # ShogunCsvConfigLoaderを使用して全カラムを取得
    loader = ShogunCsvConfigLoader()
    result = {}

    for csv_type in all_files:
        # 全カラムの日本語名を取得
        columns = loader.get_columns(csv_type)
        result[csv_type] = list(columns.keys())

    return result


def get_expected_dtypes_from_shogun() -> dict:
    """
    ShogunCsvConfigLoaderを使用して、全テンプレートの型定義を取得

    shogun_csv_masters.yamlから型情報を取得するため、
    expected_import_csv_dtypes.yamlは不要になります。

    Returns:
        dict: テンプレートごと、CSV種別ごとの型定義
              例: {
                  'factory_report': {
                      'shipment': {'伝票日付': 'datetime64[ns]', '品名': str, ...}
                  }
              }
    """
    loader = ShogunCsvConfigLoader()
    all_templates = get_template_config()
    result = {}

    for template_name, template_config in all_templates.items():
        required_files = template_config.get("required_files", [])
        optional_files = template_config.get("optional_files", [])
        all_files = required_files + optional_files

        result[template_name] = {}

        for csv_type in all_files:
            # ShogunCsvConfigLoaderから型マップを取得
            type_map = loader.get_type_map(csv_type)
            # 型文字列をpandas dtypeに変換
            result[template_name][csv_type] = {
                col: resolve_dtype(dtype_str) for col, dtype_str in type_map.items()
            }

    return result
