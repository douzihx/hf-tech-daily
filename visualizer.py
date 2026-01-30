#!/usr/bin/env python3
"""
Hugging Face 热门 AI 技术可视化脚本
生成词云、排行榜、趋势图等可视化效果
适配 GitHub Actions 环境
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
import matplotlib.font_manager as fm
import numpy as np
from wordcloud import WordCloud

# 设置中文字体
plt.rcParams['font.family'] = ['Noto Sans CJK SC', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 配置 - 适配 GitHub Actions 环境
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 在 GitHub Actions 中，数据文件保存在仓库根目录
DATA_DIR = SCRIPT_DIR  # 数据文件在脚本同目录
OUTPUT_DIR = SCRIPT_DIR  # 输出也在同目录

# 颜色方案
COLORS = {
    "primary": "#FF6B35",
    "secondary": "#004E89",
    "accent": "#00A896",
    "background": "#F8F9FA",
    "text": "#2D3436"
}

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

def load_data(date: Optional[str] = None) -> Optional[Dict]:
    """加载数据文件 - 支持多种文件名格式"""
    print(f"正在查找数据文件...")
    print(f"  脚本目录: {SCRIPT_DIR}")
    print(f"  数据目录: {DATA_DIR}")
    
    # 列出目录中的所有文件
    all_files = os.listdir(DATA_DIR)
    print(f"  目录中的文件: {all_files}")
    
    # 尝试多种文件名格式
    patterns = [
        "data_*.json",           # scraper.py 保存的格式
        "hf_data_*.json",        # 旧格式
    ]
    
    data_files = []
    for pattern in patterns:
        matches = glob.glob(os.path.join(DATA_DIR, pattern))
        data_files.extend(matches)
    
    print(f"  找到的数据文件: {data_files}")
    
    if not data_files:
        print("  没有找到数据文件!")
        return None
    
    # 选择最新的文件
    latest_file = sorted(data_files)[-1]
    print(f"  使用数据文件: {latest_file}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_keywords(models: List[Dict]) -> Dict[str, int]:
    """从模型名称和标签中提取关键词"""
    keywords = Counter()
    
    # 常见的技术关键词
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
        
        # 分词
        words = re.findall(r'[a-zA-Z]+|\d+[bB]', model_name)
        for word in words:
            word_lower = word.lower()
            if len(word_lower) >= 2 and word_lower in tech_terms:
                keywords[word_lower] += 1
        
        # 添加 pipeline_tag
        pipeline_tag = model.get("pipeline_tag")
        if pipeline_tag:
            keywords[pipeline_tag.replace("-", " ")] += 1
        
        # 添加作者
        author = model.get("author")
        if author:
            keywords[author.lower()] += 1
    
    return dict(keywords)

def generate_wordcloud(data: Dict, output_path: str) -> str:
    """生成词云图"""
    print("正在生成词云...")
    
    # 合并所有模型
    all_models = (
        data.get("trending_models", []) +
        data.get("most_downloaded", []) +
        data.get("most_liked", [])
    )
    
    # 提取关键词
    keywords = extract_keywords(all_models)
    
    if not keywords:
        print("  没有足够的关键词生成词云")
        return ""
    
    # 生成词云
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
    
    # 保存图片
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    ax.set_title(f'Hugging Face 热门技术词云 - {data.get("date", "")}', 
                 fontsize=20, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  词云已保存到: {output_path}")
    return output_path

def generate_leaderboard(data: Dict, output_path: str) -> str:
    """生成排行榜图表"""
    print("正在生成排行榜...")
    
    # 获取热门模型 Top 15
    trending = data.get("trending_models", [])[:15]
    if not trending:
        trending = data.get("most_downloaded", [])[:15]
    
    if not trending:
        print("  没有足够的数据生成排行榜")
        return ""
    
    # 准备数据
    names = [m.get("id", "").split("/")[-1][:25] for m in trending]
    downloads = [m.get("downloads", 0) for m in trending]
    likes = [m.get("likes", 0) for m in trending]
    categories = [m.get("tech_category", "其他") for m in trending]
    colors = [TECH_COLORS.get(cat, TECH_COLORS["其他"]) for cat in categories]
    
    # 创建图表
    fig, axes = plt.subplots(1, 2, figsize=(18, 10))
    
    # 下载量排行
    ax1 = axes[0]
    y_pos = np.arange(len(names))
    bars1 = ax1.barh(y_pos, downloads, color=colors, edgecolor='white', linewidth=0.5)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(names, fontsize=10)
    ax1.invert_yaxis()
    ax1.set_xlabel('下载量', fontsize=12)
    ax1.set_title('热门模型下载量排行', fontsize=14, fontweight='bold')
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K' if x < 1e6 else f'{x/1e6:.1f}M'))
    
    # 添加数值标签
    for bar, val in zip(bars1, downloads):
        width = bar.get_width()
        label = f'{val/1000:.1f}K' if val < 1e6 else f'{val/1e6:.2f}M'
        ax1.text(width, bar.get_y() + bar.get_height()/2, f' {label}',
                va='center', fontsize=9)
    
    # 点赞数排行
    ax2 = axes[1]
    bars2 = ax2.barh(y_pos, likes, color=colors, edgecolor='white', linewidth=0.5)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(names, fontsize=10)
    ax2.invert_yaxis()
    ax2.set_xlabel('点赞数', fontsize=12)
    ax2.set_title('热门模型点赞数排行', fontsize=14, fontweight='bold')
    
    # 添加数值标签
    for bar, val in zip(bars2, likes):
        width = bar.get_width()
        ax2.text(width, bar.get_y() + bar.get_height()/2, f' {val}',
                va='center', fontsize=9)
    
    # 添加图例
    unique_cats = list(set(categories))
    legend_handles = [plt.Rectangle((0,0),1,1, color=TECH_COLORS.get(cat, TECH_COLORS["其他"])) 
                      for cat in unique_cats]
    fig.legend(legend_handles, unique_cats, loc='upper center', 
               ncol=min(5, len(unique_cats)), bbox_to_anchor=(0.5, 0.02))
    
    plt.suptitle(f'Hugging Face 热门模型排行榜 - {data.get("date", "")}', 
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  排行榜已保存到: {output_path}")
    return output_path

def generate_tech_distribution(data: Dict, output_path: str) -> str:
    """生成技术领域分布图"""
    print("正在生成技术领域分布图...")
    
    tech_dist = data.get("statistics", {}).get("tech_distribution", {})
    if not tech_dist:
        print("  没有技术分布数据")
        return ""
    
    # 准备数据
    labels = list(tech_dist.keys())
    sizes = list(tech_dist.values())
    colors = [TECH_COLORS.get(label, TECH_COLORS["其他"]) for label in labels]
    
    # 创建图表
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    # 饼图
    ax1 = axes[0]
    wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors,
                                        autopct='%1.1f%%', startangle=90,
                                        textprops={'fontsize': 10})
    ax1.set_title('技术领域分布', fontsize=14, fontweight='bold')
    
    # 条形图
    ax2 = axes[1]
    y_pos = np.arange(len(labels))
    bars = ax2.barh(y_pos, sizes, color=colors, edgecolor='white', linewidth=0.5)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(labels, fontsize=11)
    ax2.invert_yaxis()
    ax2.set_xlabel('模型数量', fontsize=12)
    ax2.set_title('各技术领域模型数量', fontsize=14, fontweight='bold')
    
    # 添加数值标签
    for bar, val in zip(bars, sizes):
        width = bar.get_width()
        ax2.text(width, bar.get_y() + bar.get_height()/2, f' {val}',
                va='center', fontsize=10)
    
    plt.suptitle(f'Hugging Face 技术领域分布 - {data.get("date", "")}', 
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  技术分布图已保存到: {output_path}")
    return output_path

def generate_org_ranking(data: Dict, output_path: str) -> str:
    """生成组织排行图"""
    print("正在生成组织排行图...")
    
    org_dist = data.get("statistics", {}).get("top_organizations", {})
    if not org_dist:
        print("  没有组织分布数据")
        return ""
    
    # 取 Top 15
    sorted_orgs = sorted(org_dist.items(), key=lambda x: x[1], reverse=True)[:15]
    labels = [org for org, _ in sorted_orgs]
    values = [count for _, count in sorted_orgs]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # 使用渐变色
    cmap = plt.cm.get_cmap('RdYlBu_r')
    colors = [cmap(i / len(labels)) for i in range(len(labels))]
    
    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, color=colors, edgecolor='white', linewidth=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel('热门模型数量', fontsize=12)
    ax.set_title(f'Hugging Face 活跃组织排行 - {data.get("date", "")}', 
                 fontsize=16, fontweight='bold')
    
    # 添加数值标签
    for bar, val in zip(bars, values):
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2, f' {val}',
               va='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  组织排行图已保存到: {output_path}")
    return output_path

def generate_bubble_chart(data: Dict, output_path: str) -> str:
    """生成气泡图"""
    print("正在生成气泡图...")
    
    # 合并所有模型
    all_models = data.get("trending_models", [])[:30]
    if not all_models:
        print("  没有足够的数据生成气泡图")
        return ""
    
    # 准备数据
    downloads = [m.get("downloads", 0) for m in all_models]
    likes = [m.get("likes", 0) for m in all_models]
    names = [m.get("id", "").split("/")[-1][:15] for m in all_models]
    categories = [m.get("tech_category", "其他") for m in all_models]
    colors = [TECH_COLORS.get(cat, TECH_COLORS["其他"]) for cat in categories]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # 气泡大小基于下载量
    max_downloads = max(downloads) if downloads else 1
    sizes = [max(100, (d / max_downloads) * 2000) for d in downloads]
    
    scatter = ax.scatter(downloads, likes, s=sizes, c=colors, alpha=0.6, edgecolors='white', linewidth=1)
    
    # 添加标签
    for i, name in enumerate(names[:15]):  # 只标注前15个
        ax.annotate(name, (downloads[i], likes[i]), fontsize=8, ha='center', va='bottom')
    
    ax.set_xlabel('下载量', fontsize=12)
    ax.set_ylabel('点赞数', fontsize=12)
    ax.set_title(f'Hugging Face 模型热度分布 - {data.get("date", "")}', 
                 fontsize=16, fontweight='bold')
    
    # 添加图例
    unique_cats = list(set(categories))
    legend_handles = [plt.scatter([], [], c=TECH_COLORS.get(cat, TECH_COLORS["其他"]), s=100, label=cat) 
                      for cat in unique_cats]
    ax.legend(handles=legend_handles, loc='upper right')
    
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K' if x < 1e6 else f'{x/1e6:.1f}M'))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  气泡图已保存到: {output_path}")
    return output_path

def main():
    """主函数"""
    print("=" * 60)
    print("Hugging Face 热门技术可视化")
    print("=" * 60)
    
    # 加载数据
    data = load_data()
    if not data:
        print("错误: 无法加载数据文件")
        return
    
    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    print(f"\n数据日期: {date_str}")
    
    # 生成各种可视化
    outputs = []
    
    # 1. 词云
    wordcloud_path = os.path.join(OUTPUT_DIR, f"wordcloud_{date_str}.png")
    if generate_wordcloud(data, wordcloud_path):
        outputs.append(wordcloud_path)
    
    # 2. 排行榜
    leaderboard_path = os.path.join(OUTPUT_DIR, f"leaderboard_{date_str}.png")
    if generate_leaderboard(data, leaderboard_path):
        outputs.append(leaderboard_path)
    
    # 3. 技术分布
    tech_dist_path = os.path.join(OUTPUT_DIR, f"tech_distribution_{date_str}.png")
    if generate_tech_distribution(data, tech_dist_path):
        outputs.append(tech_dist_path)
    
    # 4. 组织排行
    org_ranking_path = os.path.join(OUTPUT_DIR, f"org_ranking_{date_str}.png")
    if generate_org_ranking(data, org_ranking_path):
        outputs.append(org_ranking_path)
    
    # 5. 气泡图
    bubble_path = os.path.join(OUTPUT_DIR, f"bubble_chart_{date_str}.png")
    if generate_bubble_chart(data, bubble_path):
        outputs.append(bubble_path)
    
    print("\n" + "=" * 60)
    print(f"可视化完成! 共生成 {len(outputs)} 个图表")
    print("=" * 60)

if __name__ == "__main__":
    main()
