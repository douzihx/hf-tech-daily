#!/usr/bin/env python3
"""
生成 HTML 报告页面 (100% 样式保留版)
更新: 增加精美交互式技术关键字词云，支持点击跳转到 Hugging Face 搜索
修复：1) 植入超链接 2) 植入交互式标签云 3) 保持原始精美样式与所有图表
"""

import json
import os
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
    
    files = [f for f in os.listdir(ROOT_DIR) if f.startswith("hf_data_") and f.endswith(".json")]
    if files:
        filepath = os.path.join(ROOT_DIR, sorted(files)[-1])
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# ========== 新增: 生成精美交互式词云 HTML ==========
def generate_keyword_cloud_html(tech_keywords: dict) -> str:
    """根据技术关键字热度生成精美交互式词云 HTML"""
    if not tech_keywords:
        return '<p style="color:#999; text-align:center;">暂无技术关键字数据</p>'
    
    # 按热度排序
    sorted_keywords = sorted(tech_keywords.items(), key=lambda x: x[1], reverse=True)
    max_count = max(tech_keywords.values()) if tech_keywords else 1
    
    # 分级阈值
    hot_threshold = max_count * 0.7      # 超热门
    warm_threshold = max_count * 0.4     # 热门
    medium_threshold = max_count * 0.2   # 上升中
    
    cloud_items = []
    for keyword, count in sorted_keywords[:30]:  # 最多显示30个
        # 生成搜索链接
        url = f"https://huggingface.co/models?search={keyword}"
        
        # 根据热度分配样式类
        if count >= hot_threshold:
            css_class = "kw-hot"
        elif count >= warm_threshold:
            css_class = "kw-warm"
        elif count >= medium_threshold:
            css_class = "kw-medium"
        else:
            css_class = "kw-normal"
        
        cloud_items.append(f'<a href="{url}" target="_blank" class="{css_class}">{keyword}</a>')
    
    return '\n'.join(cloud_items)

