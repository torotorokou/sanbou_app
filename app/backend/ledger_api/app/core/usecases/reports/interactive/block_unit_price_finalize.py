"""
Block Unit Price Interactive - Finalize Step Handler
最終処理を担当するモジュール
"""

from typing import Any, cast

import pandas as pd
from backend_shared.application.logging import create_log_context, get_module_logger

from app.core.domain.reports.processors.block_unit_price.process2 import (
    apply_transport_fee_by_vendor,
    apply_weight_based_transport_fee,
    df_cul_filtering,
    first_cell_in_template,
    make_sum_date,
    make_total_sum,
)
from app.infra.report_utils import (
    MainPath,
    get_template_config,
    load_master_and_template,
)
from app.infra.report_utils.domain import ReadTransportDiscount

from .block_unit_price_utils import (
    ensure_datetime_col,
    fmt_cols,
    fmt_head_rows,
    handle_step_error,
    log_checkpoint,
)

logger = get_module_logger(__name__)


# ------------------------------ Selection Merge ------------------------------


def merge_selected_transport_vendors_with_df(
    df_shipment: pd.DataFrame, selection_df: pd.DataFrame
) -> pd.DataFrame:
    """
    選択された運搬業者をDataFrameにマージ

    Args:
        df_shipment: 出荷データ
        selection_df: 選択データ

    Returns:
        マージ後のDataFrame
    """
    if selection_df is None or selection_df.empty:
        logger.warning("selection_df is None or empty, returning original df_shipment")
        return df_shipment.copy()

    df_after = df_shipment.copy()

    # entry_idが存在しない場合は警告
    if "entry_id" not in df_after.columns:
        logger.error("df_shipment に 'entry_id' 列が存在しません")
        return df_after

    # entry_idを文字列型に統一
    df_after["entry_id"] = df_after["entry_id"].astype(str)

    sel = selection_df.copy()
    sel["entry_id"] = sel["entry_id"].astype(str)

    logger.info(
        "=== MERGE DEBUG START ===",
        extra=create_log_context(
            operation="merge_transport_vendors",
            df_shipment_shape=df_shipment.shape,
            df_shipment_entry_id_sample=(
                df_shipment["entry_id"].head(3).tolist()
                if "entry_id" in df_shipment.columns
                else []
            ),
            selection_df_shape=selection_df.shape,
            selection_df_columns=list(selection_df.columns),
            selection_df_head=(
                selection_df.head(3).to_dict() if not selection_df.empty else {}
            ),
        ),
    )

    # ベンダ名カラムの候補
    vendor_label_candidates = [
        "selected_vendor",
        "vendor_label",
        "運搬業者",
        "label",
        "option",
        "selected",
    ]
    label_col = next((c for c in vendor_label_candidates if c in sel.columns), None)
    if not label_col:
        logger.error(
            f"selection_df にベンダ名の列が見つかりません。columns={list(sel.columns)}"
        )
        raise ValueError(
            "selection_df にベンダ名の列が見つかりません"
            "（例: selected_vendor, vendor_label, 運搬業者 など）"
        )

    sel = sel[["entry_id", label_col]].dropna(subset=["entry_id"])
    sel = sel.drop_duplicates(subset=["entry_id"], keep="last")

    logger.debug(
        f"Preparing to merge with {len(sel)} selection entries",
        extra=create_log_context(
            operation="merge_transport_vendors",
            label_col=label_col,
            sel_entry_ids=sel["entry_id"].tolist()[:5],
        ),
    )

    # マージ処理
    merged = df_after.merge(
        sel.rename(columns={label_col: "__selected_vendor"}),
        on="entry_id",
        how="left",
        indicator=True,
    )

    # マージ結果の統計
    merge_stats = merged["_merge"].value_counts().to_dict()
    logger.info(
        f"Merge statistics: {merge_stats}",
        extra=create_log_context(
            operation="merge_transport_vendors",
            both=merge_stats.get("both", 0),
            left_only=merge_stats.get("left_only", 0),
            right_only=merge_stats.get("right_only", 0),
        ),
    )

    merged.drop(columns=["_merge"], inplace=True)

    if "運搬業者" not in merged.columns:
        merged["運搬業者"] = None

    # 選択された運搬業者をログ出力
    selected_count = merged["__selected_vendor"].notna().sum()
    logger.debug(
        f"Selected vendors count: {selected_count}",
        extra=create_log_context(
            operation="merge_transport_vendors",
            selected_vendors=merged["__selected_vendor"]
            .dropna()
            .unique()
            .tolist()[:10],
        ),
    )

    # 運搬業者の更新（選択がある場合は優先）
    merged["運搬業者"] = merged["__selected_vendor"].fillna(merged["運搬業者"])
    merged.drop(columns=["__selected_vendor"], inplace=True)

    # 最終結果のログ
    final_vendor_counts = merged["運搬業者"].value_counts().to_dict()
    logger.info(
        f"=== MERGE DEBUG END === Vendor distribution: {final_vendor_counts}",
        extra=create_log_context(
            operation="merge_transport_vendors",
            after_cols=list(merged.columns),
            applied_count=int(merged["運搬業者"].notna().sum()),
            vendor_distribution=final_vendor_counts,
            total_rows=len(merged),
        ),
    )

    return merged


