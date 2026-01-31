#!/usr/bin/env python3
"""
Hugging Face 热门 AI 技术爬取脚本 (终极整合版)
功能：500采样量 + 智能作者提取 + URL采集
"""

import json
import os
import requests
from datetime import datetime
from huggingface_hub import HfApi
from typing import Dict, List, Optional

# 配置
ROOT_DIR = os.getcwd()

# 技术领域分类映射
TECH_CATEGORIES = {
    "语言模型": ["text-generation", "text2text-generation", "conversational"],
    "多模态模型": ["image-text-to-text", "any-to-any", "visual-question-answering"],
    "图像生成": ["text-to-image", "image-to-image", "unconditional-image-generation"],
    "视频生成": ["text-to-video", "image-to-video", "video-to-video"],
    "语音合成": ["text-to-speech", "text-to-audio"],
    "语音识别": ["automatic-speech-recognition", "audio-to-audio"],
    "文档理解": ["image-to-text", "document-question-answering"],
    "嵌入模型": ["feature-extraction", "sentence-similarity"],
    "图像理解": ["image-classification", "object-detection", "image-segmentation"],
    "其他": []
}

def get_tech_category(pipeline_tag: Optional[str]) -> str:
    if pipeline_tag is None:
        return "其他"
    for category, tags in TECH_CATEGORIES.items():
        if pipeline_tag in tags:
            return category
    return "其他"

def fetch_models(sort: str, limit: int = 500) -> List[Dict]:
    print(f"正在获取模型 (sort={sort}, limit={limit})...")
    api = HfApi()
    models = []
    try:
        models_iter = api.list_models(sort=sort, limit=limit, full=True)
        for m in models_iter:
            # 智能提取作者：如果 author 字段缺失，从 ID 中截取
            author = m.author
            if not author and m.id and "/" in m.id:
                author = m.id.split("/")[0]
            
            models.append({
                "id": m.id,
                "url": f"https://huggingface.co/{m.id}",
                "author": author or "unknown",
                "author_url": f"https://huggingface.co/{author}" if author else None,
                "pipeline_tag": m.pipeline_tag,
                "downloads": getattr(m, 'downloads', 0),
                "likes": getattr(m, 'likes', 0),
                "tech_category": get_tech_category(m.pipeline_tag)
            })
        return models
    except Exception as e:
        print(f"获取失败: {e}")
        return []

def collect_all_data():
    today = datetime.now().strftime("%Y-%m-%d")
    data = {
        "date": today,
        "timestamp": datetime.now().isoformat(),
        "trending_models": [],
        "statistics": {}
    }
    
    # 扩大采样量到 500
    all_models = fetch_models("downloads", 500)
    data["trending_models"] = all_models[:100] # 报告中展示前100
    
    # 统计技术分布
    tech_dist = {}
    for m in all_models:
        cat = m["tech_category"]
        tech_dist[cat] = tech_dist.get(cat, 0) + 1
    data["statistics"]["tech_distribution"] = tech_dist
    
    # 统计组织活跃度 (基于 500 个样本)
    org_dist = {}
    for m in all_models:
        author = m["author"]
        if author and author != "unknown":
            org_dist[author] = org_dist.get(author, 0) + 1
    
    data["statistics"]["top_organizations"] = dict(
        sorted(org_dist.items(), key=lambda x: x[1], reverse=True)[:20]
    )
    
    return data

def save_data(data):
    filename = f"hf_data_{data['date']}.json"
    with open(os.path.join(ROOT_DIR, filename), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(os.path.join(ROOT_DIR, "latest.json"), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    data = collect_all_data()
    save_data(data)