def generate_html(data):
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    trending = data.get("trending_models", [])[:10]
    tech_dist = data.get("statistics", {}).get("tech_distribution", {})
    tech_keywords = data.get("statistics", {}).get("tech_keywords", {})  # 新增
    
    total_models = len(data.get("trending_models", [])) + len(data.get("most_downloaded", [])) + len(data.get("most_liked", []))
    tech_count = len(tech_dist)
    llm_ratio = tech_dist.get("语言模型", 0) / sum(tech_dist.values()) * 100 if tech_dist and sum(tech_dist.values()) > 0 else 0
    
    archive_links = ""
    files = sorted([f for f in os.listdir(ROOT_DIR) if f.startswith("hf_data_") and f.endswith(".json")])
    for filename in files[-7:]:
        date_str = filename.replace("hf_data_", "").replace(".json", "")
        archive_links += f'<li style="padding: 8px 0; border-bottom: 1px solid #eee;"><a href="?date={date_str}" style="color: #667eea; text-decoration: none;">{date_str}</a></li>\n'
    
    if not archive_links:
        archive_links = '<li style="padding: 8px 0; color: #999;">暂无历史数据</li>' 
    
    # 生成交互式标签云 (技术领域分类)
    tag_cloud_html = ""
    if tech_dist:
        max_count = max(tech_dist.values())
        for tech, count in sorted(tech_dist.items(), key=lambda x: x[1], reverse=True):
            tag = HF_TAG_MAP.get(tech, "")
            url = f"https://huggingface.co/models?pipeline_tag={tag}" if tag else "#"
            font_size = 0.8 + (count / max_count) * 1.0
            tag_cloud_html += f'<a href="{url}" target="_blank" style="text-decoration:none; display:inline-block; margin:5px 10px; font-size:{font_size:.2f}rem; color:#6366f1; font-weight:bold;">{tech}</a> '

    # ========== 新增: 生成精美技术关键字词云 ==========
    keyword_cloud_html = generate_keyword_cloud_html(tech_keywords)

    table_rows = ""
    for i, model in enumerate(trending, 1):
        rank_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
        full_id = model.get("id", "")
        name = full_id.split("/")[-1]
        category = model.get("tech_category", "其他")
        downloads = model.get("downloads", 0)
        likes = model.get("likes", 0)
        author = model.get("author", "unknown")
        
        # 植入超链接
        model_url = model.get("url", f"https://huggingface.co/{full_id}")
        author_url = model.get("author_url", f"https://huggingface.co/{author}")
        cat_tag = HF_TAG_MAP.get(category, "")
        cat_url = f"https://huggingface.co/models?pipeline_tag={cat_tag}" if cat_tag else "#"
        
        downloads_str = f"{downloads/1000:.1f}K" if downloads < 1e6 else f"{downloads/1e6:.1f}M"
        
        category_colors = {
            "语言模型": "#6366f1", "多模态模型": "#14b8a6", "图像生成": "#3b82f6",
            "语音合成": "#f59e0b", "语音识别": "#a855f7", "其他": "#6b7280"
        }
        cat_color = category_colors.get(category, "#6b7280")
        
        table_rows += f"""
            <tr>
                <td class="rank">{rank_icon}</td>
                <td class="model-name"><a href="{model_url}" target="_blank" style="text-decoration:none; color:#333; font-weight:600;">{name}</a></td>
                <td><a href="{cat_url}" target="_blank" style="text-decoration:none;"><span class="category-tag" style="background-color: {cat_color}">{category}</span></a></td>
                <td class="downloads">{downloads_str}</td>
                <td class="likes">{likes}</td>
                <td class="author"><a href="{author_url}" target="_blank" style="text-decoration:none; color:#888;">{author}</a></td>
            </tr>
        """
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HF 热榜日报 - Hugging Face 热门 AI 技术分析</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
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
            font-size: 0.85rem;
        }}
        .downloads {{ color: #667eea; font-weight: 600; }}
        .likes {{ color: #e91e63; }}
        .author {{ color: #888; font-size: 0.9rem; }}
        .image-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 20px 0;
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
            font-size: 1.2rem;
        }}
        .image-card img {{
            width: 100%;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .image-card img:hover {{
            transform: scale(1.02);
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }}
        .trends {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin: 20px 0;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .trends h2 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .trends ul {{
            list-style: none;
        }}
        .trends li {{
            padding: 12px 0;
            border-bottom: 1px solid #eee;
            color: #555;
            line-height: 1.6;
        }}
        .trends li:last-child {{
            border-bottom: none;
        }}
        .footer {{
            text-align: center;
            color: white;
            padding: 30px;
            opacity: 0.9;
        }}
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
            cursor: pointer;
        }}
        .modal-content {{
            margin: auto;
            display: block;
            max-width: 90%;
            max-height: 90%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            border-radius: 8px;
            box-shadow: 0 0 30px rgba(255,255,255,0.2);
        }}
        .modal-close {{
            position: absolute;
            top: 20px;
            right: 35px;
            color: #fff;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            z-index: 1001;
        }}
        .modal-title {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: white;
            font-size: 1.2rem;
            text-align: center;
            background: rgba(0,0,0,0.5);
            padding: 10px 20px;
            border-radius: 8px;
        }}
        .click-hint {{
            text-align: center;
            color: #888;
            font-size: 0.85rem;
            margin-top: 8px;
        }}
        .tag-cloud {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
            margin-top: 15px;
        }}
        
        /* ========== 新增: 精美技术关键字词云样式 ========== */
        .keyword-cloud-container {{
            position: relative;
            background: 
                radial-gradient(ellipse at 20% 30%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 70%, rgba(236, 72, 153, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(20, 184, 166, 0.06) 0%, transparent 60%),
                linear-gradient(180deg, #fafbff 0%, #fff 100%);
            border-radius: 20px;
            padding: 35px 25px;
            min-height: 200px;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            gap: 8px 12px;
            border: 1px solid rgba(102, 126, 234, 0.15);
            box-shadow: inset 0 2px 15px rgba(102, 126, 234, 0.05);
        }}
        .keyword-cloud-container a {{
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            padding: 6px 14px;
            border-radius: 10px;
            display: inline-block;
            letter-spacing: 0.5px;
        }}
        .keyword-cloud-container a:hover {{
            transform: scale(1.12) translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        /* 超热门 */
        .kw-hot {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            font-size: 1.6rem;
            padding: 10px 18px;
            border-radius: 14px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }}
        .kw-hot:hover {{
            box-shadow: 0 10px 35px rgba(102, 126, 234, 0.5) !important;
        }}
        /* 热门 */
        .kw-warm {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white !important;
            font-size: 1.35rem;
            padding: 8px 15px;
            box-shadow: 0 3px 12px rgba(245, 87, 108, 0.3);
        }}
        /* 上升中 */
        .kw-medium {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white !important;
            font-size: 1.15rem;
            box-shadow: 0 3px 10px rgba(79, 172, 254, 0.3);
        }}
        /* 一般 */
        .kw-normal {{
            background: rgba(102, 126, 234, 0.1);
            color: #667eea !important;
            font-size: 1rem;
        }}
        .kw-normal:hover {{
            background: rgba(102, 126, 234, 0.2);
        }}
        
        .keyword-legend {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        .keyword-legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.8rem;
            color: #666;
        }}
        .keyword-legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 4px;
        }}
        .keyword-legend-dot.hot {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .keyword-legend-dot.warm {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .keyword-legend-dot.medium {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
        .keyword-legend-dot.normal {{ background: rgba(102, 126, 234, 0.3); }}
        
        .keyword-hint {{
            text-align: center;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px dashed rgba(102, 126, 234, 0.2);
        }}
        .keyword-hint .badge {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 8px;
        }}
        .keyword-hint .text {{
            color: #888;
            font-size: 0.85rem;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.8rem; }}
            .image-grid {{ grid-template-columns: 1fr; }}
            th, td {{ padding: 10px 5px; font-size: 0.9rem; }}
            .kw-hot {{ font-size: 1.3rem; padding: 8px 14px; }}
            .kw-warm {{ font-size: 1.15rem; }}
            .kw-medium {{ font-size: 1rem; }}
            .kw-normal {{ font-size: 0.9rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 HF 热榜日报</h1>
            <p>Hugging Face 热门 AI 技术分析报告</p>
            <div class="date-badge">
                📅 {date}   |   🏠 数据来源: Hugging Face Hub
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
        
        <!-- ========== 新增: 精美技术关键字词云 ========== -->
        <div class="card">
            <h2>🎨 技术热点词云</h2>
            <p style="color:#666; font-size:0.9rem; margin-bottom:15px;">基于热门模型标签实时提取的技术关键字，字体越大表示热度越高</p>
            <div class="keyword-cloud-container">
                {keyword_cloud_html}
            </div>
            <div class="keyword-legend">
                <div class="keyword-legend-item"><span class="keyword-legend-dot hot"></span> 超热门</div>
                <div class="keyword-legend-item"><span class="keyword-legend-dot warm"></span> 热门</div>
                <div class="keyword-legend-item"><span class="keyword-legend-dot medium"></span> 上升中</div>
                <div class="keyword-legend-item"><span class="keyword-legend-dot normal"></span> 稳定</div>
            </div>
            <div class="keyword-hint">
                <span class="badge">✨ 可点击</span>
                <span class="text">点击任意标签，即可跳转至 Hugging Face 查看相关模型</span>
            </div>
        </div>
        
        <!-- 原有词云图片 (保留兼容) -->
        <div class="card" style="display:none;">
            <h2>🎨 技术词云 (图片版)</h2>
            <img src="wordcloud_{date}.png" alt="技术词云" class="zoomable" data-title="Hugging Face 技术词云 - {date}" style="width: 100%; border-radius: 8px; cursor: pointer;" onerror="this.parentElement.style.display='none'">
            <div class="tag-cloud">
                <p style="color:#666; font-size:0.9rem; margin-bottom:10px;">👇 点击下方标签可直接跳转至 HF 对应领域</p>
                {tag_cloud_html}
            </div>
            <p class="click-hint">👆 点击图片可放大查看</p>
        </div>
        
        <div class="image-grid">
            <div class="image-card">
                <h3>📊 Top Models Leaderboard</h3>
                <img src="leaderboard_{date}.png" alt="排行榜" class="zoomable" data-title="Top Models Leaderboard - {date}" onerror="this.parentElement.style.display='none'">
                <p class="click-hint">👆 点击图片可放大查看</p>
            </div>
            <div class="image-card">
                <h3>📈 Tech Distribution</h3>
                <img src="tech_distribution_{date}.png" alt="技术分布" class="zoomable" data-title="Tech Distribution - {date}" onerror="this.parentElement.style.display='none'">
                <p class="click-hint">👆 点击图片可放大查看</p>
            </div>
        </div>
        
        <div class="image-grid">
            <div class="image-card">
                <h3>🔵 Model Popularity Bubble Chart</h3>
                <img src="bubble_chart_{date}.png" alt="气泡图" class="zoomable" data-title="Model Popularity Bubble Chart - {date}" onerror="this.parentElement.style.display='none'">
                <p class="click-hint">👆 点击图片可放大查看</p>
            </div>
            <div class="image-card">
                <h3>🏙 Active Organizations Ranking</h3>
                <img src="org_ranking_{date}.png" alt="组织排行" class="zoomable" data-title="Active Organizations Ranking - {date}" onerror="this.parentElement.style.display='none'">
                <p class="click-hint">👆 点击图片可放大查看</p>
            </div>
        </div>
        
        <div class="card">
            <h2>📈 技术领域趋势分析</h2>
            <img src="trend_chart_{date}.png" alt="技术趋势" class="zoomable" data-title="Tech Trends - {date}" style="width: 100%; border-radius: 8px; cursor: pointer;" onerror="this.parentElement.style.display='none'">
            <p class="click-hint">👆 点击图片可放大查看</p>
        </div>
        
        <div class="trends">
            <h2>📝 技术趋势观察</h2>
            <ul>
                <li>🚀 <strong>语言模型 (LLM)</strong>仍是最热门的技术方向，但多模态模型增长迅速</li>
                <li>🎙️ <strong>语音技术</strong>(TTS/ASR) 近期热度上升，多个新模型上榜</li>
                <li>🎈 <strong>图像生成</strong>领域持续活跃，Diffusion 模型占据主导地位</li>
                <li>📄 <strong>OCR/文档理解</strong>成为新的增长点，DeepSeek-OCR 等模型表现亮眼</li>
            </ul>
        </div>
        
        <div class="card">
            <h2>📂 历史数据归档</h2>
            <p>本系统每日自动生成报告并保存数据。下方是最近 7 天的报告归档。</p>
            <div style="margin-top: 15px;">
                <ul style="list-style: none; padding: 0;">
                    {archive_links}
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>本报告由 Hugging Face 热门技术分析系统自动生成</p>
            <p>每日早上 9:00 自动更新</p>
        </div>
    </div>
    
    <div id="imageModal" class="modal" onclick="closeModal()">
        <span class="modal-close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImage">
        <div class="modal-title" id="modalTitle"></div>
    </div>
    
    <script>
        document.querySelectorAll('.zoomable').forEach(function(img) {{
            img.addEventListener('click', function() {{
                var modal = document.getElementById('imageModal');
                var modalImg = document.getElementById('modalImage');
                var modalTitle = document.getElementById('modalTitle');
                modal.style.display = 'block';
                modalImg.src = this.src;
                modalTitle.textContent = this.getAttribute('data-title') || this.alt;
            }});
        }});
        function closeModal() {{
            document.getElementById('imageModal').style.display = 'none';
        }}
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') {{
                closeModal();
            }}
        }});
    </script>
</body>
</html>
"""
    output_path = os.path.join(ROOT_DIR, "index.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return output_path

if __name__ == "__main__":
    data = load_data()
    if data:
        generate_html(data)
