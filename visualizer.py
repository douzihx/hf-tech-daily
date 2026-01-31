import json
import os
import matplotlib.pyplot as plt
import pandas as pd
import glob
from datetime import datetime

def generate_charts(data_file):
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    date_str = data['date']
    stats = data['statistics']
    
    # 1. 组织排行图
    orgs = stats['top_organizations']
    df_org = pd.DataFrame(list(orgs.items()), columns=['Organization', 'Count']).sort_values('Count', ascending=True)
    plt.figure(figsize=(10, 6))
    plt.barh(df_org['Organization'], df_org['Count'], color='skyblue')
    plt.title(f'Hugging Face Active Organizations - {date_str}')
    plt.tight_layout()
    plt.savefig(f'org_ranking_{date_str}.png')
    
    # 2. 趋势分析图 (新增)
    generate_trend_chart(date_str)

def generate_trend_chart(current_date):
    files = sorted(glob.glob("hf_data_*.json"))[-30:] # 获取最近30天数据
    history = []
    for f in files:
        with open(f, 'r') as j:
            d = json.load(j)
            date = d['date']
            dist = d['statistics'].get('tech_distribution', {})
            dist['date'] = date
            history.append(dist)
    
    if len(history) > 1:
        df = pd.DataFrame(history).set_index('date').fillna(0)
        plt.figure(figsize=(12, 6))
        df.plot(kind='line', marker='o', ax=plt.gca())
        plt.title('Technology Trend Analysis (Last 30 Days)')
        plt.ylabel('Model Count')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f'trend_chart_{current_date}.png')

if __name__ == "__main__":
    latest_file = "latest.json"
    if os.path.exists(latest_file):
        generate_charts(latest_file)
