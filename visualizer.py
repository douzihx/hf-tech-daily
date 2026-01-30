#!/usr/bin/env python3
"""
Hugging Face Hot AI Tech Visualizer
Generate wordcloud, leaderboard, trend charts
Adapted for GitHub Actions environment
Fixed: Use English titles to avoid font issues
"""

import json
import os
import re
import glob
from datetime import datetime
from typing import Dict, List, Optional
from collections import Counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from wordcloud import WordCloud

# Use default font (no Chinese font needed)
plt.rcParams['axes.unicode_minus'] = False

# Config - GitHub Actions environment
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = SCRIPT_DIR
OUTPUT_DIR = SCRIPT_DIR

# Color scheme
COLORS = {
    "primary": "#FF6B35",
    "secondary": "#004E89",
    "accent": "#00A896",
    "background": "#F8F9FA",
    "text": "#2D3436"
}

# Tech category colors
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

# English category names for display
TECH_NAMES_EN = {
    "语言模型": "Language Model",
    "多模态模型": "Multimodal",
    "图像生成": "Image Gen",
    "视频生成": "Video Gen",
    "语音合成": "TTS",
    "语音识别": "ASR",
    "文档理解": "Doc Understanding",
    "嵌入模型": "Embedding",
    "图像理解": "Image Understanding",
    "其他": "Other"
}

