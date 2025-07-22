"""
CSVファイルの保存処理を行うモジュール。
初心者にも分かりやすいように日本語でコメント・ドックストリングを記載しています。
"""

# --- import ---
import os

from app.local_config.paths import SAVE_DIR_TEMP
# CSVProcessorは別の場所にあるようなので、必要に応じて適切なパスに修正
# from app.utils.csv_processor import CSVProcessor


# --- 保存処理 ---
class CSVUploadStorage:
    """
    CSVファイルの保存処理をまとめたクラス。
    一時保存ディレクトリへのファイル保存などを行います。
    """

    def save_to_temp(self, dfs: dict, file_inputs: dict, processor):
        """
        DataFrameを一時ディレクトリにCSVファイルとして保存します。
        :param dfs: ファイル名→DataFrameの辞書
        :param file_inputs: ファイル名→UploadFileの辞書
        :param processor: CSV処理結果を生成するプロセッサ
        :return: 保存結果の辞書
        """
        result = {}
        for name, df in dfs.items():
            file = file_inputs[name]
            filename = (
                file.filename or f"{name}.csv"
            )  # ファイル名が無い場合のフォールバック
            save_path = os.path.join(SAVE_DIR_TEMP, filename)
            # DataFrameをCSVファイルとして保存（UTF-8 BOM付き）
            df.to_csv(save_path, index=False, encoding="utf-8-sig")
            # 保存結果の情報を作成
            result[name] = processor.create_result(
                filename=filename,
                columns=df.columns.tolist(),
                status="success",
                code="SUCCESS",
                detail="アップロード成功",
            )
        return result
