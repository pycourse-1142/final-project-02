# 匯入組員 A 的 Parser 模組
from parser import load_and_clean_data

# 匯入組員 B 的 Logic 模組
from logic import (
    process_data_structure,
    analyze_air_quality,
    classify_stations_and_compare
)

# 匯入自己負責的 Plotter 模組
from plotter import create_all_plots


def main():

    # =========================
    # Step1 讀取並清洗資料
    # =========================

    print("開始讀取資料...")

    raw_df = load_and_clean_data(
        data_folder="高屏空品區_2025"
    )

    print("資料清洗完成")

    # =========================
    # Step2 將資料轉換成分析格式
    # =========================

    pivoted_df = process_data_structure(raw_df)

    print("AQI 計算完成")

    # =========================
    # Step3 計算超標率與良好率
    # =========================

    worst_5, best_5 = analyze_air_quality(
        pivoted_df
    )

    print("Top5 排序完成")

    # =========================
    # Step4 工業區與郊區分類
    # =========================

    comparison, hourly_trend = (
        classify_stations_and_compare(
            pivoted_df
        )
    )

    print("型態分類完成")

    # =========================
    # Step5 建立站點型態欄位
    # 散佈圖需要使用
    # =========================

    type_map = {}

    for station in pivoted_df["SiteName"].unique():

        # 工業區測站
        if station in [
            '小港',
            '林園',
            '大寮',
            '仁武',
            '前鎮',
            '復興',
            '楠梓'
        ]:
            type_map[station] = "工業區"

        # 郊區測站
        elif station in [
            '美濃',
            '恆春',
            '潮州',
            '橋頭'
        ]:
            type_map[station] = "郊區"

        # 其他測站
        else:
            type_map[station] = "一般住宅區"

    # 新增型態欄位
    pivoted_df["站點型態"] = (
        pivoted_df["SiteName"]
        .map(type_map)
    )

    # =========================
    # Step6 輸出圖表
    # =========================

    create_all_plots(
        pivoted_df,
        worst_5,
        best_5,
        hourly_trend,
        results_dir="results"
    )

    print("專題執行完成")


# 主程式入口
if __name__ == "__main__":
    main()