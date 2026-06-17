# 資料處理套件
import pandas as pd

# 數值運算與 NaN 使用
import numpy as np

# 搜尋資料夾中的檔案
import glob

# 作業系統路徑操作
import os


# =========================
# 髒資料定義
# =========================
# 空氣品質資料中常見的無效值
# 後續會統一轉成 NaN
INVALID_VALUES = ["...", "-999", "NR", "#", "", " "]


# =========================
# 欄位檢查
# =========================
def validate_columns(df):
    """
    檢查資料是否包含必要欄位

    Parameters
    ----------
    df : pandas.DataFrame
        原始資料表

    Raises
    ------
    ValueError
        若缺少必要欄位則拋出錯誤
    """

    # 必要欄位
    required = ["測站", "日期", "測項"]

    # 找出缺少的欄位
    missing = [c for c in required if c not in df.columns]

    # 若有缺少欄位則停止執行
    if missing:
        raise ValueError(f"缺少必要欄位: {missing}")


# =========================
# 取得 00~23 欄位
# =========================
def get_hour_columns(df):
    """
    取得資料中的 00~23 小時欄位

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    list
        小時欄位清單

    Raises
    ------
    ValueError
        若小時欄位不完整則拋出錯誤
    """

    # 建立標準小時欄位名稱
    hour_cols = [f"{i:02d}" for i in range(24)]

    # 篩選實際存在的欄位
    exist_hours = [c for c in hour_cols if c in df.columns]

    # 檢查是否完整包含 24 小時
    if len(exist_hours) != 24:
        raise ValueError("缺少 00~23 小時欄位")

    return exist_hours


# =========================
# 單檔清理
# =========================
def clean_dataframe(df):
    """
    清理單一檔案資料

    流程：
    1. 驗證欄位
    2. 髒資料轉 NaN
    3. 轉換數值型態
    4. 寬表轉長表
    5. 建立 Datetime
    6. 欄位標準化
    7. 移除無效資料

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
        整理後資料
    """

    # 檢查必要欄位
    validate_columns(df)

    # 取得 00~23 欄位
    hour_cols = get_hour_columns(df)

    # 1️⃣ 將髒資料轉成 NaN
    df = df.replace(INVALID_VALUES, np.nan)

    # 2️⃣ 小時欄位轉成數值型態
    # 無法轉換的值自動變成 NaN
    df[hour_cols] = df[hour_cols].apply(
        pd.to_numeric,
        errors="coerce"
    )

    # 3️⃣ 寬表轉長表
    # 原本:
    # 日期 | 00 | 01 | 02 ...
    #
    # 轉成:
    # 日期 | Hour | Value
    df_long = pd.melt(
        df,
        id_vars=["測站", "日期", "測項"],
        value_vars=hour_cols,
        var_name="Hour",
        value_name="Value"
    )

    # 4️⃣ 合併日期與小時欄位
    # 建立完整時間 Datetime
    df_long["Datetime"] = pd.to_datetime(
        df_long["日期"].astype(str).str[:10]
        + " "
        + df_long["Hour"] + ":00:00",
        errors="coerce"
    )

    # 5️⃣ 欄位名稱標準化
    # 方便後續分析與英文命名統一
    df_long = df_long.rename(columns={
        "測站": "SiteName",
        "測項": "Item"
    })

    # 6️⃣ 移除時間或數值缺失資料
    df_long = df_long.dropna(subset=["Datetime", "Value"])

    # 回傳標準格式資料
    return df_long[["SiteName", "Datetime", "Item", "Value"]]


# =========================
# 讀單一 CSV
# =========================
def load_single_csv(file_path):
    """
    讀取單一 CSV 檔案

    優先使用 UTF-8，
    若失敗則改用 Big5

    Parameters
    ----------
    file_path : str

    Returns
    -------
    pandas.DataFrame
    """

    try:
        return pd.read_csv(file_path, encoding="utf-8")

    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding="big5")


# =========================
# 讀所有 CSV（支援子資料夾）
# =========================
def load_all_csv(data_folder):
    """
    搜尋指定資料夾內所有 CSV

    支援遞迴搜尋子資料夾

    Parameters
    ----------
    data_folder : str

    Returns
    -------
    list
        CSV 檔案路徑清單
    """

    csv_files = glob.glob(
        os.path.join(data_folder, "**/*.csv"),
        recursive=True
    )

    # 若找不到檔案則停止
    if not csv_files:
        raise FileNotFoundError("找不到任何 CSV 檔案")

    return csv_files


# =========================
# 主函式（給其他組員用）
# =========================
def load_and_clean_data(data_folder="data"):
    """
    讀取資料夾中所有 CSV 並完成清理

    Parameters
    ----------
    data_folder : str
        資料夾路徑

    Returns
    -------
    pandas.DataFrame
        合併後乾淨資料
    """

    # 取得所有 CSV
    csv_files = load_all_csv(data_folder)

    # 儲存各檔案清理結果
    all_data = []

    print(f"找到 {len(csv_files)} 個檔案")

    # 逐一處理每個 CSV
    for file in csv_files:

        try:
            print(f"處理中: {os.path.basename(file)}")

            # 讀取檔案
            df = load_single_csv(file)

            # 清理資料
            clean_df = clean_dataframe(df)

            # 加入總資料集
            all_data.append(clean_df)

            print(f"成功: {len(clean_df)} 筆")

        except Exception as e:

            # 單一檔案失敗不影響其他檔案
            print(f"失敗: {file}")
            print(f"原因: {e}")

    # 若全部檔案都失敗
    if not all_data:
        raise ValueError("全部檔案都失敗")

    # 合併所有資料
    final_df = pd.concat(
        all_data,
        ignore_index=True
    )

    # 排序資料
    final_df = final_df.sort_values(
        ["SiteName", "Datetime", "Item"]
    )

    # 顯示統計資訊
    print("\n===== 完成 =====")
    print(f"總筆數: {len(final_df):,}")
    print(f"測站數: {final_df['SiteName'].nunique()}")
    print(f"測項數: {final_df['Item'].nunique()}")

    return final_df