def merge_selected_transport_vendors_copy(
    df_shipment: pd.DataFrame, state: dict[str, Any]
) -> pd.DataFrame:
    """
    選択辞書を使って運搬業者をマージ（コピー版）

    Args:
        df_shipment: 出荷データ
        state: 状態辞書

    Returns:
        マージ後のDataFrame
    """
    selections = state.get("selections") or {}
    if not selections:
        logger.warning("merge_copy: selections is empty, returning df_shipment copy")
        return df_shipment.copy()

    df_after = df_shipment.copy()
    if "entry_id" not in df_after.columns:
        logger.error("merge_copy: 'entry_id' 列が無いため selections を適用できません")
        return df_after

    # entry_idを文字列型に統一
    df_after["entry_id"] = df_after["entry_id"].astype(str)

    logger.info(
        "=== MERGE_COPY DEBUG START ===",
        extra=create_log_context(
            operation="merge_transport_vendors_copy",
            df_after_shape=df_after.shape,
            selections_count=len(selections),
            df_after_entry_id_sample=df_after["entry_id"].head(3).tolist(),
            selections_keys_sample=list(selections.keys())[:5],
        ),
    )

    applied = 0
    not_found = []
    vendor_counts = {}

    for entry_id, vendor_label in selections.items():
        try:
            # entry_idを文字列型に統一
            entry_id_str = str(entry_id)
            mask = df_after["entry_id"] == entry_id_str
            matched_count = int(mask.sum())

            if matched_count == 0:
                not_found.append(entry_id_str)
                continue

            df_after.loc[mask, "運搬業者"] = str(vendor_label)
            applied += matched_count

            # ベンダー分布をカウント
            vendor_counts[str(vendor_label)] = (
                vendor_counts.get(str(vendor_label), 0) + matched_count
            )

        except Exception as e:
            logger.warning(
                f"merge_copy: apply failed for {entry_id}: {type(e).__name__}: {e}"
            )
            continue

    # マッチしなかったentry_idをログ出力
    if not_found:
        logger.warning(
            f"merge_copy: {len(not_found)} entry_ids did not match in df_after",
            extra=create_log_context(
                operation="merge_transport_vendors_copy",
                not_found_count=len(not_found),
                not_found_entry_ids=not_found[:10],
            ),
        )

    logger.info(
        f"=== MERGE_COPY DEBUG END === Applied: {applied}, Vendor distribution: {vendor_counts}",
        extra=create_log_context(
            operation="merge_transport_vendors_copy",
            applied_rows=applied,
            notna_count=int(df_after["運搬業者"].notna().sum()),
            vendor_distribution=vendor_counts,
            total_rows=len(df_after),
            not_found_count=len(not_found),
        ),
    )

    return df_after


# ------------------------------ Pipeline Processing ------------------------------


