import pandas as pd
import numpy as np

# =========================================================================
# 老師驗收專用參數區（可隨時修改，現場拉動這兩個參數，圖表就會連動！）
# =========================================================================
AQI_THRESHOLD = 100  # 超標門檻 (老師若要求改 150，現場改這裡)
GOOD_THRESHOLD = 50  # 良好門檻

# 次要問題二：測站型態分類定義（配合組員 A 清洗後的測站名稱）
STATION_TYPES = {
    '工業區': ['小港', '林園', '大寮', '仁武', '前鎮', '復興', '楠梓'],
    '郊區': ['美濃', '恆春', '潮州', '橋頭']
}

# =========================================================================
# 資料結構轉置（配合組員 A 的英文欄位：SiteName, Datetime, Item, Value）
# =========================================================================
def process_data_structure(df):
    """將 Parser 給的直立式資料進行樞紐轉置，讓 PM2.5 和 O3 變成獨立欄位"""
    # 💡 呼應組員 A 的英文欄位：index 用 Datetime 和 SiteName，columns 用 Item
    pivoted = df.pivot_table(index=['Datetime', 'SiteName'], columns='Item', values='Value').reset_index()
    
    # 檢查有沒有我們需要的測項，沒有的話給空值避免程式崩潰
    if 'PM2.5' not in pivoted.columns:
        pivoted['PM2.5'] = np.nan
        
    # 用 PM2.5 來當作 AQI 趨勢的簡化代理計算（扣住主要問題的參數）
    pivoted['AQI'] = pivoted['PM2.5'] * 2.5  
    return pivoted

# =========================================================================
# 主要問題演算法（計算超標率與良好率，並找出 Top 5）
# =========================================================================
def analyze_air_quality(df):
    """核心主要問題演算法：計算超標率與良好率，並找出 Top 5"""
    # 算出每個站點的總有效觀測小時數（呼應次要問題一：確保公平性）
    station_total_hours = df.groupby('SiteName').size()
    
    # 算出每個站點「AQI 超標」與「良好」的小時數
    exceed_hours = df[df['AQI'] > AQI_THRESHOLD].groupby('SiteName').size()
    good_hours = df[df['AQI'] <= GOOD_THRESHOLD].groupby('SiteName').size()
    
    # 建立統計結果 DataFrame
    stats_df = pd.DataFrame(index=station_total_hours.index)
    stats_df['總時數'] = station_total_hours
    stats_df['超標時數'] = exceed_hours.reindex(stats_df.index, fill_value=0)
    stats_df['良好時數'] = good_hours.reindex(stats_df.index, fill_value=0)
    
    # 計算百分比 (%)
    stats_df['超標率(%)'] = (stats_df['超標時數'] / stats_df['總時數'] * 100).round(2)
    stats_df['良好率(%)'] = (stats_df['良好時數'] / stats_df['總時數'] * 100).round(2)
    
    # 排序出 Top 5
    top5_worst = stats_df.sort_values(by='超標率(%)', ascending=False).head(5)
    top5_best = stats_df.sort_values(by='良好率(%)', ascending=False).head(5)
    
    return top5_worst, top5_best

# =========================================================================
# 次要問題二演算法（過濾住宅區，只留工業區 vs 郊區，並算好 24H 趨勢）
# =========================================================================
def classify_stations_and_compare(df):
    """將測站依型態分類，剔除一般住宅區，並計算工業區與郊區 24 小時 PM2.5 濃度變化數據"""
    def get_type(station_name):
        if station_name in STATION_TYPES['工業區']:
            return '工業區'
        elif station_name in STATION_TYPES['郊區']:
            return '郊區'
        else:
            return '一般住宅區'
            
    # 1. 貼上型態標籤
    df['站點型態'] = df['SiteName'].apply(get_type)
    
    # 2. 💡 聚焦核心：直接把「一般住宅區」剔除，只留下工業區與郊區！
    filtered_df = df[df['站點型態'].isin(['工業區', '郊區'])].copy()
    
    # 3. 提取小時（從 Datetime 欄位抓出 00~23 的整數小時）
    filtered_df['Hour'] = filtered_df['Datetime'].dt.hour
    
    # 4. 💡 核心計算：依據「站點型態」和「Hour」分組計算 PM2.5 平均值，並排成 24 小時交叉表格
    if 'PM2.5' in filtered_df.columns:
        hourly_trend = filtered_df.groupby(['站點型態', 'Hour'])['PM2.5'].mean().unstack(level=0).round(2)
        type_comparison = filtered_df.groupby('站點型態')['PM2.5'].mean().round(2).to_frame(name='平均PM2.5')
    else:
        hourly_trend = pd.DataFrame()
        type_comparison = pd.DataFrame()
        
    return type_comparison, hourly_trend

# =========================================================================
# 5. 本地端測試獨立執行區（與組員 A 完美合流 + 折線圖數據計算版！）
# =========================================================================
if __name__ == '__main__':
    print("=========================================")
    print("🤖 執行組員 B 的 Logic 模組（真實數據測試）")
    print("=========================================\n")
    
    # 1. 引入組員 A 的 parser 模組
    import parser 
    
    # 💡 呼叫組員 A 寫的正確主函式名稱，去讀取你的資料夾
    try:
        raw_real = parser.load_and_clean_data(data_folder="高屏空品區_2025") 
        
        print("\n正在進行資料結構轉置與樞紐計算...")
        # 2. 結構轉置
        pivoted_real = process_data_structure(raw_real)
        
        print("正在計算 AQI 超標率與良好率 Top 5...")
        # 3. 跑主要問題（超標/良好率排序）
        worst_5, best_5 = analyze_air_quality(pivoted_real)
        
        print("正在進行工業區 vs 郊區之型態對比與 24H 趨勢運算...")
        # 4. 跑次要問題（工業區 vs 郊區對比 + 產生 24 小時趨勢數據）
        comparison, hourly_trend = classify_stations_and_compare(pivoted_real)
        
        # 5. 印出真實的統計結果！
        print("\n" + "="*50)
        print("【主要問題】2025 全年高屏區 AQI 超標率最高 Top 5 站點：")
        print(worst_5[['總時數', '超標時數', '超標率(%)']])
        print("-" * 50)
        print("【主要問題】2025 全年高屏區 AQI 良好率最高 Top 5 站點：")
        print(best_5[['總時數', '良好時數', '良好率(%)']])
        print("-" * 50)
        print("【次要問題二】工業區 vs 郊區之全年整體平均 PM2.5 對比：")
        print(comparison)
        print("-" * 50)
        print("【次要問題二】工業區 vs 郊區 24 小時 PM2.5 趨勢數據：")
        print(hourly_trend)
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 執行失敗，原因: {e}")
        print("💡 請確認專案目錄下是否有 '高屏空品區_2025' 資料夾，且裡面放了那些 CSV 檔案喔！")