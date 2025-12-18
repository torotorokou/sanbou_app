"""
将軍データセット取得クラスのテスト

pytest で実行可能なユニットテスト
DBなしでテスト可能な部分を中心に実装
"""
import pytest
from datetime import date
from backend_shared.db.shogun.dataset_keys import ShogunDatasetKey
from backend_shared.db.shogun.master_name_mapper import ShogunMasterNameMapper


class TestShogunDatasetKey:
    """ShogunDatasetKeyのテスト"""
    
    def test_enum_values(self):
        """Enumの値が正しいこと"""
        assert ShogunDatasetKey.SHOGUN_FINAL_RECEIVE.value == "shogun_final_receive"
        assert ShogunDatasetKey.SHOGUN_FLASH_SHIPMENT.value == "shogun_flash_shipment"
    
    def test_is_final(self):
        """is_finalプロパティが正しく動作すること"""
        assert ShogunDatasetKey.SHOGUN_FINAL_RECEIVE.is_final is True
        assert ShogunDatasetKey.SHOGUN_FLASH_RECEIVE.is_final is False
    
    def test_is_flash(self):
        """is_flashプロパティが正しく動作すること"""
        assert ShogunDatasetKey.SHOGUN_FLASH_RECEIVE.is_flash is True
        assert ShogunDatasetKey.SHOGUN_FINAL_RECEIVE.is_flash is False
    
    def test_data_type(self):
        """data_typeプロパティが正しく返されること"""
        assert ShogunDatasetKey.SHOGUN_FINAL_RECEIVE.data_type == "receive"
        assert ShogunDatasetKey.SHOGUN_FLASH_SHIPMENT.data_type == "shipment"
        assert ShogunDatasetKey.SHOGUN_FINAL_YARD.data_type == "yard"
    
    def test_get_view_name(self):
        """get_view_name()が正しいview名を返すこと"""
        assert ShogunDatasetKey.SHOGUN_FINAL_RECEIVE.get_view_name() == "v_active_shogun_final_receive"
        assert ShogunDatasetKey.SHOGUN_FLASH_SHIPMENT.get_view_name() == "v_active_shogun_flash_shipment"
    
    def test_get_master_key(self):
        """get_master_key()が正しいmaster.yamlキーを返すこと"""
        assert ShogunDatasetKey.SHOGUN_FINAL_RECEIVE.get_master_key() == "receive"
        assert ShogunDatasetKey.SHOGUN_FLASH_SHIPMENT.get_master_key() == "shipment"
        assert ShogunDatasetKey.SHOGUN_FINAL_YARD.get_master_key() == "yard"


class TestShogunMasterNameMapper:
    """ShogunMasterNameMapperのテスト"""
    
    def test_extract_master_key(self):
        """_extract_master_key()が正しくキーを抽出すること"""
        assert ShogunMasterNameMapper._extract_master_key("shogun_final_receive") == "receive"
        assert ShogunMasterNameMapper._extract_master_key("shogun_flash_shipment") == "shipment"
        assert ShogunMasterNameMapper._extract_master_key("shogun_final_yard") == "yard"
        assert ShogunMasterNameMapper._extract_master_key("invalid_key") is None
    
    @pytest.mark.skipif(
        True,
        reason="実際のmaster.yamlファイルが必要なため、統合テストで実行"
    )
    def test_get_dataset_label(self):
        """
        get_dataset_label()が正しい日本語ラベルを返すこと
        
        注意: このテストは実際のmaster.yamlが必要
        """
        mapper = ShogunMasterNameMapper()
        
        # 実際のmaster.yamlから取得
        label = mapper.get_dataset_label("shogun_final_receive")
        assert label == "受入一覧"
        
        label = mapper.get_dataset_label("shogun_flash_shipment")
        assert label == "出荷一覧"
    
    @pytest.mark.skipif(
        True,
        reason="実際のmaster.yamlファイルが必要なため、統合テストで実行"
    )
    def test_get_ja_column_name(self):
        """
        get_ja_column_name()が正しく英語→日本語変換すること
        
        注意: このテストは実際のmaster.yamlが必要
        """
        mapper = ShogunMasterNameMapper()
        
        ja_name = mapper.get_ja_column_name("receive", "slip_date")
        assert ja_name == "伝票日付"
        
        ja_name = mapper.get_ja_column_name("shipment", "vendor_name")
        assert ja_name == "業者名"
    
    @pytest.mark.skipif(
        True,
        reason="実際のmaster.yamlファイルが必要なため、統合テストで実行"
    )
    def test_get_en_column_name(self):
        """
        get_en_column_name()が正しく日本語→英語変換すること
        
        注意: このテストは実際のmaster.yamlが必要
        """
        mapper = ShogunMasterNameMapper()
        
        en_name = mapper.get_en_column_name("receive", "伝票日付")
        assert en_name == "slip_date"
        
        en_name = mapper.get_en_column_name("shipment", "業者名")
        assert en_name == "vendor_name"


