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
    
    # 修正：.iloc[::-1] 把資料列由後往前倒序，這樣畫出來最上面就會是第一名！
    worst_5["超標率(%)"].iloc[::-1].plot(kind="barh", color="#e74c3c") 
    
    plt.title("AQI 超標率最高 Top 5 測站")
    plt.xlabel("超標率 (%)")
    plt.ylabel("測站")
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "01_top5_worst.png"), dpi=300)
    plt.close()

    # AQI 良好率最高 Top 5
    plt.figure(figsize=(10, 6))
    
    # 修正：同樣加上 .iloc[::-1]
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
    plt.legend(title="站點型態")  # 顯示乾淨的圖例
    plt.tight_layout()

    plt.savefig(os.path.join(results_dir, "03_hourly_pm25_trend.png"), dpi=300)
    plt.close()


# ==========================================================
# 圖表三：高屏區 AQI 與 PM2.5 相關性分析
# 圖表類型：散佈圖
# hue="站點型態" 讓不同測站類型用不同顏色呈現
# ==========================================================
def plot_aqi_pm25_scatter(df, results_dir):
    setup_chinese_font()

    plt.figure(figsize=(10, 6))

    sns.scatterplot(
        data=df,
        x="PM2.5",
        y="AQI",
        hue="站點型態",
        alpha=0.6
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

    # copy 一份資料，避免直接改到 main.py 傳進來的原始 DataFrame
    df = df.copy()

    # 從 Datetime 欄位取出月份
    df["Month"] = df["Datetime"].dt.month

    # 依 AQI 數值分類成不同等級
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

    # 新增 AQI 等級欄位
    df["AQI等級"] = df["AQI"].apply(get_aqi_level)

    # 依月份與 AQI 等級統計筆數
    monthly_level = (
        df.groupby(["Month", "AQI等級"])
        .size()
        .unstack(fill_value=0)
    )

    # 畫堆疊長條圖
    monthly_level.plot(
        kind="bar",
        stacked=True,
        figsize=(12, 6)
    )

    plt.title("AQI 等級月份變化圖")
    plt.xlabel("月份")
    plt.ylabel("筆數")
    plt.tight_layout()

    plt.savefig(os.path.join(results_dir, "05_monthly_aqi_level.png"), dpi=300)
    plt.close()


# ==========================================================
# 統一輸出所有圖表
# main.py 只需要呼叫這個函式即可
# ==========================================================
def create_all_plots(df, worst_5, best_5, hourly_trend, results_dir="results"):

    # 如果 results/ 不存在，就自動建立
    os.makedirs(results_dir, exist_ok=True)

    # 圖表一：Top 5 排名圖
    plot_top5(worst_5, best_5, results_dir)

    # 圖表二：24 小時 PM2.5 折線圖
    plot_hourly_pm25(hourly_trend, results_dir)

    # 圖表三：AQI 與 PM2.5 散佈圖
    plot_aqi_pm25_scatter(df, results_dir)

    # 圖表四：AQI 等級月份堆疊圖
    plot_monthly_aqi_level(df, results_dir)

    print("四張圖表已輸出到 results/ 資料夾")
