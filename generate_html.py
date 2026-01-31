#!/usr/bin/env python3
"""
生成 HTML 报告页面 (终极整合版)
功能：支持模型、作者、技术标签的超链接跳转
"""

import json
import os
from datetime import datetime

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

def generate_html(data):
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    trending = data.get("trending_models", [])[:15] # 展示前15名
    
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
                <td style="padding:15px; border-bottom:1px solid #eee;">{rank_icon}</td>
                <td style="padding:15px; border-bottom:1px solid #eee;">
                    <a href="{model_url}" target="_blank" style="text-decoration:none; color:#333; font-weight:bold;">{name}</a>
                </td>
                <td style="padding:15px; border-bottom:1px solid #eee;">
                    <a href="{cat_url}" target="_blank" style="text-decoration:none;">
                        <span style="background:#6366f1; color:white; padding:4px 10px; border-radius:10px; font-size:0.8rem;">{category}</span>
                    </a>
                </td>
                <td style="padding:15px; border-bottom:1px solid #eee; color:#6366f1; font-weight:600;">{downloads_str}</td>
                <td style="padding:15px; border-bottom:1px solid #eee;">
                    <a href="{author_url}" target="_blank" style="text-decoration:none; color:#888;">{author}</a>
                </td>
            </tr>
        """
    
    # 简化版 HTML 模板 (保留核心样式)
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>HF 热榜日报 - {date}</title>
        <style>
            body {{ font-family: sans-serif; background: #f4f7f6; padding: 20px; }}
            .card {{ background: white; border-radius: 15px; padding: 25px; max-width: 1000px; margin: 20px auto; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ text-align: left; padding: 15px; background: #f8f9fa; color: #666; }}
        </style>
    </head>
    <body>
        <div style="text-align:center; margin-bottom:40px;">
            <h1 style="color:#333;">🔥 Hugging Face 技术日报</h1>
            <p style="color:#666;">日期：{date} | 自动更新</p>
        </div>
        
        <div class="card">
            <h2>📈 今日热门模型 Top 15</h2>
            <table>
                <thead>
                    <tr><th>排名</th><th>模型名称</th><th>技术领域</th><th>下载量</th><th>作者</th></tr>
                </thead>
                <tbody>{table_rows}</tbody>
            </table>
        </div>
        
        <div class="card" style="text-align:center;">
            <h2>📊 活跃组织排行</h2>
            <img src="org_ranking_{date}.png" style="max-width:100%; border-radius:10px;">
        </div>

        <div class="card" style="text-align:center;">
            <h2>📉 技术领域趋势 (30天)</h2>
            <img src="trend_chart_{date}.png" style="max-width:100%; border-radius:10px;">
        </div>
    </body>
    </html>
    """
    
    with open(os.path.join(ROOT_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    data = load_data()
    if data:
        generate_html(data)
