#!/usr/bin/env python3
"""
Hugging Face 热门 AI 技术爬取脚本 (全功能无损升级版)
功能：保留原始所有逻辑 + 500采样量 + 智能作者提取 + URL采集
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
    if num_params is None:
        return "未知"
    if num_params < 1e9:
        return "微型 (<1B)"
    elif num_params < 7e9:
        return "小型 (1B-7B)"
    elif num_params < 32e9:
        return "中型 (7B-32B)"
    elif num_params < 128e9:
        return "大型 (32B-128B)"
    else:
        return "超大型 (>128B)"

def get_tech_category(pipeline_tag: Optional[str]) -> str:
    if pipeline_tag is None:
        return "其他"
    for category, tags in TECH_CATEGORIES.items():
        if pipeline_tag in tags:
            return category
    return "其他"

def fetch_trending_models(limit: int = 100) -> List[Dict]:
    print(f"正在获取热门模型 (Top {limit})...")
    url = "https://huggingface.co/api/trending"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        models = []
        for item in data.get("recentlyTrending", [])[:limit]:
            repo_data = item.get("repoData", {})
            if item.get("repoType") == "model":
                model_id = repo_data.get("id")
                author = repo_data.get("author")
                # 智能作者提取
                if not author and model_id and "/" in model_id:
                    author = model_id.split("/")[0]
                
                models.append({
                    "id": model_id,
                    "url": f"https://huggingface.co/{model_id}",
                    "author": author or "unknown",
                    "author_url": f"https://huggingface.co/{author}" if author else None,
                    "pipeline_tag": repo_data.get("pipeline_tag"),
                    "downloads": repo_data.get("downloads", 0),
                    "likes": repo_data.get("likes", 0),
                    "num_parameters": repo_data.get("numParameters"),
                    "last_modified": repo_data.get("lastModified"),
                    "source": "trending"
                })
        print(f"  获取到 {len(models)} 个热门模型")
        return models
    except Exception as e:
        print(f"  获取热门模型失败: {e}")
        return []

def fetch_models_by_sort(sort: str, limit: int = 500, pipeline_tag: Optional[str] = None) -> List[Dict]:
    print(f"正在获取模型 (sort={sort}, limit={limit})...")
    api = HfApi()
    try:
        models_iter = api.list_models(sort=sort, limit=limit, pipeline_tag=pipeline_tag)
        
        models = []
        for model in models_iter:
            author = model.author
            # 智能作者提取
            if not author and model.id and "/" in model.id:
                author = model.id.split("/")[0]
                
            models.append({
                "id": model.id,
                "url": f"https://huggingface.co/{model.id}",
                "author": author or "unknown",
                "author_url": f"https://huggingface.co/{author}" if author else None,
                "pipeline_tag": model.pipeline_tag,
                "downloads": getattr(model, 'downloads', 0),
                "likes": getattr(model, 'likes', 0),
                "num_parameters": getattr(model, 'safetensors', {}).get('total') if hasattr(model, 'safetensors') and model.safetensors else None,
                "last_modified": model.last_modified.isoformat() if model.last_modified else None,
                "tags": list(model.tags) if model.tags else [],
                "source": f"{sort}"
            })
        print(f"  获取到 {len(models)} 个模型")
        return models
    except Exception as e:
        print(f"  获取模型失败: {e}")
        return []

def fetch_models_by_category(limit_per_category: int = 20) -> Dict[str, List[Dict]]:
    print("正在按技术领域获取模型...")
    category_models = {}
    for category, tags in TECH_CATEGORIES.items():
        if not tags: continue
        category_models[category] = []
        for tag in tags[:2]:
            models = fetch_models_by_sort("downloads", limit=limit_per_category, pipeline_tag=tag)
            category_models[category].extend(models)
        seen_ids = set()
        unique_models = []
        for m in category_models[category]:
            if m["id"] not in seen_ids:
                seen_ids.add(m["id"])
                unique_models.append(m)
        category_models[category] = unique_models[:limit_per_category]
    return category_models

def enrich_model_data(models: List[Dict]) -> List[Dict]:
    for model in models:
        model["tech_category"] = get_tech_category(model.get("pipeline_tag"))
        model["size_category"] = get_size_category(model.get("num_parameters"))
    return models

def collect_all_data() -> Dict:
    today = datetime.now().strftime("%Y-%m-%d")
    data = {
        "date": today,
        "timestamp": datetime.now().isoformat(),
        "trending_models": [],
        "most_downloaded": [],
        "most_liked": [],
        "by_category": {},
        "statistics": {}
    }
    
    # 扩大采样量到 500
    data["trending_models"] = enrich_model_data(fetch_trending_models(100))
    data["most_downloaded"] = enrich_model_data(fetch_models_by_sort("downloads", 500))
    data["most_liked"] = enrich_model_data(fetch_models_by_sort("likes", 500))
    
    category_models = fetch_models_by_category(20)
    for category, models in category_models.items():
        data["by_category"][category] = enrich_model_data(models)
    
    all_models_raw = data["trending_models"] + data["most_downloaded"] + data["most_liked"]
    # 去重
    seen = set()
    all_models = []
    for m in all_models_raw:
        if m["id"] not in seen:
            seen.add(m["id"])
            all_models.append(m)
    
    # 统计
    tech_dist = {}
    for model in all_models:
        cat = model.get("tech_category", "其他")
        tech_dist[cat] = tech_dist.get(cat, 0) + 1
    data["statistics"]["tech_distribution"] = tech_dist
    
    org_dist = {}
    for model in all_models:
        author = model.get("author")
        if author and author != "unknown":
            org_dist[author] = org_dist.get(author, 0) + 1
    data["statistics"]["top_organizations"] = dict(
        sorted(org_dist.items(), key=lambda x: x[1], reverse=True)[:20]
    )
    
    size_dist = {}
    for model in all_models:
        size = model.get("size_category", "未知")
        size_dist[size] = size_dist.get(size, 0) + 1
    data["statistics"]["size_distribution"] = size_dist
    
    return data

def save_data(data: Dict) -> str:
    filename = f"hf_data_{data['date']}.json"
    filepath = os.path.join(ROOT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(os.path.join(ROOT_DIR, "latest.json"), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath

if __name__ == "__main__":
    data = collect_all_data()
    save_data(data)
