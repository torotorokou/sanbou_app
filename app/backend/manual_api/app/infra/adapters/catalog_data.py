from app.utils.utils import build_manual_asset_url


sections = [
    {
        "id": "master",
        "title": "マスター情報・登録",
        "icon": "FolderOpenOutlined",
        "items": [
            {"id": "customer", "title": "取引先", "route": "/manual/master/customer", "description": "取引先の登録・更新・検索"},
            {
                "id": "vendor",
                "title": "業者",
                "route": "/manual/master/vendor",
                "description": "運搬業者・処分業者の管理",
                "flow_url": build_manual_asset_url("master/vender/vender_fllowchart.png"),
                "video_url": build_manual_asset_url("master/vender/vender_movie.mp4"),
                "tags": ["業者", "マスター"],
            },
            {"id": "site", "title": "現場", "route": "/manual/master/site"},
            {"id": "unitprice", "title": "単価", "route": "/manual/master/unit-price"},
            {"id": "item", "title": "品名", "route": "/manual/master/item"},
        ],
    },
    {
        "id": "contract",
        "title": "契約書",
        "icon": "FileProtectOutlined",
        "items": [
            {
                "id": "contract-reg-biz",
                "title": "登録関係（事業系）",
                "description": "事業系契約の登録フロー",
                "flow_url": "https://example.com/contract_biz_flow.pdf",
                "video_url": "https://example.com/contract_biz.mp4",
                "route": "/manual/contract/biz",
            },
            {
                "id": "contract-reg-construction",
                "title": "登録関係（建設系）",
                "flow_url": "https://example.com/contract_construction_flow.pdf",
                "video_url": "https://example.com/contract_construction.mp4",
                "route": "/manual/contract/construction",
            },
            {"id": "contract-search", "title": "検索", "route": "/manual/contract/search"},
        ],
    },
    {
        "id": "estimate",
        "title": "見積書",
        "icon": "FileTextOutlined",
        "items": [
            {
                "id": "estimate-make",
                "title": "見積書の作成フロー",
                "flow_url": "https://example.com/estimate_flow.pdf",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "description": "見積作成の全体像",
                "route": "/manual/estimate",
            },
        ],
    },
    {
        "id": "manifest",
        "title": "マニフェスト",
        "icon": "FileDoneOutlined",
        "items": [
            {
                "id": "mf-honest-out",
                "title": "工場外のオネスト運搬のマニフェスト入力",
                "flow_url": "https://example.com/mf_honest_out_flow.pdf",
                "video_url": "https://example.com/mf_honest_out.mp4",
                "route": "/manual/manifest/honest-out",
            },
            {"id": "mf-search", "title": "マニフェストの検索", "route": "/manual/manifest/search"},
            {"id": "mf-edit", "title": "マニフェストの修正", "route": "/manual/manifest/edit"},
            {
                "id": "mf-e-return",
                "title": "E票の返却",
                "flow_url": "https://example.com/mf_e_return.pdf",
                "video_url": "https://example.com/mf_e_return.mp4",
            },
            {"id": "mf-e-check", "title": "E票・返却の有無確認", "route": "/manual/manifest/e-check"},
            {"id": "mf-ledger", "title": "台帳", "route": "/manual/manifest/ledger"},
        ],
    },
    {
        "id": "external-input",
        "title": "工場外入力",
        "icon": "CloudUploadOutlined",
        "items": [
            {
                "id": "ext-sales",
                "title": "売上のみ入力",
                "flow_url": "https://example.com/ext_sales_flow.png",
                "video_url": "https://example.com/ext_sales.mp4",
            },
            {
                "id": "ext-purchase",
                "title": "仕入のみの入力",
                "flow_url": "https://example.com/ext_purchase_flow.png",
                "video_url": "https://example.com/ext_purchase.mp4",
            },
        ],
    },
]
