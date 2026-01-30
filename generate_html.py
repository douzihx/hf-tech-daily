#!/usr/bin/env python3
"""
生成 HTML 报告页面 (GitHub Actions 版本)
"""

import json
import os
from datetime import datetime

# 使用当前工作目录
ROOT_DIR = os.getcwd()

def load_data():
    print(f"当前工作目录: {ROOT_DIR}")
    print(f"目录内容: {os.listdir(ROOT_DIR)}")
    
    # 首先尝试 latest.json
    latest_path = os.path.join(ROOT_DIR, "latest.json")
    if os.path.exists(latest_path):
        print(f"找到 latest.json: {latest_path}")
        with open(latest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 尝试 hf_data_*.json 文件
    files = [f for f in os.listdir(ROOT_DIR) if f.startswith("hf_data_") and f.endswith(".json")]
    if files:
        filepath = os.path.join(ROOT_DIR, sorted(files)[-1])
        print(f"找到数据文件: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    print("没有找到数据文件!")
    return None

def generate_html(data):
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    trending = data.get("trending_models", [])[:10]
    tech_dist = data.get("statistics", {}).get("tech_distribution", {})
    
    # 计算统计数据
    total_models = len(data.get("trending_models", [])) + len(data.get("most_downloaded", [])) + len(data.get("most_liked", []))
    tech_count = len(tech_dist)
    llm_ratio = tech_dist.get("语言模型", 0) / sum(tech_dist.values()) * 100 if tech_dist and sum(tech_dist.values()) > 0 else 0
    
    # 生成表格行
    table_rows = ""
    for i, model in enumerate(trending, 1):
        rank_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
        name = model.get("id", "").split("/")[-1]
        category = model.get("tech_category", "其他")
        downloads = model.get("downloads", 0)
        likes = model.get("likes", 0)
        author = model.get("author", "unknown")
        
        downloads_str = f"{downloads/1000:.1f}K" if downloads < 1e6 else f"{downloads/1e6:.1f}M"
        
        category_colors = {
            "语言模型": "#6366f1", "多模态模型": "#14b8a6", "图像生成": "#3b82f6",
            "语音合成": "#f59e0b", "语音识别": "#a855f7", "其他": "#6b7280"
        }
        cat_color = category_colors.get(category, "#6b7280")
        
        table_rows += f"""
            <tr>
                <td class="rank">{rank_icon}</td>
                <td class="model-name"><strong>{name}</strong></td>
                <td><span class="category-tag" style="background-color: {cat_color}">{category}</span></td>
                <td class="downloads">{downloads_str}</td>
                <td class="likes">{likes}</td>
                <td class="author">{author}</td>
            </tr>
        """
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 HF 热榜日报 - Hugging Face 热门 AI 技术分析</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            text-align: center;
            color: white;
            padding: 40px 20px;
        }}
        .header h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
        .header p {{ font-size: 1.1rem; opacity: 0.9; }}
        .date-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 8px 20px;
            border-radius: 20px;
            margin-top: 15px;
            font-size: 0.9rem;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .stat-card .number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-card .label {{
            color: #666;
            margin-top: 5px;
        }}
        .card {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin: 20px 0;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .card h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 15px 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}
        .rank {{ font-size: 1.2rem; width: 60px; }}
        .model-name {{ color: #333; }}
        .category-tag {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            color: white;
            font-size: 0.8rem;
        }}
        .downloads, .likes {{ color: #666; }}
        .author {{ color: #888; font-size: 0.9rem; }}
        .image-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}
        .image-card {{
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .image-card h3 {{
            color: #333;
            margin-bottom: 15px;
            text-align: center;
        }}
        .image-card img {{
            width: 100%;
            border-radius: 8px;
        }}
        .trends {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin: 20px 0;
        }}
        .trends h2 {{ color: #333; margin-bottom: 20px; }}
        .trends ul {{ list-style: none; }}
        .trends li {{
            padding: 12px 0;
            border-bottom: 1px solid #eee;
            color: #555;
        }}
        .trends li:last-child {{ border-bottom: none; }}
        .footer {{
            text-align: center;
            color: white;
            padding: 30px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 HF 热榜日报</h1>
            <p>Hugging Face 热门 AI 技术分析报告</p>
            <div class="date-badge">
                📅 {date} &nbsp;&nbsp;|&nbsp;&nbsp; 🏠 数据来源: Hugging Face Hub
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">{len(trending)}</div>
                <div class="label">热门模型</div>
            </div>
            <div class="stat-card">
                <div class="number">{tech_count}</div>
                <div class="label">技术领域</div>
            </div>
            <div class="stat-card">
                <div class="number">{total_models}+</div>
                <div class="label">分析模型数</div>
            </div>
            <div class="stat-card">
                <div class="number">{llm_ratio:.0f}%</div>
                <div class="label">语言模型占比</div>
            </div>
        </div>
        
        <div class="card">
            <h2>📈 今日热榜 Top 10</h2>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>模型名称</th>
                        <th>技术领域</th>
                        <th>下载量</th>
                        <th>点赞数</th>
                        <th>作者</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>🎨 技术词云</h2>
            <img src="wordcloud_{date}.png" alt="技术词云" style="width: 100%; border-radius: 8px;" onerror="this.style.display='none'">
        </div>
        
        <div class="image-grid">
            <div class="image-card">
                <h3>热门模型排行榜</h3>
                <img src="leaderboard_{date}.png" alt="排行榜" onerror="this.style.display='none'">
            </div>
            <div class="image-card">
                <h3>技术领域分布</h3>
                <img src="tech_distribution_{date}.png" alt="技术分布" onerror="this.style.display='none'">
            </div>
        </div>
        
        <div class="image-grid">
            <div class="image-card">
                <h3>模型热度分布（气泡图）</h3>
                <img src="bubble_chart_{date}.png" alt="气泡图" onerror="this.style.display='none'">
            </div>
            <div class="image-card">
                <h3>活跃组织排行</h3>
                <img src="org_ranking_{date}.png" alt="组织排行" onerror="this.style.display='none'">
            </div>
        </div>
        
        <div class="trends">
            <h2>📝 技术趋势观察</h2>
            <ul>
                <li>🚀 <strong>语言模型 (LLM)</strong>仍是最热门的技术方向，但多模态模型增长迅速</li>
                <li>🎙️ <strong>语音技术</strong>(TTS/ASR) 近期热度上升，多个新模型上榜</li>
                <li>🎨 <strong>图像生成</strong>领域持续活跃，Diffusion 模型占据主导地位</li>
                <li>📄 <strong>OCR/文档理解</strong>成为新的增长点，DeepSeek-OCR 等模型表现亮眼</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>本报告由 Hugging Face 热门技术分析系统自动生成</p>
            <p>每日早上 9:00 自动更新</p>
        </div>
    </div>
</body>
</html>
"""
    
    output_path = os.path.join(ROOT_DIR, "index.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTML 报告已生成: {output_path}")
    return output_path

def main():
    data = load_data()
    if not data:
        print("没有找到数据文件，创建默认数据...")
        data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "trending_models": [],
            "statistics": {"tech_distribution": {}}
        }
    
    generate_html(data)

if __name__ == "__main__":
    main()
