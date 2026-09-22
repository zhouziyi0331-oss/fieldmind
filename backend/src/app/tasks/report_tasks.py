"""
报告生成任务 - 可视化和文档导出
"""
from app.celery_app import celery_app
from typing import Dict, Any, List
import os
from datetime import datetime
from pathlib import Path


@celery_app.task(name="app.tasks.report_tasks.create_visualization")
def create_visualization(data: Dict[str, Any], chart_type: str) -> Dict[str, Any]:
    """
    创建数据可视化
    使用 pyecharts 生成图表
    """
    try:
        from pyecharts import options as opts
        from pyecharts.charts import Bar, Line, Pie, Scatter, Graph, Map
        import json

        output_dir = os.getenv("VISUALIZATION_OUTPUT_DIR", "./data/visualizations")
        os.makedirs(output_dir, exist_ok=True)

        chart = None

        if chart_type == "bar":
            chart = Bar()
            chart.add_xaxis(data.get("x_axis", []))
            chart.add_yaxis(data.get("series_name", "数据"), data.get("y_axis", []))
            chart.set_global_opts(title_opts=opts.TitleOpts(title=data.get("title", "柱状图")))

        elif chart_type == "line":
            chart = Line()
            chart.add_xaxis(data.get("x_axis", []))
            chart.add_yaxis(data.get("series_name", "数据"), data.get("y_axis", []))
            chart.set_global_opts(title_opts=opts.TitleOpts(title=data.get("title", "折线图")))

        elif chart_type == "pie":
            chart = Pie()
            chart.add("", list(zip(data.get("labels", []), data.get("values", []))))
            chart.set_global_opts(title_opts=opts.TitleOpts(title=data.get("title", "饼图")))

        elif chart_type == "graph":
            # 知识图谱可视化
            nodes = [{"name": node["name"], "symbolSize": node.get("size", 20)}
                    for node in data.get("nodes", [])]
            links = [{"source": link["source"], "target": link["target"]}
                    for link in data.get("links", [])]

            chart = Graph()
            chart.add("", nodes, links, repulsion=8000)
            chart.set_global_opts(title_opts=opts.TitleOpts(title=data.get("title", "知识图谱")))

        elif chart_type == "wordcloud":
            from pyecharts.charts import WordCloud
            chart = WordCloud()
            chart.add("", data.get("words", []), word_size_range=[20, 100])
            chart.set_global_opts(title_opts=opts.TitleOpts(title=data.get("title", "词云")))

        else:
            return {
                "success": False,
                "error": f"Unsupported chart type: {chart_type}",
            }

        # 保存为 HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{chart_type}_{timestamp}.html"
        filepath = os.path.join(output_dir, filename)

        chart.render(filepath)

        return {
            "success": True,
            "chart_type": chart_type,
            "filepath": filepath,
            "created_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Visualization creation failed: {str(e)}",
        }


