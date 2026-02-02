#!/usr/bin/env python3
"""
Hugging Face 热门 AI 技术爬取脚本 (GitHub Actions 版本)
更新: 增加技术关键字标签提取功能，用于生成精美交互式词云
"""

import json
import os
import re
import requests
from datetime import datetime
from huggingface_hub import HfApi
from typing import Dict, List, Optional
from collections import Counter

# 配置 - 使用当前工作目录
ROOT_DIR = os.getcwd()
DATA_DIR = ROOT_DIR  # 直接保存到根目录

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

# ========== 新增: 技术关键字提取配置 ==========
# 已知的热门技术关键字 (用于从模型ID和标签中匹配)
KNOWN_TECH_KEYWORDS = [
    # 大语言模型系列
    "Qwen", "DeepSeek", "LLaMA", "Llama", "Mistral", "Gemma", "Phi", "Yi", "InternLM", 
    "ChatGLM", "Baichuan", "BLOOM", "Falcon", "MPT", "OPT", "Pythia", "StableLM",
    "Vicuna", "Alpaca", "WizardLM", "OpenChat", "Zephyr", "Neural", "Orca",
    # 图像生成
    "Diffusion", "SDXL", "Stable", "FLUX", "Kandinsky", "PixArt", "Playground",
    "DALL-E", "Midjourney", "ControlNet", "IP-Adapter", "LoRA", "LCM",
    # 多模态
    "CLIP", "BLIP", "LLaVA", "CogVLM", "Qwen-VL", "InternVL", "MiniGPT",
    "Fuyu", "Idefics", "PaliGemma", "Florence",
    # 语音
    "Whisper", "Wav2Vec", "HuBERT", "SpeechT5", "VITS", "Bark", "TTS",
    "Coqui", "XTTS", "MMS", "SeamlessM4T",
    # NLP基础
    "BERT", "RoBERTa", "T5", "GPT", "GPT-2", "XLNet", "ELECTRA", "DeBERTa",
    "DistilBERT", "ALBERT", "Longformer", "BigBird",
    # 视觉
    "ViT", "DINO", "SAM", "YOLO", "ResNet", "ConvNeXt", "Swin", "BEiT",
    "DeiT", "EfficientNet", "MobileNet", "SegFormer", "Mask2Former",
    # 其他热门
    "Embedding", "Reranker", "BGE", "E5", "GTE", "Jina", "Cohere",
    "Sentence", "Transformer", "Mamba", "RWKV", "RetNet",
    # 特定项目/公司
    "OpenAI", "Anthropic", "Google", "Meta", "Microsoft", "NVIDIA",
    "Alibaba", "Tencent", "Baidu", "ByteDance", "01-ai", "Colossal",
]

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

# ========== 新增: 从模型ID和标签中提取技术关键字 ==========
# 需要排除的非技术标签 (pipeline tags, 框架, 部署等)
EXCLUDE_TAGS = [
    # Pipeline tags
    "text-generation", "text2text-generation", "conversational", "text-to-image",
    "image-to-text", "text-to-speech", "automatic-speech-recognition", "text-to-audio",
    "text-to-video", "image-to-video", "video-to-video", "image-classification",
    "object-detection", "image-segmentation", "feature-extraction", "sentence-similarity",
    "visual-question-answering", "document-question-answering", "image-text-to-text",
    "any-to-any", "audio-to-audio", "unconditional-image-generation", "image-to-image",
    "fill-mask", "token-classification", "question-answering", "summarization",
    "translation", "zero-shot-classification", "reinforcement-learning",
    # 框架和格式
    "pytorch", "tensorflow", "jax", "flax", "onnx", "safetensors", "gguf", "ggml",
    "transformers", "diffusers", "peft", "trl", "accelerate",
    # 部署和平台
    "deploy:azure", "endpoints_compatible", "text-generation-inference",
    "region:us", "region:eu", "region:cn",
    # 语言和许可
    "en", "zh", "es", "fr", "de", "ja", "ko", "ar", "ru", "pt",
    "license:mit", "license:apache-2.0", "license:cc-by-4.0", "license:other",
    # 其他无意义标签
    "arxiv", "autotrain", "autotrain_compatible", "eval", "generated_from_trainer",
    "base_model", "finetune", "adapter", "merge", "quantized", "4bit", "8bit",
]

