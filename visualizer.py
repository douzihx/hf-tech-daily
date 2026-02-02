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

    # --- 3. 保留原始：Model Popularity Bubble Chart ---
    if all_models:
        df = pd.DataFrame(all_models)
        plt.figure(figsize=(12, 8))
        plt.scatter(df['downloads'], df['likes'], s=df['downloads']/1000, alpha=0.5, c=range(len(df)), cmap='viridis')
        plt.xlabel('Downloads')
        plt.ylabel('Likes')
        plt.title('Model Popularity Bubble Chart')
        plt.xscale('log')
        plt.yscale('log')
        plt.tight_layout()
        plt.savefig(f'bubble_chart_{date_str}.png')
        plt.close()

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