@celery_app.task(name="app.tasks.report_tasks.create_map")
def create_map(locations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    创建地图可视化（田野调查位置）
    使用 folium
    """
    try:
        import folium

        # 计算中心点
        if not locations:
            return {
                "success": False,
                "error": "No locations provided",
            }

        avg_lat = sum(loc["lat"] for loc in locations) / len(locations)
        avg_lon = sum(loc["lon"] for loc in locations) / len(locations)

        # 创建地图
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=10)

        # 添加标记
        for loc in locations:
            folium.Marker(
                location=[loc["lat"], loc["lon"]],
                popup=loc.get("name", "位置"),
                tooltip=loc.get("description", ""),
                icon=folium.Icon(color=loc.get("color", "blue"))
            ).add_to(m)

        # 保存
        output_dir = os.getenv("VISUALIZATION_OUTPUT_DIR", "./data/visualizations")
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"map_{timestamp}.html"
        filepath = os.path.join(output_dir, filename)

        m.save(filepath)

        return {
            "success": True,
            "locations_count": len(locations),
            "filepath": filepath,
            "created_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Map creation failed: {str(e)}",
        }


@celery_app.task(name="app.tasks.report_tasks.export_to_word")
def export_to_word(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    导出为 Word 文档
    使用 python-docx
    """
    try:
        from docx import Document
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()

        # 添加标题
        title = content.get("title", "研究报告")
        doc.add_heading(title, level=0)

        # 添加元数据
        metadata = content.get("metadata", {})
        if metadata:
            meta_para = doc.add_paragraph()
            meta_para.add_run(f"生成时间: {metadata.get('created_at', '')}\n")
            meta_para.add_run(f"作者: {metadata.get('author', '未知')}\n")

        # 添加摘要
        if "summary" in content:
            doc.add_heading("摘要", level=1)
            doc.add_paragraph(content["summary"])

        # 添加章节
        for section in content.get("sections", []):
            doc.add_heading(section.get("title", ""), level=section.get("level", 1))
            doc.add_paragraph(section.get("content", ""))

            # 插入图片
            if "image" in section:
                if os.path.exists(section["image"]):
                    doc.add_picture(section["image"], width=Inches(5))

        # 添加参考文献
        if "references" in content:
            doc.add_heading("参考文献", level=1)
            for ref in content["references"]:
                doc.add_paragraph(ref, style="List Number")

        # 保存
        output_dir = os.getenv("REPORT_OUTPUT_DIR", "./data/reports")
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{content.get('filename', 'report')}_{timestamp}.docx"
        filepath = os.path.join(output_dir, filename)

        doc.save(filepath)

        return {
            "success": True,
            "format": "docx",
            "filepath": filepath,
            "created_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Word export failed: {str(e)}",
        }


@celery_app.task(name="app.tasks.report_tasks.export_to_pdf")
def export_to_pdf(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    导出为 PDF
    使用 weasyprint (HTML → PDF)
    """
    try:
        from weasyprint import HTML, CSS
        from jinja2 import Template

        # 使用 Jinja2 模板生成 HTML
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: 'SimSun', serif;
                    margin: 2cm;
                    line-height: 1.6;
                }
                h1 {
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }
                h2 {
                    color: #34495e;
                    margin-top: 20px;
                }
                .metadata {
                    color: #7f8c8d;
                    font-size: 0.9em;
                    margin-bottom: 20px;
                }
                .summary {
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-left: 4px solid #3498db;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <h1>{{ title }}</h1>

            <div class="metadata">
                <p>生成时间: {{ metadata.created_at }}</p>
                <p>作者: {{ metadata.author }}</p>
            </div>

            {% if summary %}
            <div class="summary">
                <h2>摘要</h2>
                <p>{{ summary }}</p>
            </div>
            {% endif %}

            {% for section in sections %}
            <h{{ section.level }}>{{ section.title }}</h{{ section.level }}>
            <p>{{ section.content }}</p>
            {% endfor %}

            {% if references %}
            <h2>参考文献</h2>
            <ol>
                {% for ref in references %}
                <li>{{ ref }}</li>
                {% endfor %}
            </ol>
            {% endif %}
        </body>
        </html>
        """

        template = Template(html_template)
        html_content = template.render(
            title=content.get("title", "研究报告"),
            metadata=content.get("metadata", {}),
            summary=content.get("summary", ""),
            sections=content.get("sections", []),
            references=content.get("references", []),
        )

        # 生成 PDF
        output_dir = os.getenv("REPORT_OUTPUT_DIR", "./data/reports")
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{content.get('filename', 'report')}_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)

        HTML(string=html_content).write_pdf(filepath)

        return {
            "success": True,
            "format": "pdf",
            "filepath": filepath,
            "created_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"PDF export failed: {str(e)}",
        }


@celery_app.task(name="app.tasks.report_tasks.generate_report")
def generate_report(query: str, include_visualizations: bool = True) -> Dict[str, Any]:
    """
    生成完整研究报告
    1. RAG 查询获取相关内容
    2. 生成可视化（可选）
    3. 导出为 Word 和 PDF

    自动触发：用户请求生成报告时调用
    """
    try:
        from app.tasks.rag_tasks import triple_retrieval_query, generate_answer
        from celery import chain

        # 步骤 1: 检索相关内容
        retrieval_result = triple_retrieval_query(query, top_k=10)

        if not retrieval_result.get("success"):
            return {
                "success": False,
                "error": "Retrieval failed",
            }

        # 步骤 2: 生成答案
        answer_result = generate_answer(query, retrieval_result["top_documents"])

        # 步骤 3: 构建报告内容
        report_content = {
            "title": f"研究报告: {query}",
            "metadata": {
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "author": "FieldMind AI",
                "query": query,
            },
            "summary": answer_result.get("answer", ""),
            "sections": [
                {
                    "title": "检索结果",
                    "level": 1,
                    "content": f"检索到 {len(retrieval_result['top_documents'])} 条相关文档。",
                },
                {
                    "title": "详细内容",
                    "level": 2,
                    "content": "\n\n".join([
                        f"{i+1}. {doc.get('content', doc.get('entity', ''))[:200]}..."
                        for i, doc in enumerate(retrieval_result["top_documents"])
                    ]),
                }
            ],
            "references": [
                doc.get("metadata", {}).get("file_path", "未知来源")
                for doc in retrieval_result["top_documents"]
            ],
            "filename": query[:30].replace(" ", "_"),
        }

        # 步骤 4: 导出
        word_result = export_to_word(report_content)
        pdf_result = export_to_pdf(report_content)

        return {
            "success": True,
            "query": query,
            "retrieval": retrieval_result,
            "answer": answer_result,
            "exports": {
                "word": word_result,
                "pdf": pdf_result,
            },
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Report generation failed: {str(e)}",
        }
