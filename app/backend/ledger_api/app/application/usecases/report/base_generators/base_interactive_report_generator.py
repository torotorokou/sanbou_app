"""Interactive report generator base classes.

インタラクティブ帳票生成の共通基底クラス。

目的:
 1. 既存の `BaseReportGenerator` の validate / format / Excel 生成ロジックを再利用
 2. main_process を複数ステップ (initial -> N 回の apply -> finalize) に分割
 3. セッション状態をシリアライズ/デシリアライズする仕組みを提供

各ステップ概要:
 initial_step(df_formatted) -> (state_dict, payload_dict)
   - フロント初回呼び出しで実行。ユーザー入力前の前処理と選択肢生成など。

 apply_step(state_dict, user_input_dict) -> (updated_state, payload_dict)
   - 中間ステップ。ユーザー選択を逐次反映し、確認用データを返す。

 finalize_step(state_dict) -> (final_result_df, payload_dict)
   - 最終 DataFrame を返す。payload_dict にはフロント表示用サマリーなど任意情報。

フロントとのデータ受け渡し方針:
 - state は JSON 化 (DataFrame は df.to_json()) して `session_data` として返却
 - 次ステップでは `session_data` を受け取り `deserialize_state` で復元
 - DataFrame の JSON orient はデフォルト (records でない) を使用し、対称性を確保

「保守性」観点の工夫:
 - 抽象メソッドのインターフェースを最小限にし、共通シリアライズ処理を集中
 - 将来ステップ追加時は apply_step を複数回呼ぶだけで拡張可能
 - 非インタラクティブ帳票との共存 (既存 ReportProcessingService.run) を壊さない
"""

from __future__ import annotations

from abc import abstractmethod
from io import StringIO
from typing import Any, Callable, Dict, Tuple

import pandas as pd

from app.application.usecases.report.base_generators.base_report_generator import (
    BaseReportGenerator,
)

SerializedState = Dict[str, Any]


class BaseInteractiveReportGenerator(BaseReportGenerator):
    """インタラクティブ帳票用基底クラス。

    既存 BaseReportGenerator を継承し、ステップ分割された処理インターフェースを追加。
    """

    # ------- 抽象ステップメソッド -------
    @abstractmethod
    def initial_step(
        self, df_formatted: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """初期ステップ。state, payload を返す。"""
        raise NotImplementedError

    def apply_step(
        self, state: Dict[str, Any], user_input: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """中間ステップ (汎用ディスパッチ)

        user_input から以下いずれかを読みステップハンドラを呼び出す:
          - action (推奨文字列)
          - step (数値 or 文字列)

        サブクラスは get_step_handlers() をオーバーライドして
        { "action_name": callable } を返す。callable は
          (state, user_input) -> (state, payload)
        を実装する。
        任意回数呼び出し可能で、最終確定は finalize_step で行う。
        """
        handlers = self.get_step_handlers()
        key = user_input.get("action")
        if key is None:
            step_val = user_input.get("step")
            if step_val is not None:
                key = str(step_val)
        if key is None:
            raise ValueError("ユーザー入力に 'action' も 'step' も存在しません。")
        handler = handlers.get(str(key))
        if handler is None:
            raise ValueError(f"未対応のステップ/アクション: {key}")
        return handler(state, user_input)

    # サブクラスで必要に応じてオーバーライド
    def get_step_handlers(
        self,
    ) -> Dict[
        str,
        Callable[
            [Dict[str, Any], Dict[str, Any]], Tuple[Dict[str, Any], Dict[str, Any]]
        ],
    ]:  # noqa: E501
        return {}

    @abstractmethod
    def finalize_step(
        self, state: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """最終ステップ。帳票最終 DataFrame と追加情報 payload を返す。"""
        raise NotImplementedError

    # ------- セッション状態シリアライズ支援 -------
    def serialize_state(self, state: Dict[str, Any]) -> SerializedState:
        serialized: Dict[str, Any] = {}
        for k, v in state.items():
            if isinstance(v, pd.DataFrame):
                serialized[k] = {"__df__": True, "value": v.to_json()}
            else:
                serialized[k] = v
        return serialized

    def deserialize_state(self, serialized: SerializedState) -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        for k, v in serialized.items():
            if isinstance(v, dict) and v.get("__df__") and "value" in v:
                value = v["value"]
                if not isinstance(value, str):
                    raise TypeError(
                        "DataFrame シリアライズ値は str である必要がありますが、"
                        f"{type(value)!r} が渡されました"
                    )
                state[k] = pd.read_json(StringIO(value))
            else:
                state[k] = v
        return state

    # main_process は未使用 (互換のため定義) ---------
    def main_process(self, df_formatted: Dict[str, Any]):  # type: ignore[override]
        """非インタラクティブ互換: finalize_step を直接呼ぶ場合のフォールバック。
        インタラクティブフローでは利用しない。"""
        final_df, _ = self.finalize_step({"df_formatted": df_formatted})
        return final_df
