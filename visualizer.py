#!/usr/bin/env python3
"""
Hugging Face 热门 AI 技术可视化脚本 (GitHub Actions 版本)
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from collections import Counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from wordcloud import WordCloud

# 配置路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_DIR = ROOT_DIR  # 输出到根目录

# 技术领域颜色
TECH_COLORS = {
    "语言模型": "#FF6B6B",
    "多模态模型": "#4ECDC4",
    "图像生成": "#45B7D1",
    "视频生成": "#96CEB4",
    "语音合成": "#FFEAA7",
    "语音识别": "#DDA0DD",
    "文档理解": "#98D8C8",
    "嵌入模型": "#F7DC6F",
    "图像理解": "#BB8FCE",
    "其他": "#AEB6BF"
}

def load_data() -> Optional[Dict]:
    filepath = os.path.join(DATA_DIR, "latest.json")
    if not os.path.exists(filepath):
        files = [f for f in os.listdir(DATA_DIR) if f.startswith("hf_data_") and f.endswith(".json")]
        if not files:
            return None
        filepath = os.path.join(DATA_DIR, sorted(files)[-1])
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_keywords(models: List[Dict]) -> Dict[str, int]:
    keywords = Counter()
    tech_terms = [
        "llm", "gpt", "bert", "transformer", "diffusion", "stable", "flux",
        "whisper", "llama", "mistral", "qwen", "gemma", "phi", "deepseek",
        "vision", "audio", "speech", "text", "image", "video", "multimodal",
        "ocr", "tts", "asr", "embedding", "rag", "agent", "chat", "instruct",
        "finetune", "lora", "gguf", "quantized", "7b", "8b", "13b", "70b",
        "flash", "turbo", "ultra", "pro", "base", "large", "small", "mini"
    ]
    
    for model in models:
        model_id = model.get("id", "")
        model_name = model_id.split("/")[-1].lower() if "/" in model_id else model_id.lower()
        
        words = re.findall(r'[a-zA-Z]+|\d+[bB]', model_name)
        for word in words:
            word_lower = word.lower()
            if len(word_lower) >= 2 and word_lower in tech_terms:
                keywords[word_lower] += 1
        
        pipeline_tag = model.get("pipeline_tag")
        if pipeline_tag:
            keywords[pipeline_tag.replace("-", " ")] += 1
        
        author = model.get("author")
        if author:
            keywords[author.lower()] += 1
    
    return dict(keywords)

def generate_wordcloud(data: Dict, date: str) -> str:
    print("正在生成词云...")
    all_models = data.get("trending_models", []) + data.get("most_downloaded", []) + data.get("most_liked", [])
    keywords = extract_keywords(all_models)
    
    if not keywords:
        return ""
    
    wordcloud = WordCloud(
        width=1200, height=600, background_color='white',
        colormap='viridis', max_words=100, min_font_size=10, max_font_size=120
    ).generate_from_frequencies(keywords)
    
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    ax.set_title(f'Hugging Face 热门技术词云 - {date}', fontsize=20, fontweight='bold', pad=20)
    
    output_path = os.path.join(OUTPUT_DIR, f"wordcloud_{date}.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  词云已保存到: {output_path}")
    return output_path

def generate_leaderboard(data: Dict, date: str) -> str:
    print("正在生成排行榜...")
    trending = data.get("trending_models", [])[:15]
    if not trending:
        return ""
    
    names = [m.get("id", "").split("/")[-1][:25] for m in trending]
    downloads = [m.get("downloads", 0) for m in trending]
    likes = [m.get("likes", 0) for m in trending]
    categories = [m.get("tech_category", "其他") for m in trending]
    colors = [TECH_COLORS.get(cat, TECH_COLORS["其他"]) for cat in categories]
    
    fig, axes = plt.subplots(1, 2, figsize=(18, 10))
    
    ax1 = axes[0]
    y_pos = np.arange(len(names))
    bars1 = ax1.barh(y_pos, downloads, color=colors)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(names, fontsize=10)
    ax1.invert_yaxis()
    ax1.set_xlabel('下载量', fontsize=12)
    ax1.set_title('热门模型下载量排行', fontsize=14, fontweight='bold')
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K' if x < 1e6 else f'{x/1e6:.1f}M'))
    
    for bar, val in zip(bars1, downloads):
        label = f'{val/1000:.1f}K' if val < 1e6 else f'{val/1e6:.2f}M'
        ax1.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f' {label}', va='center', fontsize=9)
    
    ax2 = axes[1]
    bars2 = ax2.barh(y_pos, likes, color=colors)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(names, fontsize=10)
    ax2.invert_yaxis()
    ax2.set_xlabel('点赞数', fontsize=12)
    ax2.set_title('热门模型点赞数排行', fontsize=14, fontweight='bold')
    
    for bar, val in zip(bars2, likes):
        ax2.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f' {val}', va='center', fontsize=9)
    
    unique_cats = list(set(categories))
    legend_handles = [plt.Rectangle((0,0),1,1, color=TECH_COLORS.get(cat, TECH_COLORS["其他"])) for cat in unique_cats]
    fig.legend(legend_handles, unique_cats, loc='upper center', ncol=min(5, len(unique_cats)), bbox_to_anchor=(0.5, 0.02))
    
    plt.suptitle(f'Hugging Face 热门模型排行榜 - {date}', fontsize=16, fontweight='bold', y=0.98)
    
    output_path = os.path.join(OUTPUT_DIR, f"leaderboard_{date}.png")
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  排行榜已保存到: {output_path}")
    return output_path

def generate_tech_distribution(data: Dict, date: str) -> str:
    print("正在生成技术分布图...")
    tech_dist = data.get("statistics", {}).get("tech_distribution", {})
    if not tech_dist:
        return ""
    
    labels = list(tech_dist.keys())
    sizes = list(tech_dist.values())
    colors = [TECH_COLORS.get(label, TECH_COLORS["其他"]) for label in labels]
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    ax1 = axes[0]
    ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax1.set_title('技术领域分布', fontsize=14, fontweight='bold')
    
    ax2 = axes[1]
    y_pos = np.arange(len(labels))
    bars = ax2.barh(y_pos, sizes, color=colors)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(labels, fontsize=11)
    ax2.invert_yaxis()
    ax2.set_xlabel('模型数量', fontsize=12)
    ax2.set_title('各技术领域模型数量', fontsize=14, fontweight='bold')
    
    for bar, val in zip(bars, sizes):
        ax2.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f' {val}', va='center', fontsize=10)
    
    plt.suptitle(f'Hugging Face 技术领域分布 - {date}', fontsize=16, fontweight='bold', y=0.98)
    
    output_path = os.path.join(OUTPUT_DIR, f"tech_distribution_{date}.png")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  技术分布图已保存到: {output_path}")
    return output_path

def generate_org_ranking(data: Dict, date: str) -> str:
    print("正在生成组织排行图...")
    org_dist = data.get("statistics", {}).get("top_organizations", {})
    if not org_dist:
        return ""
    
    sorted_orgs = sorted(org_dist.items(), key=lambda x: x[1], reverse=True)[:15]
    labels = [org for org, _ in sorted_orgs]
    values = [count for _, count in sorted_orgs]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    cmap = plt.cm.get_cmap('RdYlBu_r')
    colors = [cmap(i / len(labels)) for i in range(len(labels))]
    
    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel('热门模型数量', fontsize=12)
    ax.set_title(f'Hugging Face 活跃组织排行 - {date}', fontsize=16, fontweight='bold')
    
    for bar, val in zip(bars, values):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f' {val}', va='center', fontsize=10, fontweight='bold')
    
    output_path = os.path.join(OUTPUT_DIR, f"org_ranking_{date}.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  组织排行图已保存到: {output_path}")
    return output_path

def generate_bubble_chart(data: Dict, date: str) -> str:
    print("正在生成气泡图...")
    trending = data.get("trending_models", [])[:30]
    if not trending:
        return ""
    
    downloads = [m.get("downloads", 0) for m in trending]
    likes = [m.get("likes", 0) for m in trending]
    categories = [m.get("tech_category", "其他") for m in trending]
    names = [m.get("id", "").split("/")[-1][:15] for m in trending]
    colors = [TECH_COLORS.get(cat, TECH_COLORS["其他"]) for cat in categories]
    
    max_download = max(downloads) if downloads else 1
    sizes = [100 + (d / max_download) * 500 for d in downloads]
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    for i, (d, l, s, c, n) in enumerate(zip(downloads, likes, sizes, colors, names)):
        ax.scatter(d, l, s=s, c=c, alpha=0.6, edgecolors='white', linewidth=1)
        ax.annotate(n, (d, l), fontsize=7, alpha=0.8)
    
    ax.set_xlabel('下载量', fontsize=12)
    ax.set_ylabel('点赞数', fontsize=12)
    ax.set_title(f'Hugging Face 模型热度分布 - {date}', fontsize=16, fontweight='bold')
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K' if x < 1e6 else f'{x/1e6:.1f}M'))
    
    unique_cats = list(set(categories))
    legend_handles = [plt.scatter([], [], c=TECH_COLORS.get(cat, TECH_COLORS["其他"]), s=100, label=cat) for cat in unique_cats]
    ax.legend(handles=legend_handles, loc='upper left', fontsize=9)
    
    output_path = os.path.join(OUTPUT_DIR, f"bubble_chart_{date}.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  气泡图已保存到: {output_path}")
    return output_path

def generate_size_distribution(data: Dict, date: str) -> str:
    print("正在生成规模分布图...")
    size_dist = data.get("statistics", {}).get("size_distribution", {})
    if not size_dist:
        return ""
    
    order = ["微型 (<1B)", "小型 (1B-7B)", "中型 (7B-32B)", "大型 (32B-128B)", "超大型 (>128B)", "未知"]
    labels = [s for s in order if s in size_dist]
    sizes = [size_dist[s] for s in labels]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(labels)))
    bars = ax.bar(labels, sizes, color=colors, edgecolor='white', linewidth=1)
    
    for bar, val in zip(bars, sizes):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{val}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax.set_xlabel('模型规模', fontsize=12)
    ax.set_ylabel('模型数量', fontsize=12)
    ax.set_title(f'Hugging Face 模型规模分布 - {date}', fontsize=16, fontweight='bold')
    
    output_path = os.path.join(OUTPUT_DIR, f"size_distribution_{date}.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  规模分布图已保存到: {output_path}")
    return output_path

def main():
    data = load_data()
    if not data:
        print("没有找到数据文件")
        return
    
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    print(f"\n开始生成可视化 - {date}\n")
    
    generate_wordcloud(data, date)
    generate_leaderboard(data, date)
    generate_tech_distribution(data, date)
    generate_org_ranking(data, date)
    generate_bubble_chart(data, date)
    generate_size_distribution(data, date)
    
    print("\n所有可视化生成完成!")

if __name__ == "__main__":
    main()
