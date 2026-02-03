import json
import os
import matplotlib.pyplot as plt
import pandas as pd
import glob
from wordcloud import WordCloud
from datetime import datetime


# 僅用於趨勢圖顯示的映射，解決 GitHub Actions 環境下的中文亂碼問題
DISPLAY_LABELS = {
    "语言模型": "Language Models",
    "多模态模型": "Multimodal",
    "图像生成": "Image Generation",
    "视频生成": "Video Generation",
    "语音合成": "TTS",
    "语音识别": "ASR",
    "文档理解": "Document AI",
    "嵌入模型": "Embedding",
    "图像理解": "Computer Vision",
    "其他": "Others"
}

# 技術類別顏色映射
CATEGORY_COLORS = {
    "Language Models": "#FF6B6B",
    "Multimodal": "#4ECDC4",
    "Image Generation": "#45B7D1",
    "Video Generation": "#96CEB4",
    "TTS": "#FFEAA7",
    "ASR": "#DDA0DD",
    "Document AI": "#98D8C8",
    "Embedding": "#F7DC6F",
    "Computer Vision": "#BB8FCE",
    "Others": "#85C1E9"
}


def generate_charts(data_file):
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    date_str = data['date']
    stats = data['statistics']
    all_models = data.get('trending_models', [])
    
    # --- 1. 保留原始：Top Models Leaderboard ---
    top_models = all_models[:10]
    if top_models:
        names = [m['id'].split('/')[-1] for m in top_models]
        downloads = [m.get('downloads', 0) for m in top_models]
        likes = [m.get('likes', 0) for m in top_models]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
        ax1.barh(names[::-1], downloads[::-1], color='skyblue')
        ax1.set_title('Top Models by Downloads')
        ax2.barh(names[::-1], likes[::-1], color='lightcoral')
        ax2.set_title('Top Models by Likes')
        plt.tight_layout()
        plt.savefig(f'top_models_{date_str}.png')
        plt.close()


    # --- 2. 保留原始：Tech Distribution (Pie & Bar) ---
    dist = stats.get('tech_distribution', {})
    if dist:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
        ax1.pie(dist.values(), labels=dist.keys(), autopct='%1.1f%%', colors=plt.cm.Paired.colors)
        ax1.set_title('Tech Distribution (Pie)')
        ax2.bar(dist.keys(), dist.values(), color=plt.cm.Set3.colors)
        ax2.set_title('Tech Distribution (Bar)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'tech_dist_{date_str}.png')
        plt.close()


    # --- 3. 【修改】模型新鮮度 vs 熱度圖表 (替換原氣泡圖) ---
    if all_models:
        generate_freshness_chart(all_models, date_str)


    # --- 4. 保留原始：Active Organizations Ranking ---
    orgs = stats.get('top_organizations', {})
    if orgs:
        df_org = pd.DataFrame(list(orgs.items()), columns=['Organization', 'Count']).sort_values('Count', ascending=True)
        plt.figure(figsize=(10, 8))
        plt.barh(df_org['Organization'], df_org['Count'], color='teal')
        plt.title(f'Active Organizations - {date_str}')
        plt.tight_layout()
        plt.savefig(f'org_ranking_{date_str}.png')
        plt.close()


    # --- 5. 新增：生成詞雲 (Word Cloud) ---
    text = " ".join([m.get('id', '').split('/')[-1] for m in all_models])
    if text:
        wordcloud = WordCloud(width=1200, height=600, background_color='white', 
                              colormap='viridis', max_words=100).generate(text)
        plt.figure(figsize=(15, 7.5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'Hugging Face Tech Keywords - {date_str}', fontsize=20)
        plt.tight_layout(pad=0)
        plt.savefig(f'wordcloud_{date_str}.png')
        plt.close()
    
    # --- 6. 新增：趨勢分析圖 ---
    generate_trend_chart(date_str)


def generate_freshness_chart(all_models, date_str):
    """
    生成「模型新鮮度 vs 熱度」圖表
    X 軸：模型創建時間（天數，相對於今天）
    Y 軸：Likes 數量（熱度）
    氣泡大小：Downloads 數量
    顏色：技術類別
    """
    from datetime import datetime, timezone
    
    today = datetime.now(timezone.utc)
    
    # 準備數據
    chart_data = []
    for m in all_models:
        created_at = m.get('created_at') or m.get('lastModified')
        if not created_at:
            continue
        
        try:
            # 解析創建時間
            if isinstance(created_at, str):
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                continue
            
            # 計算天數差（新鮮度）
            days_old = (today - created_date).days
            if days_old < 0:
                days_old = 0
            
            # 獲取技術類別
            tech_cat = m.get('tech_category', '其他')
            tech_cat_en = DISPLAY_LABELS.get(tech_cat, 'Others')
            
            chart_data.append({
                'name': m['id'].split('/')[-1][:20],  # 截斷長名稱
                'days_old': days_old,
                'likes': m.get('likes', 0),
                'downloads': m.get('downloads', 0),
                'category': tech_cat_en,
                'full_name': m['id']
            })
        except Exception as e:
            continue
    
    if not chart_data:
        return
    
    df = pd.DataFrame(chart_data)
    
    # 過濾掉異常數據
    df = df[df['days_old'] <= 365]  # 只顯示一年內的模型
    df = df[df['likes'] > 0]  # 只顯示有 likes 的模型
    
    if df.empty:
        return
    
    # 創建圖表
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # 按類別繪製散點
    categories = df['category'].unique()
    for cat in categories:
        cat_df = df[df['category'] == cat]
        color = CATEGORY_COLORS.get(cat, '#85C1E9')
        
        # 氣泡大小基於 downloads，設置最小和最大值
        sizes = cat_df['downloads'].apply(lambda x: max(50, min(x / 500, 2000)))
        
        ax.scatter(
            cat_df['days_old'],
            cat_df['likes'],
            s=sizes,
            c=color,
            alpha=0.6,
            label=cat,
            edgecolors='white',
            linewidth=0.5
        )
    
    # 標註 Top 10 熱門模型名稱
    top_10 = df.nlargest(10, 'likes')
    for _, row in top_10.iterrows():
        ax.annotate(
            row['name'],
            (row['days_old'], row['likes']),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=8,
            alpha=0.8,
            fontweight='bold'
        )
    
    # 設置軸標籤和標題
    ax.set_xlabel('Model Age (Days Since Creation)', fontsize=12)
    ax.set_ylabel('Likes (Popularity)', fontsize=12)
    ax.set_title(f'Model Freshness vs Popularity - {date_str}\n(Bubble Size = Downloads)', fontsize=14, fontweight='bold')
    
    # 反轉 X 軸，讓新模型在左邊
    ax.invert_xaxis()
    
    # 設置對數刻度（如果數據範圍大）
    if df['likes'].max() > 1000:
        ax.set_yscale('log')
    
    # 添加圖例
    ax.legend(title='Tech Category', loc='upper right', fontsize=9)
    
    # 添加網格
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # 添加說明文字
    ax.text(
        0.02, 0.02,
        'Left = Newer Models | Right = Older Models\nBubble Size = Download Count',
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='bottom',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.tight_layout()
    plt.savefig(f'freshness_chart_{date_str}.png', dpi=150)
    plt.close()


def generate_trend_chart(current_date):
    files = sorted(glob.glob("hf_data_*.json"))
    if len(files) > 30:
        files = files[-30:]
        
    history = []
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as j:
                d = json.load(j)
                date = d['date']
                dist = d['statistics'].get('tech_distribution', {})
                # 僅在趨勢圖中使用英文映射解決亂碼
                plot_dist = {DISPLAY_LABELS.get(k, k): v for k, v in dist.items()}
                plot_dist['date'] = date
                history.append(plot_dist)
        except Exception as e:
            print(f"Error reading {f}: {e}")
    
    if len(history) > 1:
        df = pd.DataFrame(history).set_index('date').fillna(0)
        plt.figure(figsize=(12, 6))
        df.plot(kind='line', marker='o', ax=plt.gca())
        plt.title('Technology Trend Analysis (Last 30 Days)')
        plt.ylabel('Model Count')
        plt.xlabel('Date')
        plt.legend(title="Categories", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f'trend_chart_{current_date}.png')
        plt.close()


if __name__ == "__main__":
    latest_file = "latest.json"
    if os.path.exists(latest_file):
        generate_charts(latest_file)
