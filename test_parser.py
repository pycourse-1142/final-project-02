from parser import load_and_clean_data

df = load_and_clean_data("高屏空品區_2025")

print(df.head())

print("\n資料筆數：", len(df))