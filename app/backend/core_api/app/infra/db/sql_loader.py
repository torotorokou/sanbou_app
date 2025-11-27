"""
SQL File Loader

SQLファイルを読み込むユーティリティ。
複雑なSQLをPythonコードから分離し、保守性を向上させる。

使用例:
    from app.infra.db.sql_loader import load_sql
    from sqlalchemy import text
    
    sql_str = load_sql("dashboard/dashboard_target_repo__get_by_date_optimized.sql")
    query = text(sql_str)
"""
from pathlib import Path

# SQLファイルの基準ディレクトリ
BASE_SQL_DIR = Path(__file__).parent / "sql"


def load_sql(path: str) -> str:
    """
    相対パスで.sqlファイルを読み込む
    
    Args:
        path: BASE_SQL_DIRからの相対パス
              例: "dashboard/dashboard_target_repo__get_by_date_optimized.sql"
    
    Returns:
        str: SQLファイルの内容
        
    Raises:
        FileNotFoundError: 指定されたSQLファイルが存在しない場合
        
    Note:
        - ファイルはUTF-8エンコーディングで読み込まれる
        - パスの区切り文字は "/" を使用（Windows/Linux両対応）
    """
    full_path = BASE_SQL_DIR / path
    
    if not full_path.exists():
        raise FileNotFoundError(
            f"SQL file not found: {full_path}\n"
            f"Expected path: {path}"
        )
    
    return full_path.read_text(encoding="utf-8")