def extract_tech_keywords(model_id: str, tags: List[str]) -> List[str]:
    """从模型ID和标签中提取技术关键字"""
    keywords = set()
    
    # 从模型ID中提取
    model_name = model_id.split("/")[-1] if "/" in model_id else model_id
    
    for keyword in KNOWN_TECH_KEYWORDS:
        # 不区分大小写匹配
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        if pattern.search(model_name):
            # 保留原始大小写形式
            keywords.add(keyword)
    
    # 从标签中匹配已知技术关键字
    for tag in tags:
        tag_lower = tag.lower()
        for keyword in KNOWN_TECH_KEYWORDS:
            if keyword.lower() == tag_lower or keyword.lower() in tag_lower:
                keywords.add(keyword)
    
    return list(keywords)

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
                model_id = repo_data.get("id", "")
                tags = repo_data.get("tags", [])
                models.append({
                    "id": model_id,
                    "author": repo_data.get("author"),
                    "pipeline_tag": repo_data.get("pipeline_tag"),
                    "downloads": repo_data.get("downloads", 0),
                    "likes": repo_data.get("likes", 0),
                    "num_parameters": repo_data.get("numParameters"),
                    "last_modified": repo_data.get("lastModified"),
                    "tags": tags if isinstance(tags, list) else [],
                    "tech_keywords": extract_tech_keywords(model_id, tags if isinstance(tags, list) else []),
                    "source": "trending"
                })
        print(f"  获取到 {len(models)} 个热门模型")
        return models
    except Exception as e:
        print(f"  获取热门模型失败: {e}")
        return []

def fetch_models_by_sort(sort: str, limit: int = 100, pipeline_tag: Optional[str] = None) -> List[Dict]:
    print(f"正在获取模型 (sort={sort}, limit={limit})...")
    api = HfApi()
    try:
        models_iter = api.list_models(sort=sort, limit=limit, pipeline_tag=pipeline_tag)
        
        models = []
        for model in models_iter:
            model_id = model.id
            tags = list(model.tags) if model.tags else []
            models.append({
                "id": model_id,
                "author": model.author,
                "pipeline_tag": model.pipeline_tag,
                "downloads": getattr(model, 'downloads', 0),
                "likes": getattr(model, 'likes', 0),
                "num_parameters": getattr(model, 'safetensors', {}).get('total') if hasattr(model, 'safetensors') and model.safetensors else None,
                "last_modified": model.last_modified.isoformat() if model.last_modified else None,
                "tags": tags,
                "tech_keywords": extract_tech_keywords(model_id, tags),
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
        if not tags:
            continue
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

# ========== 新增: 统计技术关键字热度 ==========
def calculate_keyword_stats(all_models: List[Dict]) -> Dict[str, int]:
    """统计所有模型中技术关键字的出现频率"""
    keyword_counter = Counter()
    
    for model in all_models:
        keywords = model.get("tech_keywords", [])
        # 每个模型的关键字只计算一次
        for kw in set(keywords):
            keyword_counter[kw] += 1
    
    # 过滤掉出现次数太少的关键字（至少出现2次）
    filtered = {k: v for k, v in keyword_counter.items() if v >= 2}
    
    # 按热度排序，取前50个
    sorted_keywords = dict(sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:50])
    
    return sorted_keywords

def collect_all_data() -> Dict:
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'='*60}")
    print(f"开始数据采集 - {today}")
    print(f"{'='*60}\n")
    
    data = {
        "date": today,
        "timestamp": datetime.now().isoformat(),
        "trending_models": [],
        "most_downloaded": [],
        "most_liked": [],
        "by_category": {},
        "statistics": {}
    }
    
    data["trending_models"] = enrich_model_data(fetch_trending_models(100))
    data["most_downloaded"] = enrich_model_data(fetch_models_by_sort("downloads", 100))
    data["most_liked"] = enrich_model_data(fetch_models_by_sort("likes", 100))
    
    category_models = fetch_models_by_category(20)
    for category, models in category_models.items():
        data["by_category"][category] = enrich_model_data(models)
    
    all_models = data["trending_models"] + data["most_downloaded"] + data["most_liked"]
    
    tech_dist = {}
    for model in all_models:
        cat = model.get("tech_category", "其他")
        tech_dist[cat] = tech_dist.get(cat, 0) + 1
    data["statistics"]["tech_distribution"] = tech_dist
    
    org_dist = {}
    for model in all_models:
        author = model.get("author")
        if author:
            org_dist[author] = org_dist.get(author, 0) + 1
    data["statistics"]["top_organizations"] = dict(
        sorted(org_dist.items(), key=lambda x: x[1], reverse=True)[:20]
    )
    
    size_dist = {}
    for model in all_models:
        size = model.get("size_category", "未知")
        size_dist[size] = size_dist.get(size, 0) + 1
    data["statistics"]["size_distribution"] = size_dist
    
    # ========== 新增: 技术关键字热度统计 ==========
    print("正在统计技术关键字热度...")
    keyword_stats = calculate_keyword_stats(all_models)
    data["statistics"]["tech_keywords"] = keyword_stats
    print(f"  提取到 {len(keyword_stats)} 个热门技术关键字")
    
    print(f"\n数据采集完成!")
    return data

def save_data(data: Dict) -> str:
    # 保存到根目录
    filename = f"hf_data_{data['date']}.json"
    filepath = os.path.join(ROOT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 同时保存为 latest.json
    latest_path = os.path.join(ROOT_DIR, "latest.json")
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到: {filepath}")
    print(f"latest.json 已保存到: {latest_path}")
    return filepath

def main():
    print(f"当前工作目录: {ROOT_DIR}")
    print(f"目录内容: {os.listdir(ROOT_DIR)}")
    data = collect_all_data()
    save_data(data)
    return data

if __name__ == "__main__":
    main()
