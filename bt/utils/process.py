import pandas as pd

def process_data(path):
    df_data = pd.read_csv(path)
    df_data.index = pd.to_datetime(df_data["日期"], format="%Y年%m月%d日")
    if any(df_data["交易量"].astype(str).str.contains("-")):
        df_data["交易量"][df_data["交易量"].str.contains("-")] = df_data["交易量"][
            df_data["交易量"].str.contains("-")
        ].replace("-", 0)
    if any(df_data["交易量"].astype(str).str.contains("B")):
        df_data["交易量"][df_data["交易量"].str.contains("B").fillna(False)] = (
                df_data["交易量"][df_data["交易量"].str.contains("B").fillna(False)]
                .str.replace("B", "")
                .str.replace(",", "")
                .astype(float)
                * 1000000000
        )
    if any(df_data["交易量"].astype(str).str.contains("M")):
        df_data["交易量"][df_data["交易量"].str.contains("M").fillna(False)] = (
                df_data["交易量"][df_data["交易量"].str.contains("M").fillna(False)]
                .str.replace("M", "")
                .str.replace(",", "")
                .astype(float)
                * 1000000
        )
    if any(df_data["交易量"].astype(str).str.contains("K")):
        df_data["交易量"][df_data["交易量"].str.contains("K").fillna(False)] = (
                df_data["交易量"][df_data["交易量"].str.contains("K").fillna(False)]
                .str.replace("K", "")
                .str.replace(",", "")
                .astype(float)
                * 1000
        )
    df_data["交易量"] = df_data["交易量"].astype(float)
    df_data["涨跌幅"] = pd.DataFrame(
        round(
            df_data["涨跌幅"].str.replace(",", "").str.replace("%", "").astype(float)
            / 100,
            6,
        )
    )
    del df_data["日期"]
    df_data.reset_index(inplace=True)
    df_data = df_data[[
        "日期",
        "收盘",
        "开盘",
        "高",
        "低",
        "交易量",
        "涨跌幅",
    ]]
    df_data['日期'] = pd.to_datetime(df_data['日期']).dt.date
    df_data['收盘'] = pd.to_numeric(df_data['收盘'].str.replace(",", ""))
    df_data['开盘'] = pd.to_numeric(df_data['开盘'].str.replace(",", ""))
    df_data['高'] = pd.to_numeric(df_data['高'].str.replace(",", ""))
    df_data['低'] = pd.to_numeric(df_data['低'].str.replace(",", ""))
    df_data['交易量'] = pd.to_numeric(df_data['交易量'])
    df_data['涨跌幅'] = pd.to_numeric(df_data['涨跌幅'])
    df_data.sort_values('日期', inplace=True)
    df_data.reset_index(inplace=True, drop=True)
    return df_data