def run_block_unit_price_pipeline(
    df_shipment: pd.DataFrame, df_transport_cost: pd.DataFrame, master_csv: pd.DataFrame
) -> pd.DataFrame:
    """
    ブロック単価計算パイプラインを実行

    Args:
        df_shipment: 出荷データ
        df_transport_cost: 運搬費用データ
        master_csv: マスターCSV

    Returns:
        処理後のDataFrame
    """
    df_after = df_shipment.copy()

    log_checkpoint("pipeline_start", df_after, df_transport_cost)
    logger.debug(
        f"PIPELINE START: df={fmt_cols(df_after)} | "
        f"transport={fmt_cols(df_transport_cost)} | "
        f"master={fmt_cols(master_csv)}"
    )

    # 左DFの '運搬費' を退避（マージ時の衝突回避）
    if "運搬費" in df_after.columns:
        df_after = df_after.rename(columns={"運搬費": "__old_transport_fee"})
        logger.debug(
            "pipeline note: 左DFの '運搬費' を '__old_transport_fee' に退避しました"
            "（マージ時の衝突回避）"
        )

    # パイプライン処理
    df_after = apply_transport_fee_by_vendor(df_after, df_transport_cost)
    log_checkpoint("after_apply_transport_fee_by_vendor", df_after, df_transport_cost)
    logger.debug(
        "運搬費(業者別)適用後",
        extra=create_log_context(
            operation="finalize_block_unit_price", head=fmt_head_rows(df_after)
        ),
    )

    df_after = apply_weight_based_transport_fee(df_after, df_transport_cost)
    log_checkpoint(
        "after_apply_weight_based_transport_fee", df_after, df_transport_cost
    )
    logger.debug(
        "運搬費(重量別)適用後",
        extra=create_log_context(
            operation="finalize_block_unit_price", head=fmt_head_rows(df_after)
        ),
    )

    # --- Fallback for transport fee ---
    # Ensure '運搬費' exists and is numeric; prefer newly calculated values but
    # fall back to any previously saved '__old_transport_fee', then default to 0.
    if "運搬費" not in df_after.columns:
        df_after["運搬費"] = pd.Series(dtype="float64")
    df_after["運搬費"] = pd.to_numeric(df_after["運搬費"], errors="coerce")

    if "__old_transport_fee" in df_after.columns:
        _old = pd.to_numeric(df_after["__old_transport_fee"], errors="coerce")
        df_after["運搬費"] = df_after["運搬費"].fillna(_old)

    df_after["運搬費"] = df_after["運搬費"].fillna(0)
    df_after.drop(columns="__old_transport_fee", inplace=True, errors="ignore")
    # --- end fallback ---

    df_after = make_total_sum(df_after, master_csv)
    log_checkpoint("after_make_total_sum", df_after, master_csv)
    logger.debug(
        "合計行追加後",
        extra=create_log_context(
            operation="finalize_block_unit_price", head=fmt_head_rows(df_after)
        ),
    )

    df_after = df_cul_filtering(df_after)
    log_checkpoint("after_df_cul_filtering", df_after, None)
    logger.debug(
        "重複フィルタ後",
        extra=create_log_context(
            operation="finalize_block_unit_price", head=fmt_head_rows(df_after)
        ),
    )

    return df_after


# ------------------------------ Main Finalize Step ------------------------------


