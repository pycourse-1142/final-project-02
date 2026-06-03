import pandas as pd
import numpy as np
import glob
import os


INVALID_VALUES = [
    "...",
    "-999",
    "NR",
    "#",
    "",
    " "
]


def validate_columns(df):

    required_cols = [
        "測站",
        "日期",
        "測項"
    ]

    missing = []

    for col in required_cols:
        if col not in df.columns:
            missing.append(col)

    if missing:
        raise ValueError(
            f"缺少必要欄位: {missing}"
        )


def get_hour_columns(df):

    hour_cols = []

    for i in range(24):

        col = f"{i:02d}"

        if col in df.columns:
            hour_cols.append(col)

    if len(hour_cols) != 24:
        raise ValueError(
            "00~23 小時欄位不完整"
        )

    return hour_cols


def clean_dataframe(df):

    validate_columns(df)

    hour_cols = get_hour_columns(df)

    df = df.replace(
        INVALID_VALUES,
        np.nan
    )

    df[hour_cols] = df[hour_cols].apply(
        pd.to_numeric,
        errors="coerce"
    )

    df_long = pd.melt(
        df,
        id_vars=[
            "測站",
            "日期",
            "測項"
        ],
        value_vars=hour_cols,
        var_name="Hour",
        value_name="Value"
    )

    df_long["Datetime"] = pd.to_datetime(
        df_long["日期"].astype(str)
        .str[:10]
        + " "
        + df_long["Hour"]
        + ":00:00",
        errors="coerce"
    )

    df_long = df_long.rename(
        columns={
            "測站": "SiteName",
            "測項": "Item"
        }
    )

    df_long = df_long.dropna(
        subset=[
            "Datetime",
            "Value"
        ]
    )

    df_long = df_long[
        [
            "SiteName",
            "Datetime",
            "Item",
            "Value"
        ]
    ]

    return df_long


def load_single_csv(file_path):

    try:

        return pd.read_csv(
            file_path,
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        return pd.read_csv(
            file_path,
            encoding="big5"
        )


def load_and_clean_data(data_folder="data"):

    csv_files = glob.glob(
        os.path.join(
            data_folder,
            "*.csv"
        )
    )

    if len(csv_files) == 0:

        raise FileNotFoundError(
            "找不到 CSV 檔案"
        )

    all_data = []

    for file in csv_files:

        try:

            print(
                f"讀取中: {os.path.basename(file)}"
            )

            raw_df = load_single_csv(file)

            clean_df = clean_dataframe(
                raw_df
            )

            all_data.append(
                clean_df
            )

            print(
                f"成功 {len(clean_df)} 筆"
            )

        except Exception as e:

            print(
                f"失敗: {file}"
            )

            print(e)

    if len(all_data) == 0:

        raise ValueError(
            "所有檔案處理失敗"
        )

    final_df = pd.concat(
        all_data,
        ignore_index=True
    )

    final_df = final_df.sort_values(
        [
            "SiteName",
            "Datetime",
            "Item"
        ]
    )

    print("\n=== Parser 完成 ===")
    print(
        f"總筆數: {len(final_df):,}"
    )

    return final_df