#!/usr/bin/env python3
"""
生成 HTML 报告页面 (全功能无损整合版)
功能：保留原始所有逻辑（趋势总结、分类表格、精美样式）+ 植入超链接 + 植入历史归档
"""

import json
import os
import glob
from datetime import datetime

# 使用当前工作目录
ROOT_DIR = os.getcwd()

HF_TAG_MAP = {
    "语言模型": "text-generation",
    "多模态模型": "multimodal",
    "图像生成": "text-to-image",
    "视频生成": "text-to-video",
    "语音合成": "text-to-speech",
    "语音识别": "automatic-speech-recognition",
    "文档理解": "document-question-answering",
    "嵌入模型": "feature-extraction",
    "图像理解": "image-classification"
}

def load_data():
    latest_path = os.path.join(ROOT_DIR, "latest.json")
    if os.path.exists(latest_path):
        with open(latest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_archive_links():
    # 扫描历史 HTML 报告
    files = sorted(glob.glob("hf_daily_report_*.html"), reverse=True)
    if not files: return ""
    links = []
    for f in files[:7]: # 展示最近7天
        date_str = f.replace("hf_daily_report_", "").replace(".html", "")
        links.append(f'<li><a href="{f}" style="text-decoration:none; color:#6366f1; background:white; padding:5px 12px; border-radius:8px; border:1px solid #eee; font-size:0.9rem;">{date_str}</a></li>')
    return "\n".join(links)

def generate_html(data):
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    trending = data.get("trending_models", [])[:10]
    tech_dist = data.get("statistics", {}).get("tech_distribution", {})
    by_category = data.get("by_category", {})
    
    # 1. 计算统计数据
    total_models = sum(tech_dist.values())
    tech_count = len(tech_dist)
    llm_count = tech_dist.get("语言模型", 0)
    llm_ratio = (llm_count / total_models * 100) if total_models > 0 else 0
    
    # 2. 生成趋势分析文字 (保留原始逻辑)
    top_tech = sorted(tech_dist.items(), key=lambda x: x[1], reverse=True)[:3]
    trend_summary = f"今日 Hugging Face 社区共分析了 {total_models} 个活跃模型。其中，"
    trend_summary += "、".join([f"<strong>{k}</strong> ({v}个)" for k, v in top_tech])
    trend_summary += f" 位居前三。语言模型占比达 {llm_ratio:.1f}%，显示出大语言模型依然是当前 AI 发展的核心驱动力。"

    # 3. 生成今日热榜表格 (植入超链接)
    table_rows = ""
    for i, model in enumerate(trending, 1):
        rank_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
        full_id = model.get("id", "unknown")
        name = full_id.split("/")[-1]
        category = model.get("tech_category", "其他")
        downloads = model.get("downloads", 0)
        author = model.get("author", "unknown")
        
        # 链接处理
        model_url = model.get("url", f"https://huggingface.co/{full_id}")
        author_url = model.get("author_url", f"https://huggingface.co/{author}")
        cat_tag = HF_TAG_MAP.get(category, "")
        cat_url = f"https://huggingface.co/models?pipeline_tag={cat_tag}" if cat_tag else "#"
        
        downloads_str = f"{downloads/1000:.1f}K" if downloads < 1e6 else f"{downloads/1e6:.1f}M"
        
        table_rows += f"""
            <tr>
                <td class="rank">{rank_icon}</td>
                <td class="model-name"><a href="{model_url}" target="_blank" style="text-decoration:none; color:#333; font-weight:600;">{name}</a></td>
                <td><a href="{cat_url}" target="_blank" style="text-decoration:none;"><span class="category-tag">{category}</span></a></td>
                <td class="downloads">{downloads_str}</td>
                <td class="author"><a href="{author_url}" target="_blank" style="text-decoration:none; color:#888;">{author}</a></td>
            </tr>
        """

    # 4. 生成分类展示区块 (保留原始逻辑 + 植入超链接)
    category_sections = ""
    for category, models in by_category.items():
        if not models: continue
        cat_tag = HF_TAG_MAP.get(category, "")
        cat_url = f"https://huggingface.co/models?pipeline_tag={cat_tag}" if cat_tag else "#"
        
        model_list_html = ""
        for m in models[:5]: # 每个分类展示前5个
            m_name = m.get("id", "").split("/")[-1]
            m_url = m.get("url", f"https://huggingface.co/{m.get('id')}")
            m_author = m.get("author", "unknown")
            m_author_url = m.get("author_url", f"https://huggingface.co/{m_author}")
            
            model_list_html += f"""
                <div style="padding:10px; border-bottom:1px solid #f0f0f0; display:flex; justify-content:space-between; align-items:center;">
                    <a href="{m_url}" target="_blank" style="text-decoration:none; color:#444; font-weight:500;">{m_name}</a>
                    <a href="{m_author_url}" target="_blank" style="text-decoration:none; color:#999; font-size:0.85rem;">@{m_author}</a>
                </div>
            """
        
        category_sections += f"""
            <div class="card" style="flex: 1 1 300px; margin: 10px;">
                <h3 style="border-left:4px solid #6366f1; padding-left:10px; margin-bottom:15px;">
                    <a href="{cat_url}" target="_blank" style="text-decoration:none; color:#333;">{category}</a>
                </h3>
                {model_list_html}
            </div>
        """

    archive_links = get_archive_links()

    # 5. 完整 HTML 模板 (保留原始精美样式)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HF 热榜日报 - {date}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f7f9; color: #333; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 50px 20px; border-radius: 24px; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 25px; border-radius: 20px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: transform 0.3s; }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-card .num {{ font-size: 2.5rem; font-weight: 800; color: #667eea; margin-bottom: 5px; }}
        .card {{ background: white; padding: 30px; border-radius: 24px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; padding: 18px; background: #f8f9fa; color: #666; font-weight: 600; }}
        td {{ padding: 18px; border-bottom: 1px solid #eee; }}
        .category-tag {{ background: #6366f1; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; }}
        .downloads {{ color: #6366f1; font-weight: 700; }}
        .img-container {{ text-align: center; margin-top: 20px; }}
        .img-container img {{ max-width: 100%; border-radius: 20px; cursor: zoom-in; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
        .archive-list {{ list-style: none; display: flex; flex-wrap: wrap; gap: 12px; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="font-size: 2.8rem; margin-bottom: 10px;">🔥 Hugging Face 技术日报</h1>
            <p style="font-size: 1.2rem; opacity: 0.9;">探索全球最前沿的 AI 模型动态</p>
            <div style="margin-top:20px; background:rgba(255,255,255,0.2); display:inline-block; padding:8px 25px; border-radius:30px;">📅 {date}</div>
        </div>

        <div class="stats-grid">
            <div class="stat-card"><div class="num">{len(trending)}</div><div style="color:#666;">热门模型</div></div>
            <div class="stat-card"><div class="num">{tech_count}</div><div style="color:#666;">技术领域</div></div>
            <div class="stat-card"><div class="num">{total_models}</div><div style="color:#666;">分析样本</div></div>
            <div class="stat-card"><div class="num">{llm_ratio:.0f}%</div><div style="color:#666;">语言模型占比</div></div>
        </div>

        <div class="card">
            <h2 style="margin-bottom:20px; display:flex; align-items:center;">📢 趋势分析</h2>
            <p style="font-size:1.1rem; color:#444; background:#f8f9fa; padding:20px; border-radius:15px; border-left:5px solid #667eea;">{trend_summary}</p>
        </div>

        <div class="card">
            <h2 style="margin-bottom:20px;">📈 今日热榜 Top 10</h2>
            <table>
                <thead><tr><th>排名</th><th>模型名称</th><th>技术领域</th><th>下载量</th><th>作者</th></tr></thead>
                <tbody>{table_rows}</tbody>
            </table>
        </div>

        <div style="display: flex; flex-wrap: wrap; margin: 0 -10px;">
            {category_sections}
        </div>

        <div class="card" style="text-align:center;">
            <h2 style="margin-bottom:20px;">📊 活跃组织排行 (Top 20)</h2>
            <div class="img-container"><img src="org_ranking_{date}.png" onclick="window.open(this.src)"></div>
        </div>

        <div class="card" style="text-align:center;">
            <h2 style="margin-bottom:20px;">📉 技术领域趋势 (最近30天)</h2>
            <div class="img-container"><img src="trend_chart_{date}.png" onclick="window.open(this.src)"></div>
        </div>

        <div class="card">
            <h2 style="margin-bottom:15px;">📂 历史报告归档</h2>
            <ul class="archive-list">{archive_links}</ul>
        </div>
    </div>
</body>
</html>
"""
    with open(os.path.join(ROOT_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(html)
    with open(os.path.join(ROOT_DIR, f"hf_daily_report_{date}.html"), 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    data = load_data()
    if data:
        generate_html(data)