class TestShogunDatasetFetcher:
    """
    ShogunDatasetFetcherのテスト
    
    注意: DB接続が必要なため、実際のテストはskip
    統合テスト環境で実行すること
    """
    
    @pytest.mark.skipif(
        True,
        reason="DB接続が必要なため、統合テストで実行"
    )
    def test_fetch_final_receive(self):
        """
        fetch()が正しくデータを取得すること
        
        注意: このテストはDB接続が必要
        """
        # from sqlalchemy import create_engine
        # from sqlalchemy.orm import Session
        # from backend_shared.shogun import ShogunDatasetFetcher, ShogunDatasetKey
        # 
        # engine = create_engine("postgresql://...")
        # with Session(engine) as session:
        #     fetcher = ShogunDatasetFetcher(session)
        #     data = fetcher.fetch(
        #         ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
        #         limit=10
        #     )
        #     assert len(data) <= 10
        #     assert isinstance(data, list)
        #     if data:
        #         assert isinstance(data[0], dict)
        pass
    
    @pytest.mark.skipif(
        True,
        reason="DB接続が必要なため、統合テストで実行"
    )
    def test_fetch_with_date_filter(self):
        """
        日付フィルタが正しく動作すること
        
        注意: このテストはDB接続が必要
        """
        # from sqlalchemy import create_engine
        # from sqlalchemy.orm import Session
        # from backend_shared.shogun import ShogunDatasetFetcher, ShogunDatasetKey
        # 
        # engine = create_engine("postgresql://...")
        # with Session(engine) as session:
        #     fetcher = ShogunDatasetFetcher(session)
        #     data = fetcher.fetch(
        #         ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
        #         start_date=date(2024, 4, 1),
        #         end_date=date(2024, 10, 31),
        #     )
        #     # 全てのレコードが日付範囲内であることを確認
        #     for row in data:
        #         slip_date = row.get("slip_date")
        #         if slip_date:
        #             assert date(2024, 4, 1) <= slip_date <= date(2024, 10, 31)
        pass
    
    @pytest.mark.skipif(
        True,
        reason="DB接続が必要なため、統合テストで実行"
    )
    def test_convenience_methods(self):
        """
        便利メソッド（get_final_receive等）が正しく動作すること
        
        注意: このテストはDB接続が必要
        """
        # from sqlalchemy import create_engine
        # from sqlalchemy.orm import Session
        # from backend_shared.shogun import ShogunDatasetFetcher
        # 
        # engine = create_engine("postgresql://...")
        # with Session(engine) as session:
        #     fetcher = ShogunDatasetFetcher(session)
        #     
        #     # 6種類の便利メソッドが全て動作することを確認
        #     data = fetcher.get_final_receive(limit=1)
        #     assert isinstance(data, list)
        #     
        #     data = fetcher.get_flash_shipment(limit=1)
        #     assert isinstance(data, list)
        pass