def execute_finalize_step(state: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    最終ステップの実行

    Args:
        state: 状態辞書

    Returns:
        (final_master_csv, payload): 最終マスターCSVとペイロード
    """
    try:
        logger.debug(
            "Finalize step開始",
            extra=create_log_context(
                operation="finalize_block_unit_price",
                session_id=state.get("session_id"),
                has_selection_df=bool(state.get("selection_df") is not None),
                selections_count=len(state.get("selections") or {}),
            ),
        )

        # マスターCSVと運搬費用データの読み込み
        config = get_template_config()["block_unit_price"]
        master_path = config["master_csv_path"]["vendor_code"]
        master_csv = load_master_and_template(master_path)

        mainpath = MainPath()
        reader = ReadTransportDiscount(mainpath)
        df_transport_cost = reader.load_discounted_df()

        log_checkpoint("transport_cost_loaded", df_transport_cost)
        logger.debug(
            "運搬費用データ読込",
            extra=create_log_context(
                operation="finalize_block_unit_price",
                head=fmt_head_rows(df_transport_cost),
            ),
        )

        # 初期出荷データの取得
        df_shipment_initial: pd.DataFrame = state["df_shipment"]
        _tmp_shipment = ensure_datetime_col(df_shipment_initial, "伝票日付")
        # ensure non-None DataFrame for static typing
        assert isinstance(_tmp_shipment, pd.DataFrame)
        df_shipment_initial = cast(pd.DataFrame, _tmp_shipment)
        log_checkpoint("shipment_initial", df_shipment_initial)

        # 選択データの準備
        selection_df: pd.DataFrame | None = state.get("selection_df")
        if (selection_df is None or selection_df.empty) and state.get("selections"):
            try:
                selections_dict = state["selections"]
                selection_df = pd.DataFrame(
                    [
                        {"entry_id": str(k), "selected_vendor": str(v)}
                        for k, v in selections_dict.items()
                    ]
                )
                logger.info(
                    f"selection_df created from selections dict: shape={selection_df.shape}, "
                    f"cols={list(selection_df.columns)}, sample={selection_df.head(3).to_dict()}",
                    extra=create_log_context(
                        operation="finalize_block_unit_price",
                        selection_df_cols=list(selection_df.columns),
                        selection_df_shape=selection_df.shape,
                        selection_df_sample=selection_df.head(3).to_dict(),
                        selections_dict_sample=dict(list(selections_dict.items())[:3]),
                    ),
                )
            except Exception as e:
                logger.error(
                    f"selection_df 作成失敗: {type(e).__name__}: {e}",
                    extra=create_log_context(
                        operation="finalize_block_unit_price",
                        error_type=type(e).__name__,
                        error_msg=str(e),
                    ),
                )
                selection_df = None

        # 選択の適用
        if selection_df is not None and not selection_df.empty:
            logger.info(
                "Using merge_selected_transport_vendors_with_df",
                extra=create_log_context(
                    operation="finalize_block_unit_price",
                    method="merge_with_df",
                    selection_df_shape=selection_df.shape,
                    selection_df_columns=list(selection_df.columns),
                ),
            )
            df_selected = merge_selected_transport_vendors_with_df(
                df_shipment_initial, selection_df
            )
        else:
            logger.info(
                "Using merge_selected_transport_vendors_copy",
                extra=create_log_context(
                    operation="finalize_block_unit_price",
                    method="merge_copy",
                    selections_count=len(state.get("selections") or {}),
                    has_selection_df=selection_df is not None,
                    selection_df_empty=(
                        selection_df.empty if selection_df is not None else None
                    ),
                ),
            )
            df_selected = merge_selected_transport_vendors_copy(
                df_shipment_initial, state
            )

        _tmp_selected = ensure_datetime_col(df_selected, "伝票日付")
        assert isinstance(_tmp_selected, pd.DataFrame)
        df_selected = cast(pd.DataFrame, _tmp_selected)
        log_checkpoint("shipment_selected", df_selected)
        logger.debug(f"selected head: {fmt_head_rows(df_selected)}")

        # パイプライン処理
        df_after = run_block_unit_price_pipeline(
            df_selected, df_transport_cost, master_csv
        )
        # ensure DataFrame after pipeline
        assert isinstance(df_after, pd.DataFrame)
        log_checkpoint("after_pipeline", df_after)

        # サマリーの作成
        summary = {
            "total_amount": float(
                df_after.get("合計金額", pd.Series(dtype=float)).sum() or 0
            ),
            "total_transport_fee": float(
                df_after.get("運搬費", pd.Series(dtype=float)).sum() or 0
            ),
            "processed_records": int(len(df_after)),
        }

        payload = {
            "status": "success",
            "summary": summary,
            "step": 2,
            "message": "ブロック単価計算が完了しました",
            "session_id": state.get("session_id"),
            "resolvedSelections": state.get("selections", {}),
            "debug": {
                "df_selected_cols": list(df_selected.columns),
                "df_after_cols": list(df_after.columns),
            },
        }

        # 最終マスターCSVの作成
        final_master_csv = first_cell_in_template(df_after)
        df_for_date_any = ensure_datetime_col(df_shipment_initial.copy(), "伝票日付")
        assert isinstance(df_for_date_any, pd.DataFrame)
        df_for_date = cast(pd.DataFrame, df_for_date_any)
        final_master_csv = make_sum_date(final_master_csv, df_for_date)
        # --- report_date: prefer 伝票日付 from the original shipment ---
        report_date = None
        try:
            if (
                isinstance(df_shipment_initial, pd.DataFrame)
                and "伝票日付" in df_shipment_initial.columns
            ):
                ser = pd.to_datetime(df_shipment_initial["伝票日付"], errors="coerce")
                nonnull = ser.dropna()
                if not nonnull.empty:
                    report_date = nonnull.iloc[0].date().isoformat()
        except Exception:
            report_date = None

        # Fallback to df_after if shipment didn't provide a usable date
        if not report_date:
            try:
                if (
                    isinstance(df_after, pd.DataFrame)
                    and "伝票日付" in df_after.columns
                ):
                    ser = pd.to_datetime(df_after["伝票日付"], errors="coerce")
                    nonnull = ser.dropna()
                    if not nonnull.empty:
                        report_date = nonnull.iloc[0].date().isoformat()
            except Exception:
                report_date = None

        # Last fallback: today
        if not report_date:
            from datetime import datetime

            report_date = datetime.now().date().isoformat()

        payload["report_date"] = report_date

        return final_master_csv, payload

    except Exception as e:
        # 共通エラーハンドリングを使用
        context: dict[str, Any] = {}
        try:
            if "df_selected" in locals():
                context["df_selected_cols"] = list(
                    getattr(locals()["df_selected"], "columns", [])
                )
                context["df_selected_head"] = fmt_head_rows(locals()["df_selected"])
            if "df_transport_cost" in locals():
                context["transport_cost_cols"] = list(
                    getattr(locals()["df_transport_cost"], "columns", [])
                )
                context["transport_cost_head"] = fmt_head_rows(
                    locals()["df_transport_cost"]
                )
        except Exception:
            pass

        return handle_step_error("finalize", 2, e, context)


def execute_finalize_with_optional_selections(
    state: dict[str, Any], user_input: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    オプショナル選択付き最終ステップの実行

    Args:
        state: 状態辞書
        user_input: ユーザー入力

    Returns:
        (final_master_csv, payload): 最終マスターCSVとペイロード
    """
    try:
        session_id_in = user_input.get("session_id")
        if (
            session_id_in
            and state.get("session_id")
            and session_id_in != state["session_id"]
        ):
            logger.warning(
                f"session_id 不一致: finalize続行 | "
                f"expected={state.get('session_id')}, got={session_id_in}"
            )

        # selection_rows からDataFrameを作成
        selection_rows = user_input.get("selection_rows") or []
        if isinstance(selection_rows, list) and selection_rows:
            try:
                state["selection_df"] = pd.DataFrame(selection_rows)
                logger.info(
                    "selection_rows→DataFrame変換",
                    extra=create_log_context(
                        operation="finalize_block_unit_price", rows=len(selection_rows)
                    ),
                )
            except Exception as e:
                logger.warning(
                    f"selection_rows の DataFrame 化に失敗: {type(e).__name__}: {e}"
                )

        # selections から正規化
        selections = user_input.get("selections") or {}
        if isinstance(selections, dict) and selections:
            # NOTE: resolve_and_apply_selections は元のクラスメソッドだが、
            # ここでは簡易的に状態に直接設定
            state["selections"] = selections
            logger.info(
                "selections設定",
                extra=create_log_context(
                    operation="finalize_block_unit_price", count=len(selections)
                ),
            )

            try:
                sel_df = pd.DataFrame(
                    [
                        {"entry_id": str(k), "selected_vendor": str(v)}
                        for k, v in selections.items()
                    ]
                )
                state["selection_df"] = sel_df
                logger.info(
                    "selections→selection_df生成",
                    extra=create_log_context(
                        operation="finalize_block_unit_price", rows=len(sel_df)
                    ),
                )
            except Exception as e:
                logger.warning(
                    f"selections の DataFrame 化に失敗: {type(e).__name__}: {e}"
                )

        return execute_finalize_step(state)

    except Exception as e:
        # 共通エラーハンドリングを使用
        context = {"function": "finalize_with_optional_selections"}
        return handle_step_error("finalize_with_selections", 2, e, context)
