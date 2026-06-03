import pandas as pd
import numpy as np
import glob
import os

# =========================
# 髒資料定義
# =========================
INVALID_VALUES = ["...", "-999", "NR", "#", "", " "]


# =========================
# 欄位檢查
# =========================
def validate_columns(df):

    required = ["測站", "日期", "測項"]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"缺少必要欄位: {missing}")


# =========================
# 取得 00~23 欄位
# =========================
def get_hour_columns(df):

    hour_cols = [f"{i:02d}" for i in range(24)]

    exist_hours = [c for c in hour_cols if c in df.columns]

    if len(exist_hours) != 24:
        raise ValueError("缺少 00~23 小時欄位")

    return exist_hours


# =========================
# 單檔清理
# =========================
def clean_dataframe(df):

    validate_columns(df)

    hour_cols = get_hour_columns(df)

    # 1️⃣ 髒資料轉 NaN
    df = df.replace(INVALID_VALUES, np.nan)

    # 2️⃣ 數值轉換
    df[hour_cols] = df[hour_cols].apply(
        pd.to_numeric,
        errors="coerce"
    )

    # 3️⃣ 橫轉直
    df_long = pd.melt(
        df,
        id_vars=["測站", "日期", "測項"],
        value_vars=hour_cols,
        var_name="Hour",
        value_name="Value"
    )

    # 4️⃣ 建立時間
    df_long["Datetime"] = pd.to_datetime(
        df_long["日期"].astype(str).str[:10]
        + " "
        + df_long["Hour"] + ":00:00",
        errors="coerce"
    )

    # 5️⃣ 欄位標準化
    df_long = df_long.rename(columns={
        "測站": "SiteName",
        "測項": "Item"
    })

    # 6️⃣ 移除無效資料
    df_long = df_long.dropna(subset=["Datetime", "Value"])

    return df_long[["SiteName", "Datetime", "Item", "Value"]]


# =========================
# 讀單一 CSV
# =========================
def load_single_csv(file_path):

    try:
        return pd.read_csv(file_path, encoding="utf-8")

    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding="big5")


# =========================
# 讀所有 CSV（支援子資料夾）
# =========================
def load_all_csv(data_folder):

    csv_files = glob.glob(
        os.path.join(data_folder, "**/*.csv"),
        recursive=True
    )

    if not csv_files:
        raise FileNotFoundError("找不到任何 CSV 檔案")

    return csv_files


# =========================
# 主函式（給其他組員用）
# =========================
def load_and_clean_data(data_folder="data"):

    csv_files = load_all_csv(data_folder)

    all_data = []

    print(f"找到 {len(csv_files)} 個檔案")

    for file in csv_files:

        try:
            print(f"處理中: {os.path.basename(file)}")

            df = load_single_csv(file)

            clean_df = clean_dataframe(df)

            all_data.append(clean_df)

            print(f"成功: {len(clean_df)} 筆")

        except Exception as e:
            print(f"失敗: {file}")
            print(f"原因: {e}")

    if not all_data:
        raise ValueError("全部檔案都失敗")

    final_df = pd.concat(all_data, ignore_index=True)

    final_df = final_df.sort_values(
        ["SiteName", "Datetime", "Item"]
    )

    print("\n===== 完成 =====")
    print(f"總筆數: {len(final_df):,}")
    print(f"測站數: {final_df['SiteName'].nunique()}")
    print(f"測項數: {final_df['Item'].nunique()}")

    return final_df