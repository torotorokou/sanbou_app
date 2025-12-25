"""
Unit tests for Materialized View Refresh functionality

受入CSV成功時のマテビュー自動更新機能のテスト。
"""

from unittest.mock import MagicMock, Mock, patch

from sqlalchemy.orm import Session

from app.infra.adapters.materialized_view.materialized_view_refresher import (
    MaterializedViewRefresher,
)


class TestMaterializedViewRefresher:
    """MaterializedViewRefresher のテスト"""

    def test_initialization(self):
        """初期化のテスト"""
        mock_db = Mock(spec=Session)
        refresher = MaterializedViewRefresher(mock_db)

        assert refresher.db == mock_db
        assert "receive" in refresher.MV_MAPPINGS
        assert "mart.mv_target_card_per_day" in refresher.MV_MAPPINGS["receive"]

    def test_mv_mappings_order(self):
        """MV_MAPPINGSの順序確認（依存関係を考慮）"""
        mock_db = Mock(spec=Session)
        refresher = MaterializedViewRefresher(mock_db)

        receive_mvs = refresher.MV_MAPPINGS["receive"]

        # mv_receive_dailyが先、mv_target_card_per_dayが後
        assert receive_mvs[0] == "mart.mv_receive_daily"
        assert receive_mvs[1] == "mart.mv_target_card_per_day"

    @patch("app.infra.adapters.materialized_view.materialized_view_refresher.logger")
    def test_refresh_mv_success(self, mock_logger):
        """単一MV更新成功のテスト"""
        mock_db = Mock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100  # row count
        mock_db.execute = MagicMock(return_value=mock_result)

        refresher = MaterializedViewRefresher(mock_db)

        # エラーなく実行できることを確認
        refresher._refresh_mv("mart.mv_receive_daily")

        # SQL実行が呼ばれたか確認（REFRESH + COUNT）
        assert mock_db.execute.call_count == 2

    @patch("app.infra.adapters.materialized_view.materialized_view_refresher.logger")
    def test_refresh_mv_fallback_to_normal(self, mock_logger):
        """CONCURRENTLY失敗時のフォールバックテスト"""
        mock_db = Mock(spec=Session)

        call_count = [0]
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100

        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("unique index required")
            return mock_result

        mock_db.execute = MagicMock(side_effect=execute_side_effect)

        refresher = MaterializedViewRefresher(mock_db)

        # フォールバックして成功
        refresher._refresh_mv("mart.mv_receive_daily")

        # CONCURRENTLY → 通常REFRESH → COUNTで3回
        assert mock_db.execute.call_count == 3
        mock_logger.warning.assert_called()  # フォールバックログ

    @patch("app.infra.adapters.materialized_view.materialized_view_refresher.logger")
    def test_refresh_for_csv_type_receive(self, mock_logger):
        """csv_type='receive'でMV更新"""
        mock_db = Mock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100
        mock_db.execute = MagicMock(return_value=mock_result)
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        refresher = MaterializedViewRefresher(mock_db)

        # エラーなく実行できることを確認
        refresher.refresh_for_csv_type("receive")

        # 2つのMVに対してexecuteが呼ばれた（各MVで REFRESH + COUNT）
        assert mock_db.execute.call_count == 4
        # 各MV更新後にcommit
        assert mock_db.commit.call_count == 2

    @patch("app.infra.adapters.materialized_view.materialized_view_refresher.logger")
    def test_refresh_for_csv_type_no_mvs(self, mock_logger):
        """MVが定義されていないcsv_typeでの実行"""
        mock_db = Mock(spec=Session)
        refresher = MaterializedViewRefresher(mock_db)

        # エラーなく実行できることを確認
        refresher.refresh_for_csv_type("unknown_type")

        # ログに "No MVs defined" が出力されることを確認
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "No MVs defined" in log_message

    @patch("app.infra.adapters.materialized_view.materialized_view_refresher.logger")
    def test_refresh_for_csv_type_partial_failure(self, mock_logger):
        """複数MV更新時に一部失敗しても処理が継続することを確認"""
        mock_db = Mock(spec=Session)
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        # 最初のMVは成功、2番目のMVは失敗
        call_count = [0]
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100

        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 3:  # 2番目のMVのREFRESH
                raise Exception("MV update error")
            return mock_result

        mock_db.execute = MagicMock(side_effect=execute_side_effect)

        refresher = MaterializedViewRefresher(mock_db)

        # エラーなく実行完了することを確認（例外が外部に伝播しない）
        refresher.refresh_for_csv_type("receive")

        # 成功1回 + 失敗でrollback1回
        assert mock_db.commit.call_count == 1
        assert mock_db.rollback.call_count == 1

        # エラーログと警告ログが出力されたか確認
        assert mock_logger.error.call_count >= 1
        assert mock_logger.warning.call_count >= 1

    @patch("app.infra.adapters.materialized_view.materialized_view_refresher.logger")
    def test_refresh_for_csv_kind_receive(self, mock_logger):
        """csv_kindからMV更新"""
        mock_db = Mock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100
        mock_db.execute = MagicMock(return_value=mock_result)
        mock_db.commit = MagicMock()

        refresher = MaterializedViewRefresher(mock_db)

        # shogun_flash_receive → receive
        refresher.refresh_for_csv_kind("shogun_flash_receive")

        # MV更新が実行されたか確認
        assert mock_db.execute.call_count >= 2

    @patch("app.infra.adapters.materialized_view.materialized_view_refresher.logger")
    def test_refresh_for_csv_kind_unknown(self, mock_logger):
        """不明なcsv_kindでMV更新がスキップされる"""
        mock_db = Mock(spec=Session)

        refresher = MaterializedViewRefresher(mock_db)

        # 不明なcsv_kind
        refresher.refresh_for_csv_kind("unknown_csv_kind")

        # executeは呼ばれない
        mock_db.execute.assert_not_called()

    def test_extract_csv_type_from_csv_kind(self):
        """静的メソッドのテスト"""
        assert (
            MaterializedViewRefresher.extract_csv_type_from_csv_kind(
                "shogun_flash_receive"
            )
            == "receive"
        )
        assert (
            MaterializedViewRefresher.extract_csv_type_from_csv_kind(
                "shogun_final_shipment"
            )
            == "shipment"
        )
        assert (
            MaterializedViewRefresher.extract_csv_type_from_csv_kind(
                "shogun_flash_yard"
            )
            == "yard"
        )
        assert (
            MaterializedViewRefresher.extract_csv_type_from_csv_kind("invalid") is None
        )

    def test_should_refresh_mv_for_csv_type(self):
        """静的メソッドのテスト"""
        assert (
            MaterializedViewRefresher.should_refresh_mv_for_csv_type("receive") is True
        )
        assert (
            MaterializedViewRefresher.should_refresh_mv_for_csv_type("shipment")
            is False
        )
        assert MaterializedViewRefresher.should_refresh_mv_for_csv_type("yard") is False

    @patch("app.infra.adapters.materialized_view.materialized_view_refresher.logger")
    def test_refresh_all_receive_mvs(self, mock_logger):
        """後方互換性メソッドのテスト"""
        mock_db = Mock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100
        mock_db.execute = MagicMock(return_value=mock_result)
        mock_db.commit = MagicMock()

        refresher = MaterializedViewRefresher(mock_db)

        # エラーなく実行できることを確認
        refresher.refresh_all_receive_mvs()

        # MV更新が実行されたか確認
        assert mock_db.execute.call_count >= 2
