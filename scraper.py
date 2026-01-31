#!/usr/bin/env python3
"""
Hugging Face 热门 AI 技术爬取脚本 (GitHub Actions 优化版)
"""

import json
import os
import requests
from datetime import datetime
from huggingface_hub import HfApi
from typing import Dict, List, Optional

# 配置 - 使用当前工作目录
ROOT_DIR = os.getcwd()
DATA_DIR = ROOT_DIR

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

def get_size_category(num_params: Optional[int]) -> str:
    if num_params is None: return "未知"
    if num_params < 1e9: return "微型 (<1B)"
    elif num_params < 7e9: return "小型 (1B-7B)"
    elif num_params < 32e9: return "中型 (7B-32B)"
    elif num_params < 128e9: return "大型 (32B-128B)"
    else: return "超大型 (>128B)"

def get_tech_category(pipeline_tag: Optional[str]) -> str:
    if pipeline_tag is None: return "其他"
    for category, tags in TECH_CATEGORIES.items():
        if pipeline_tag in tags: return category
    return "其他"

def fetch_trending_models(limit: int = 500) -> List[Dict]:
    print(f"正在获取热门模型 (Top {limit})...")
    url = "https://huggingface.co/api/trending"
    try:
        response = requests.get(url, timeout=30 )
        response.raise_for_status()
        data = response.json()
        models = []
        for item in data.get("recentlyTrending", [])[:limit]:
            repo_data = item.get("repoData", {})
            if item.get("repoType") == "model":
                models.append({
                    "id": repo_data.get("id"),
                    "author": repo_data.get("author"),
                    "pipeline_tag": repo_data.get("pipeline_tag"),
                    "downloads": repo_data.get("downloads", 0),
                    "likes": repo_data.get("likes", 0),
                    "num_parameters": repo_data.get("numParameters"),
                    "last_modified": repo_data.get("lastModified"),
                    "source": "trending"
                })
        return models
    except Exception as e:
        print(f"获取热门模型失败: {e}")
        return []

def fetch_models_by_sort(sort: str, limit: int = 500) -> List[Dict]:
    print(f"正在获取模型 (sort={sort}, limit={limit})...")
    api = HfApi()
    try:
        models_iter = api.list_models(sort=sort, limit=limit)
        models = []
        for model in models_iter:
            models.append({
                "id": model.id,
                "author": model.author,
                "pipeline_tag": model.pipeline_tag,
                "downloads": getattr(model, 'downloads', 0),
                "likes": getattr(model, 'likes', 0),
                "num_parameters": getattr(model, 'safetensors', {}).get('total') if hasattr(model, 'safetensors') and model.safetensors else None,
                "last_modified": model.last_modified.isoformat() if model.last_modified else None,
                "source": sort
            })
        return models
    except Exception as e:
        print(f"获取模型失败: {e}")
        return []

def collect_all_data() -> Dict:
    today = datetime.now().strftime("%Y-%m-%d")
    data = {"date": today, "timestamp": datetime.now().isoformat(), "statistics": {}}
    
    # 扩大采样量到 500
    trending = fetch_trending_models(500)
    downloaded = fetch_models_by_sort("downloads", 500)
    liked = fetch_models_by_sort("likes", 500)
    
    # 去重并整合
    all_models_dict = {m["id"]: m for m in (trending + downloaded + liked)}
    all_models = list(all_models_dict.values())
    
    for m in all_models:
        m["tech_category"] = get_tech_category(m.get("pipeline_tag"))
        m["size_category"] = get_size_category(m.get("num_parameters"))

    # 统计组织活跃度 (修复逻辑)
    org_dist = {}
    for m in all_models:
        author = m.get("author")
        if not author and m.get("id") and "/" in m["id"]:
            author = m["id"].split("/")[0]
        if author:
            org_dist[author] = org_dist.get(author, 0) + 1
    
    data["statistics"]["top_organizations"] = dict(sorted(org_dist.items(), key=lambda x: x[1], reverse=True)[:20])
    data["statistics"]["tech_distribution"] = {}
    for m in all_models:
        cat = m["tech_category"]
        data["statistics"]["tech_distribution"][cat] = data["statistics"]["tech_distribution"].get(cat, 0) + 1
        
    data["trending_models"] = trending[:20]
    return data

def save_data(data: Dict):
    filepath = os.path.join(ROOT_DIR, f"hf_data_{data['date']}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(os.path.join(ROOT_DIR, "latest.json"), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    save_data(collect_all_data())
