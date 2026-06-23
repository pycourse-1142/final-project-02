# ==========================================================
# plotter.py
# 圖表繪製模組
#
# 功能：
# 1. 接收 logic.py 分析完成的資料
# 2. 使用 matplotlib / seaborn 繪製四種統計圖
# 3. 將圖表自動儲存到 results/ 資料夾
# ==========================================================

import os
import matplotlib.pyplot as plt
import seaborn as sns


# ==========================================================
# 設定中文字型
# 避免圖表中的中文標題、座標軸出現亂碼
# ==========================================================
def setup_chinese_font():
    plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]
    plt.rcParams["axes.unicode_minus"] = False


# ==========================================================
# 圖表一：AQI 超標率 / 良好率 Top 5 排名圖
# 圖表類型：水平長條圖
# ==========================================================
def plot_top5(worst_5, best_5, results_dir):
    setup_chinese_font()

    # AQI 超標率最高 Top 5
    plt.figure(figsize=(10, 6))
    worst_5["超標率(%)"].iloc[::-1].plot(kind="barh", color="#e74c3c") 
    plt.title("AQI 超標率最高 Top 5 測站")
    plt.xlabel("超標率 (%)")
    plt.ylabel("測站")
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "01_top5_worst.png"), dpi=300)
    plt.close()

    # AQI 良好率最高 Top 5
    plt.figure(figsize=(10, 6))
    best_5["良好率(%)"].iloc[::-1].plot(kind="barh", color="#2ecc71")
    plt.title("AQI 良好率最高 Top 5 測站")
    plt.xlabel("良好率 (%)")
    plt.ylabel("測站")
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "02_top5_best.png"), dpi=300)
    plt.close()


# ==========================================================
# 圖表二：工業區 vs 郊區 24 小時 PM2.5 濃度變化
# 圖表類型：折線圖
# ==========================================================
def plot_hourly_pm25(hourly_trend, results_dir):
    setup_chinese_font()

    valid_cols = [col for col in ["工業區", "郊區"] if col in hourly_trend.columns]
    hourly_trend = hourly_trend[valid_cols]

    plt.figure(figsize=(12, 6))
    
    colors = {"工業區": "#1f77b4", "郊區": "#2ca02c"}
    for col in hourly_trend.columns:
        plt.plot(hourly_trend.index, hourly_trend[col], marker="o", label=col, color=colors.get(col))

    plt.title("工業區 vs 郊區 24 小時 PM2.5 濃度變化")
    plt.xlabel("小時")
    plt.ylabel("PM2.5 平均濃度")
    plt.xticks(range(0, 24))
    plt.grid(True)
    plt.legend(title="站點型態")
    plt.tight_layout()

    plt.savefig(os.path.join(results_dir, "03_hourly_pm25_trend.png"), dpi=300)
    plt.close()


# ==========================================================
# 圖表三：高屏區 AQI 與 PM2.5 相關性分析
# 圖表類型：散佈圖
# ==========================================================
def plot_aqi_pm25_scatter(df, results_dir):
    setup_chinese_font()

    df_filtered = df[df["站點型態"].isin(["工業區", "郊區"])].copy()

    plt.figure(figsize=(10, 6))

    sns.scatterplot(
        data=df_filtered,
        x="PM2.5",
        y="AQI",
        hue="站點型態",
        alpha=0.6,
        palette={"工業區": "#1f77b4", "郊區": "#2ca02c"}
    )

    plt.title("高屏區 AQI 與 PM2.5 相關性分析")
    plt.xlabel("PM2.5")
    plt.ylabel("AQI")
    plt.tight_layout()

    plt.savefig(os.path.join(results_dir, "04_aqi_pm25_scatter.png"), dpi=300)
    plt.close()


# ==========================================================
# 圖表四：AQI 等級月份變化圖
# 圖表類型：堆疊長條圖
# ==========================================================
def plot_monthly_aqi_level(df, results_dir):
    setup_chinese_font()

    df = df.copy()
    df["Month"] = df["Datetime"].dt.month

    def get_aqi_level(aqi):
        if aqi <= 50:
            return "良好"
        elif aqi <= 100:
            return "普通"
        elif aqi <= 150:
            return "對敏感族群不健康"
        elif aqi <= 200:
            return "對所有族群不健康"
        else:
            return "非常不健康"

    df["AQI等級"] = df["AQI"].apply(get_aqi_level)

    monthly_level = (
        df.groupby(["Month", "AQI等級"])
        .size()
        .unstack(fill_value=0)
    )

    level_order = ["良好", "普通", "對敏感族群不健康", "對所有族群不健康", "非常不健康"]
    exist_levels = [lvl for lvl in level_order if lvl in monthly_level.columns]
    monthly_level = monthly_level[exist_levels]

    color_map = {
        "良好": "#2ecc71",            # 綠色
        "普通": "#f1c40f",            # 黃色
        "對敏感族群不健康": "#e67e22",  # 橘色
        "對所有族群不健康": "#e74c3c",  # 紅色
        "非常不健康": "#9b59b6"         # 紫色
    }
    plot_colors = [color_map[lvl] for lvl in exist_levels]

    # 畫堆疊長條圖
    monthly_level.plot(
        kind="bar",
        stacked=True,
        figsize=(12, 6),
        color=plot_colors
    )

    plt.title("AQI 等級月份變化圖")
    plt.xlabel("月份")
    plt.ylabel("筆數")
    plt.legend(title="AQI等級", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    plt.savefig(os.path.join(results_dir, "05_monthly_aqi_level.png"), dpi=300)
    plt.close()


# ==========================================================
# 統一輸出所有圖表
# main.py 只需要呼叫這個函式即可
# ==========================================================
def create_all_plots(df, worst_5, best_5, hourly_trend, results_dir="results"):
    os.makedirs(results_dir, exist_ok=True)
    plot_top5(worst_5, best_5, results_dir)
    plot_hourly_pm25(hourly_trend, results_dir)
    plot_aqi_pm25_scatter(df, results_dir)
    plot_monthly_aqi_level(df, results_dir)
    print("四張圖表已輸出到 results/ 資料夾")
