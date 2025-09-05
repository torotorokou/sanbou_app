import pandas as pd

# 1日分に絞る
def day1_filtered(df: pd.DataFrame, report_date: str) -> pd.DataFrame:
    df_filtered = df[df["date"] == report_date]
    return df_filtered


# 1週間分に絞る

# 1か月分に絞る
