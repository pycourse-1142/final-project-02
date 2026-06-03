# parser.py

import pandas as pd
import numpy as np
import glob
import os


# ==========================
# 可依實際資料欄位名稱修改
# ==========================

SITE_COLS = [
    "SiteName",
    "測站",
    "測站名稱"
]

DATE_COLS = [
    "MonitorDate",
    "日期",
    "測量日期"
]

INVALID_VALUES = [
    "...",
    "-999",
    "NR",
    "#",
    "",
    " "
]


# ==========================
# 找出實際欄位名稱
# ==========================

def find_column(df, candidates):

    for col in candidates:
        if col in df.columns:
            return col

    return None


# ==========================
# 欄位驗證
# ==========================

def validate_dataframe(df):

    site_col = find_column(df, SITE_COLS)
    date_col = find_column(df, DATE_COLS)

    if site_col is None:
        raise ValueError("缺少測站欄位")

    if date_col is None:
        raise ValueError("缺少日期欄位")

    return site_col, date_col


# ==========================
# 找出24小時欄位
# ==========================

def get_hour_columns(df):

    hour_cols = []

    for col in df.columns:

        col_str = str(col).strip()

        if col_str.isdigit():

            hour = int(col_str)

            if 0 <= hour <= 23:
                hour_cols.append(col)

    if len(hour_cols) == 0:
        raise ValueError("找不到 00~23 小時欄位")

    return sorted(hour_cols, key=lambda x: int(str(x)))


# ==========================
# 清洗單一 DataFrame
# ==========================

def clean_dataframe(df):

    site_col, date_col = validate_dataframe(df)

    hour_cols = get_hour_columns(df)

    # 異常值轉 NaN
    df = df.replace(INVALID_VALUES, np.nan)

    # 小時欄位轉數字
    df[hour_cols] = df[hour_cols].apply(
        pd.to_numeric,
        errors="coerce"
    )

    # 橫轉直
    df_long = pd.melt(
        df,
        id_vars=[site_col, date_col],
        value_vars=hour_cols,
        var_name="Hour",
        value_name="Value"
    )

    # 建立 Datetime
    df_long["Datetime"] = pd.to_datetime(
        df_long[date_col].astype(str)
        + " "
        + df_long["Hour"].astype(str).str.zfill(2)
        + ":00",
        errors="coerce"
    )

    # 統一欄位名稱
    df_long = df_long.rename(
        columns={
            site_col: "SiteName"
        }
    )

    # 去除無效資料
    df_long = df_long.dropna(
        subset=[
            "SiteName",
            "Datetime"
        ]
    )

    # 重新排序
    df_long = df_long[
        [
            "SiteName",
            "Datetime",
            "Value"
        ]
    ]

    return df_long


# ==========================
# 讀取單一 CSV
# ==========================

def load_single_csv(file_path):

    try:

        df = pd.read_csv(
            file_path,
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        df = pd.read_csv(
            file_path,
            encoding="big5"
        )

    return df


# ==========================
# 讀取所有 CSV
# ==========================

def load_all_csv(data_folder):

    csv_files = glob.glob(
        os.path.join(data_folder, "*.csv")
    )

    if len(csv_files) == 0:
        raise FileNotFoundError(
            f"{data_folder} 找不到 CSV 檔案"
        )

    return csv_files


# ==========================
# 主函式
# ==========================

def load_and_clean_data(data_folder="data"):

    csv_files = load_all_csv(data_folder)

    cleaned_dfs = []

    success_count = 0
    fail_count = 0

    print(f"\n找到 {len(csv_files)} 個 CSV 檔案\n")

    for file in csv_files:

        try:

            print(f"處理中：{os.path.basename(file)}")

            raw_df = load_single_csv(file)

            clean_df = clean_dataframe(raw_df)

            cleaned_dfs.append(clean_df)

            success_count += 1

            print(
                f"成功：{len(clean_df)} 筆資料"
            )

        except Exception as e:

            fail_count += 1

            print(
                f"失敗：{os.path.basename(file)}"
            )

            print(f"原因：{e}")

            continue

    if len(cleaned_dfs) == 0:

        raise ValueError(
            "所有檔案皆處理失敗"
        )

    final_df = pd.concat(
        cleaned_dfs,
        ignore_index=True
    )

    final_df = final_df.sort_values(
        by=[
            "SiteName",
            "Datetime"
        ]
    )

    print("\n==========")
    print("處理完成")
    print("==========")
    print(f"成功檔案：{success_count}")
    print(f"失敗檔案：{fail_count}")
    print(f"總資料筆數：{len(final_df)}")

    return final_df