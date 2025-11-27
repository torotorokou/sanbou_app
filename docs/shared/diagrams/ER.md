erDiagram
  %% ========= 基本エンティティ =========
  REF_CALENDAR_DAY {
    date ddate PK
    int  iso_year
    int  iso_week
    int  iso_dow
  }

  REF_CALENDAR_EXCEPTION {
    date ddate PK
    text override_type
    text reason
    timestamp updated_at
  }

  REF_HOLIDAY_JP {
    date hdate PK
    text name
  }

  REF_CLOSURE_PERIODS {
    date start_date PK
    date end_date   PK
    text closure_name
  }

  KPI_MONTHLY_TARGETS {
    date   month_date PK
    text   segment    PK
    text   metric     PK
    numeric(20,4) value
    text   unit
    timestamptz updated_at
  }

  PLAN_MONTHLY_TARGET {
    date   month_date PK
    text   segment    PK
    text   metric     PK
    text   scenario   PK
    numeric(20,4) value
    text   unit
    timestamptz updated_at
  }

  RAW_RECEIVE_SHOGUN_FINAL {
    date   slip_date
    numeric(18,3) net_weight
    numeric(18,0) amount
    int    site_cd
    text   site_name
  }

  RAW_RECEIVE_SHOGUN_FLASH {
    date   slip_date
    numeric(18,3) net_weight
    numeric(18,0) amount
    int    site_cd
    text   site_name
  }

  RAW_RECEIVE_KING_FINAL {
    varchar(50) invoice_date   %% 文字列。日付へ変換して利用
    int         net_weight
    int         site_code
    varchar(50) site
  }

  %% ========= 論理（推定）リレーション =========
  %% カレンダー中心に“日付で結合する”実務上の関係。FK定義は未設定のため推定線。
  REF_CALENDAR_EXCEPTION  }o--||  REF_CALENDAR_DAY : ddate→ddate
  REF_HOLIDAY_JP         }o--||  REF_CALENDAR_DAY : hdate→ddate

  RAW_RECEIVE_SHOGUN_FINAL }o--|| REF_CALENDAR_DAY : slip_date→ddate
  RAW_RECEIVE_SHOGUN_FLASH }o--|| REF_CALENDAR_DAY : slip_date→ddate

  %% KINGは invoice_date が文字列。ビュー側で ::date などへ変換して結合する前提
  RAW_RECEIVE_KING_FINAL  }o..|| REF_CALENDAR_DAY : invoice_date(::date)→ddate

  %% 月次KPI/PLANは月初日で疎結合させる運用が多い（1日行と結ぶ）。実FKではなく論理線。
  KPI_MONTHLY_TARGETS     }o..|| REF_CALENDAR_DAY : month_date(1st)→ddate
  PLAN_MONTHLY_TARGET     }o..|| REF_CALENDAR_DAY : month_date(1st)→ddate

  %% クロージャは日付範囲（start_date..end_date）。図示のみ。実結合はレンジ条件。
  REF_CLOSURE_PERIODS     }o..o{ REF_CALENDAR_DAY : ddate∈[start_date,end_date]