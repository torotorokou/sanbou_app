"""
Unit tests for Materialized View Refresh functionality

受入CSV成功時のマテビュー自動更新機能のテスト。
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.infra.adapters.materialized_view.materialized_view_refresher import MaterializedViewRefresher


class TestMaterializedViewRefresher:
    """MaterializedViewRefresher のテスト"""
    
    def test_initialization(self):
        """初期化のテスト"""
        mock_db = Mock(spec=Session)
        refresher = MaterializedViewRefresher(mock_db)
        
        assert refresher.db == mock_db
        assert "receive" in refresher.MV_MAPPINGS
        assert "mart.mv_target_card_per_day" in refresher.MV_MAPPINGS["receive"]
    
    def test_list_available_mvs_all(self):
        """利用可能なMV一覧取得（全体）"""
        mock_db = Mock(spec=Session)
        refresher = MaterializedViewRefresher(mock_db)
        
        all_mvs = refresher.list_available_mvs()
        
        assert isinstance(all_mvs, list)
        assert "mart.mv_target_card_per_day" in all_mvs
    
    def test_list_available_mvs_receive(self):
        """利用可能なMV一覧取得（receive）"""
        mock_db = Mock(spec=Session)
        refresher = MaterializedViewRefresher(mock_db)
        
        receive_mvs = refresher.list_available_mvs(csv_type="receive")
        
        assert isinstance(receive_mvs, list)
        assert "mart.mv_target_card_per_day" in receive_mvs
    
    def test_list_available_mvs_unknown_type(self):
        """利用可能なMV一覧取得（未定義のcsv_type）"""
        mock_db = Mock(spec=Session)
        refresher = MaterializedViewRefresher(mock_db)
        
        unknown_mvs = refresher.list_available_mvs(csv_type="unknown")
        
        assert unknown_mvs == []
    
    @patch('app.infra.adapters.materialized_view.materialized_view_refresher.logger')
    def test_refresh_single_mv_success(self, mock_logger):
        """単一MV更新成功のテスト"""
        mock_db = Mock(spec=Session)
        mock_db.execute = MagicMock()
        mock_db.commit = MagicMock()
        
        refresher = MaterializedViewRefresher(mock_db)
        
        # エラーなく実行できることを確認
        refresher._refresh_single_mv("mart.mv_target_card_per_day")
        
        # SQL実行とコミットが呼ばれたか確認
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # ログ出力を確認
        assert mock_logger.info.call_count >= 2  # 開始と完了のログ
    
    @patch('app.infra.adapters.materialized_view.materialized_view_refresher.logger')
    def test_refresh_single_mv_failure(self, mock_logger):
        """単一MV更新失敗のテスト"""
        mock_db = Mock(spec=Session)
        mock_db.execute = MagicMock(side_effect=Exception("DB error"))
        mock_db.rollback = MagicMock()
        
        refresher = MaterializedViewRefresher(mock_db)
        
        # 例外が発生することを確認
        with pytest.raises(Exception, match="DB error"):
            refresher._refresh_single_mv("mart.mv_target_card_per_day")
        
        # ロールバックが呼ばれたか確認
        mock_db.rollback.assert_called_once()
        
        # エラーログが出力されたか確認
        mock_logger.error.assert_called()
    
    @patch('app.infra.adapters.materialized_view.materialized_view_refresher.logger')
    def test_refresh_for_csv_type_receive(self, mock_logger):
        """csv_type='receive'でMV更新"""
        mock_db = Mock(spec=Session)
        mock_db.execute = MagicMock()
        mock_db.commit = MagicMock()
        
        refresher = MaterializedViewRefresher(mock_db)
        
        # エラーなく実行できることを確認
        refresher.refresh_for_csv_type("receive")
        
        # execute と commit が呼ばれたか確認（receiveに関連するMV分）
        assert mock_db.execute.call_count >= 1
        assert mock_db.commit.call_count >= 1
    
    @patch('app.infra.adapters.materialized_view.materialized_view_refresher.logger')
    def test_refresh_for_csv_type_no_mvs(self, mock_logger):
        """MVが定義されていないcsv_typeでの実行"""
        mock_db = Mock(spec=Session)
        refresher = MaterializedViewRefresher(mock_db)
        
        # エラーなく実行できることを確認
        refresher.refresh_for_csv_type("unknown_type")
        
        # ログに "No materialized views defined" が出力されることを確認
        log_message = mock_logger.info.call_args[0][0]
        assert "No materialized views defined" in log_message
    
    @patch('app.infra.adapters.materialized_view.materialized_view_refresher.logger')
    def test_refresh_all_receive_mvs(self, mock_logger):
        """refresh_all_receive_mvs のテスト"""
        mock_db = Mock(spec=Session)
        mock_db.execute = MagicMock()
        mock_db.commit = MagicMock()
        
        refresher = MaterializedViewRefresher(mock_db)
        
        # エラーなく実行できることを確認
        refresher.refresh_all_receive_mvs()
        
        # execute と commit が呼ばれたか確認
        assert mock_db.execute.call_count >= 1
        assert mock_db.commit.call_count >= 1


class TestUploadUseCaseIntegration:
    """UploadShogunCsvUseCase とのインテグレーションテスト（モック版）"""
    
    @patch('app.application.usecases.upload.upload_shogun_csv_uc.logger')
    def test_mv_refresh_called_on_receive_success(self, mock_logger):
        """受入CSV成功時にMV更新が呼ばれることを確認"""
        from app.core.usecases.upload.upload_shogun_csv_uc import UploadShogunCsvUseCase
        
        # モックの準備
        mock_raw_writer = Mock()
        mock_stg_writer = Mock()
        mock_csv_config = Mock()
        mock_validator = Mock()
        mock_raw_data_repo = Mock()
        mock_mv_refresher = Mock()
        
        # UseCase生成
        uc = UploadShogunCsvUseCase(
            raw_writer=mock_raw_writer,
            stg_writer=mock_stg_writer,
            csv_config=mock_csv_config,
            validator=mock_validator,
            raw_data_repo=mock_raw_data_repo,
            mv_refresher=mock_mv_refresher,
        )
        
        # テストデータ
        upload_file_ids = {"receive": 1}
        formatted_dfs = {"receive": Mock(spec=["__len__"])}
        formatted_dfs["receive"].__len__ = Mock(return_value=100)
        stg_result = {"receive": {"status": "success", "rows_saved": 100}}
        
        # _update_upload_logs を実行
        uc._update_upload_logs(upload_file_ids, formatted_dfs, stg_result)
        
        # MV更新が呼ばれたか確認
        mock_mv_refresher.refresh_for_csv_type.assert_called_once_with("receive")
    
    @patch('app.application.usecases.upload.upload_shogun_csv_uc.logger')
    def test_mv_refresh_not_called_on_failure(self, mock_logger):
        """アップロード失敗時にMV更新が呼ばれないことを確認"""
        from app.core.usecases.upload.upload_shogun_csv_uc import UploadShogunCsvUseCase
        
        # モックの準備
        mock_raw_writer = Mock()
        mock_stg_writer = Mock()
        mock_csv_config = Mock()
        mock_validator = Mock()
        mock_raw_data_repo = Mock()
        mock_mv_refresher = Mock()
        
        # UseCase生成
        uc = UploadShogunCsvUseCase(
            raw_writer=mock_raw_writer,
            stg_writer=mock_stg_writer,
            csv_config=mock_csv_config,
            validator=mock_validator,
            raw_data_repo=mock_raw_data_repo,
            mv_refresher=mock_mv_refresher,
        )
        
        # テストデータ（失敗ケース）
        upload_file_ids = {"receive": 1}
        formatted_dfs = {"receive": Mock()}
        stg_result = {"receive": {"status": "failed", "detail": "Validation error"}}
        
        # _update_upload_logs を実行
        uc._update_upload_logs(upload_file_ids, formatted_dfs, stg_result)
        
        # MV更新が呼ばれないことを確認
        mock_mv_refresher.refresh_for_csv_type.assert_not_called()
    
    @patch('app.application.usecases.upload.upload_shogun_csv_uc.logger')
    def test_mv_refresh_error_does_not_break_upload(self, mock_logger):
        """MV更新エラーでもアップロード処理は継続することを確認"""
        from app.core.usecases.upload.upload_shogun_csv_uc import UploadShogunCsvUseCase
        
        # モックの準備
        mock_raw_writer = Mock()
        mock_stg_writer = Mock()
        mock_csv_config = Mock()
        mock_validator = Mock()
        mock_raw_data_repo = Mock()
        mock_mv_refresher = Mock()
        mock_mv_refresher.refresh_for_csv_type = Mock(side_effect=Exception("MV error"))
        
        # UseCase生成
        uc = UploadShogunCsvUseCase(
            raw_writer=mock_raw_writer,
            stg_writer=mock_stg_writer,
            csv_config=mock_csv_config,
            validator=mock_validator,
            raw_data_repo=mock_raw_data_repo,
            mv_refresher=mock_mv_refresher,
        )
        
        # テストデータ
        upload_file_ids = {"receive": 1}
        formatted_dfs = {"receive": Mock(spec=["__len__"])}
        formatted_dfs["receive"].__len__ = Mock(return_value=100)
        stg_result = {"receive": {"status": "success", "rows_saved": 100}}
        
        # エラーが発生しても例外が外部に伝播しないことを確認
        try:
            uc._update_upload_logs(upload_file_ids, formatted_dfs, stg_result)
        except Exception as e:
            pytest.fail(f"MV refresh error should not break upload: {e}")
        
        # エラーログが出力されたか確認
        mock_logger.error.assert_called()
        error_message = str(mock_logger.error.call_args)
        assert "Failed to refresh" in error_message or "MV error" in error_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
