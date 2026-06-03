import pandas as pd
import numpy as np

# =========================================================================
# 老師驗收專用參數區（可隨時修改，現場拉動這兩個參數，圖表就會連動！）
# =========================================================================
AQI_THRESHOLD = 100  # 超標門檻 (老師若要求改 150，現場改這裡)
GOOD_THRESHOLD = 50  # 良好門檻

# 次要問題二：測站型態分類定義
STATION_TYPES = {
    '工業區': ['小港', '林園', '大寮', '仁武', '前鎮', '復興', '楠梓'],
    '郊區': ['美濃', '恆春', '潮州', '橋頭']
}

# =========================================================================
# 1. 模擬數據函式（免等組員 A 的 Parser，直接開發演算法）
# =========================================================================
def get_mock_data():
    """模擬組員 A 傳過來的乾淨資料格式"""
    mock_dict = {
        '日期': ['2025-01-01 00:00', '2025-01-01 00:00', '2025-01-01 01:00', '2025-01-01 01:00',
                 '2025-01-01 00:00', '2025-01-01 00:00', '2025-01-01 01:00', '2025-01-01 01:00',
                 '2025-01-01 00:00', '2025-01-01 01:00'],
        '站點': ['小港', '小港', '小港', '小港', '恆春', '恆春', '恆春', '恆春', '左營', '左營'],
        '測項': ['PM2.5', 'O3', 'PM2.5', 'O3', 'PM2.5', 'O3', 'PM2.5', 'O3', 'PM2.5', 'PM2.5'],
        '數值': [35.4, 120.0, 40.2, 105.0, 5.2, 35.0, 6.1, 40.0, 22.1, 85.0]
    }
    return pd.DataFrame(mock_dict)

# =========================================================================
# 2. 資料結構轉置（把直立的測項揉成橫向欄位，方便算 AQI）
# =========================================================================
def process_data_structure(df):
    """將直立式資料進行樞紐轉置，讓 PM2.5 和 O3 變成獨立欄位"""
    pivoted = df.pivot_table(index=['日期', '站點'], columns='測項', values='數值').reset_index()
    
    # 用 PM2.5 來當作 AQI 趨勢的簡化代理計算（扣住主要問題的參數）
    pivoted['AQI'] = pivoted['PM2.5'] * 2.5  
    return pivoted

# =========================================================================
# 3. 主要問題演算法（計算超標率與良好率，並找出 Top 5）
# =========================================================================
def analyze_air_quality(df):
    """核心主要問題演算法：計算超標率與良好率，並找出 Top 5"""
    # 算出每個站點的總有效觀測小時數（呼應次要問題一：確保公平性）
    station_total_hours = df.groupby('站點').size()
    
    # 算出每個站點「AQI 超標」與「良好」的小時數
    exceed_hours = df[df['AQI'] > AQI_THRESHOLD].groupby('站點').size()
    good_hours = df[df['AQI'] <= GOOD_THRESHOLD].groupby('站點').size()
    
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
# 4. 次要問題二演算法（分類「工業區 vs 郊區」）
# =========================================================================
def classify_stations_and_compare(df):
    """將測站依型態分類，並計算不同型態的平均 PM2.5 濃度對比"""
    def get_type(station_name):
        if station_name in STATION_TYPES['工業區']:
            return '工業區'
        elif station_name in STATION_TYPES['郊區']:
            return '郊區'
        else:
            return '一般住宅區'
            
    df['站點型態'] = df['站點'].apply(get_type)
    type_comparison = df.groupby('站點型態')['PM2.5'].mean().round(2).to_frame(name='平均PM2.5')
    return type_comparison, df

# =========================================================================
# 5. 本地端測試獨立執行區（按右上角播放鍵就會跑這裡）
# =========================================================================
if __name__ == '__main__':
    print("=========================================")
    print("🤖 執行組員 B 的 Logic 模組獨立測試成功！")
    print("=========================================\n")
    
    # 跑流程
    raw_mock = get_mock_data()
    pivoted_mock = process_data_structure(raw_mock)
    worst_5, best_5 = analyze_air_quality(pivoted_mock)
    comparison, final_df = classify_stations_and_compare(pivoted_mock)
    
    # 印出結果
    print("【主要問題測試】AQI 超標率最高（最差）Top 5 站點：")
    print(worst_5[['總時數', '超標時數', '超標率(%)']])
    print("-" * 50)
    print("【主要問題測試】AQI 良好率最高（最好）Top 5 站點：")
    print(best_5[['總時數', '良好時數', '良好率(%)']])
    print("-" * 50)
    print("【次要問題二測試】工業區 vs 郊區之平均 PM2.5 對比：")
    print(comparison)