def load_data(date: Optional[str] = None) -> Optional[Dict]:
    """Load data file - support multiple filename formats"""
    print(f"Looking for data files...")
    print(f"  Script dir: {SCRIPT_DIR}")
    print(f"  Data dir: {DATA_DIR}")
    
    all_files = os.listdir(DATA_DIR)
    print(f"  Files in directory: {all_files}")
    
    # Try multiple filename patterns
    patterns = [
        "data_*.json",
        "hf_data_*.json",
        "latest.json"
    ]
    
    data_files = []
    for pattern in patterns:
        matches = glob.glob(os.path.join(DATA_DIR, pattern))
        data_files.extend(matches)
    
    print(f"  Found data files: {data_files}")
    
    if not data_files:
        print("  No data files found!")
        return None
    
    # Use the latest file
    latest_file = sorted(data_files)[-1]
    print(f"  Using data file: {latest_file}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_keywords(models: List[Dict]) -> Dict[str, int]:
    """Extract keywords from model names and tags"""
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

def generate_wordcloud(data: Dict, output_path: str) -> str:
    """Generate word cloud"""
    print("Generating word cloud...")
    
    all_models = (
        data.get("trending_models", []) +
        data.get("most_downloaded", []) +
        data.get("most_liked", [])
    )
    
    keywords = extract_keywords(all_models)
    
    if not keywords:
        print("  Not enough keywords for word cloud")
        return ""
    
    wordcloud = WordCloud(
        width=1200,
        height=600,
        background_color='white',
        colormap='viridis',
        max_words=100,
        min_font_size=10,
        max_font_size=120,
        prefer_horizontal=0.7
    ).generate_from_frequencies(keywords)
    
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    ax.set_title(f'Hugging Face Tech Keywords - {data.get("date", "")}', 
                 fontsize=18, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  Word cloud saved to: {output_path}")
    return output_path

def generate_leaderboard(data: Dict, output_path: str) -> str:
    """Generate leaderboard chart"""
    print("Generating leaderboard...")
    
    trending = data.get("trending_models", [])[:10]
    
    if not trending:
        print("  No trending models data")
        return ""
    
    names = [m.get("id", "").split("/")[-1][:25] for m in trending]
    downloads = [m.get("downloads", 0) for m in trending]
    likes = [m.get("likes", 0) for m in trending]
    categories = [m.get("tech_category", "Other") for m in trending]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Downloads chart
    colors1 = [TECH_COLORS.get(cat, TECH_COLORS["其他"]) for cat in categories]
    y_pos = np.arange(len(names))
    bars1 = ax1.barh(y_pos, downloads, color=colors1, edgecolor='white', linewidth=0.5)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(names, fontsize=10)
    ax1.invert_yaxis()
    ax1.set_xlabel('Downloads', fontsize=12)
    ax1.set_title('Top Models by Downloads', fontsize=14, fontweight='bold')
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K' if x < 1e6 else f'{x/1e6:.1f}M'))
    
    for bar, dl in zip(bars1, downloads):
        width = bar.get_width()
        label = f'{dl/1000:.1f}K' if dl < 1e6 else f'{dl/1e6:.1f}M'
        ax1.text(width, bar.get_y() + bar.get_height()/2, f' {label}', 
                va='center', fontsize=9, color='#333')
    
    # Likes chart
    bars2 = ax2.barh(y_pos, likes, color=colors1, edgecolor='white', linewidth=0.5)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(names, fontsize=10)
    ax2.invert_yaxis()
    ax2.set_xlabel('Likes', fontsize=12)
    ax2.set_title('Top Models by Likes', fontsize=14, fontweight='bold')
    
    for bar, lk in zip(bars2, likes):
        width = bar.get_width()
        ax2.text(width, bar.get_y() + bar.get_height()/2, f' {lk}', 
                va='center', fontsize=9, color='#333')
    
    plt.suptitle(f'Hugging Face Top Models - {data.get("date", "")}', 
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  Leaderboard saved to: {output_path}")
    return output_path

def generate_tech_distribution(data: Dict, output_path: str) -> str:
    """Generate tech distribution chart"""
    print("Generating tech distribution...")
    
    tech_dist = data.get("statistics", {}).get("tech_distribution", {})
    
    if not tech_dist:
        print("  No tech distribution data")
        return ""
    
    # Use English names for display
    labels = [TECH_NAMES_EN.get(k, k) for k in tech_dist.keys()]
    sizes = list(tech_dist.values())
    colors = [TECH_COLORS.get(k, TECH_COLORS["其他"]) for k in tech_dist.keys()]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    
    # Pie chart
    wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                        startangle=90, pctdistance=0.75)
    ax1.set_title('Tech Distribution (Pie)', fontsize=14, fontweight='bold')
    
    for autotext in autotexts:
        autotext.set_fontsize(9)
    for text in texts:
        text.set_fontsize(10)
    
    # Bar chart
    y_pos = np.arange(len(labels))
    ax2.barh(y_pos, sizes, color=colors, edgecolor='white', linewidth=0.5)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(labels, fontsize=10)
    ax2.invert_yaxis()
    ax2.set_xlabel('Count', fontsize=12)
    ax2.set_title('Tech Distribution (Bar)', fontsize=14, fontweight='bold')
    
    for i, v in enumerate(sizes):
        ax2.text(v + 0.5, i, str(v), va='center', fontsize=10)
    
    plt.suptitle(f'Hugging Face Tech Distribution - {data.get("date", "")}', 
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  Tech distribution saved to: {output_path}")
    return output_path

def generate_bubble_chart(data: Dict, output_path: str) -> str:
    """Generate bubble chart"""
    print("Generating bubble chart...")
    
    all_models = (
        data.get("trending_models", []) +
        data.get("most_downloaded", [])[:10] +
        data.get("most_liked", [])[:10]
    )
    
    # Remove duplicates
    seen = set()
    unique_models = []
    for m in all_models:
        if m.get("id") not in seen:
            seen.add(m.get("id"))
            unique_models.append(m)
    
    if len(unique_models) < 3:
        print("  Not enough models for bubble chart")
        return ""
    
    names = [m.get("id", "").split("/")[-1][:20] for m in unique_models[:20]]
    downloads = [m.get("downloads", 0) for m in unique_models[:20]]
    likes = [m.get("likes", 0) for m in unique_models[:20]]
    categories = [m.get("tech_category", "Other") for m in unique_models[:20]]
    
    # Bubble size based on likes
    sizes = [max(50, min(l * 0.5, 2000)) for l in likes]
    colors = [TECH_COLORS.get(cat, TECH_COLORS["其他"]) for cat in categories]
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    scatter = ax.scatter(downloads, likes, s=sizes, c=colors, alpha=0.6, edgecolors='white', linewidth=1)
    
    # Add labels for top 15
    for i, name in enumerate(names[:15]):
        ax.annotate(name, (downloads[i], likes[i]), fontsize=8, ha='center', va='bottom')
    
    ax.set_xlabel('Downloads', fontsize=12)
    ax.set_ylabel('Likes', fontsize=12)
    ax.set_title(f'Hugging Face Model Popularity - {data.get("date", "")}', 
                 fontsize=16, fontweight='bold')
    
    # Legend with English names
    unique_cats = list(set(categories))
    legend_handles = [plt.scatter([], [], c=TECH_COLORS.get(cat, TECH_COLORS["其他"]), s=100, 
                                  label=TECH_NAMES_EN.get(cat, cat)) 
                      for cat in unique_cats]
    ax.legend(handles=legend_handles, loc='upper right')
    
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K' if x < 1e6 else f'{x/1e6:.1f}M'))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  Bubble chart saved to: {output_path}")
    return output_path

def generate_org_ranking(data: Dict, output_path: str) -> str:
    """Generate organization ranking chart"""
    print("Generating organization ranking...")
    
    all_models = (
        data.get("trending_models", []) +
        data.get("most_downloaded", []) +
        data.get("most_liked", [])
    )
    
    org_counter = Counter()
    for model in all_models:
        author = model.get("author")
        if author:
            org_counter[author] += 1
    
    if not org_counter:
        print("  No organization data")
        return ""
    
    top_orgs = org_counter.most_common(15)
    orgs = [o[0] for o in top_orgs]
    counts = [o[1] for o in top_orgs]
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(orgs)))
    y_pos = np.arange(len(orgs))
    bars = ax.barh(y_pos, counts, color=colors, edgecolor='white', linewidth=0.5)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(orgs, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel('Model Count', fontsize=12)
    ax.set_title(f'Hugging Face Active Organizations - {data.get("date", "")}', 
                 fontsize=16, fontweight='bold')
    
    for bar, count in zip(bars, counts):
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, str(count), 
                va='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  Organization ranking saved to: {output_path}")
    return output_path

def main():
    """Main function"""
    print("=" * 60)
    print("Hugging Face Hot Tech Visualizer")
    print("=" * 60)
    
    data = load_data()
    if not data:
        print("Error: Cannot load data file")
        return
    
    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    print(f"\nData date: {date_str}")
    
    # Generate visualizations
    outputs = []
    
    # Word cloud
    wc_path = os.path.join(OUTPUT_DIR, f"wordcloud_{date_str}.png")
    if generate_wordcloud(data, wc_path):
        outputs.append(wc_path)
    
    # Leaderboard
    lb_path = os.path.join(OUTPUT_DIR, f"leaderboard_{date_str}.png")
    if generate_leaderboard(data, lb_path):
        outputs.append(lb_path)
    
    # Tech distribution
    td_path = os.path.join(OUTPUT_DIR, f"tech_distribution_{date_str}.png")
    if generate_tech_distribution(data, td_path):
        outputs.append(td_path)
    
    # Bubble chart
    bc_path = os.path.join(OUTPUT_DIR, f"bubble_chart_{date_str}.png")
    if generate_bubble_chart(data, bc_path):
        outputs.append(bc_path)
    
    # Organization ranking
    or_path = os.path.join(OUTPUT_DIR, f"org_ranking_{date_str}.png")
    if generate_org_ranking(data, or_path):
        outputs.append(or_path)
    
    print("\n" + "=" * 60)
    print(f"Visualization complete! Generated {len(outputs)} charts")
    for output in outputs:
        print(f"  - {output}")
    print("=" * 60)

if __name__ == "__main__":
    main()
