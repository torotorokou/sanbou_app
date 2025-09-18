sections = [
    {
        "id": "master",
        "title": "マスター情報・登録",
        "icon": "FolderOpenOutlined",
        "items": [
            {"id": "customer", "title": "取引先", "route": "/manual/master/customer", "description": "取引先の登録・更新・検索"},
            {"id": "vendor", "title": "業者", "route": "/manual/master/vendor", "description": "運搬業者・処分業者の管理"},
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
            {"id": "ext-gp", "title": "粗利入力", "route": "/manual/external/gross-profit"},
        ],
    },
    {
        "id": "billing",
        "title": "請求書・支払い関係",
        "icon": "DollarOutlined",
        "items": [
            {
                "id": "doc-issue",
                "title": "各書類の発行（相殺含む）",
                "flow_url": "https://example.com/billing_issue_flow.pdf",
                "video_url": "https://example.com/billing_issue.mp4",
            },
            {"id": "doc-reissue", "title": "各書類の再発行", "route": "/manual/billing/reissue"},
            {"id": "doc-delete", "title": "各処理の削除", "route": "/manual/billing/delete"},
        ],
    },
    {
        "id": "e-manifest",
        "title": "電子マニフェスト",
        "icon": "FileSyncOutlined",
        "items": [
            {"id": "e-transport", "title": "運搬終了報告", "route": "/manual/emanifest/transport-finish"},
            {"id": "e-disposal", "title": "処分終了報告", "route": "/manual/emanifest/disposal-finish"},
            {
                "id": "e-helper",
                "title": "補助データ作成",
                "flow_url": "https://example.com/emanifest_helper_flow.pdf",
                "video_url": "https://example.com/emanifest_helper.mp4",
            },
            {
                "id": "e-mix",
                "title": "混合振り分け",
                "flow_url": "https://example.com/emanifest_mix.png",
                "video_url": "https://example.com/emanifest_mix.mp4",
            },
        ],
    },
    {
        "id": "reports",
        "title": "報告書",
        "icon": "FileSearchOutlined",
        "items": [
            {"id": "report-result", "title": "実績報告", "route": "/manual/reports/results"},
            {"id": "report-kofu", "title": "交付等状況報告書", "route": "/manual/reports/kofu"},
        ],
    },
]
