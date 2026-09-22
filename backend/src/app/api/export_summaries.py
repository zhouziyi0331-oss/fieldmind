"""
导出缩影 API 路由
Export Summaries API Routes

功能：
1. 导出单个文档缩影为 PDF
2. 导出单个文档缩影为 Word
3. 批量导出项目所有缩影为 PDF
4. 批量导出项目所有缩影为 Word

依赖：
    pip install reportlab python-docx
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import json
import logging
import os
import tempfile
from datetime import datetime

from app.core.database import get_db

router = APIRouter(prefix="/file-summaries/export", tags=["Export Summaries"])
logger = logging.getLogger(__name__)


@router.get("/documents/{document_id}/pdf")
async def export_summary_pdf(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    导出单个文档缩影为 PDF

    返回 PDF 文件下载
    """

    try:
        # 查询缩影
        result = db.execute(text("""
            SELECT s.*, d.original_filename
            FROM file_summaries s
            JOIN project_documents d ON s.document_id = d.id
            WHERE s.document_id = :document_id
        """), {'document_id': document_id}).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Summary not found")

        # 解析数据
        summary = {
            'document_title': result[-1],
            'one_line_summary': result[3],
            'full_summary': result[4],
            'top_keywords': json.loads(result[5]) if result[5] else [],
            'top_entities': json.loads(result[6]) if result[6] else [],
            'top_topics': json.loads(result[7]) if result[7] else [],
            'word_count': result[9],
            'chunk_count': result[10],
            'primary_dimension': result[14],
            'secondary_dimensions': json.loads(result[15]) if result[15] else [],
            'time_start': result[16],
            'time_end': result[17],
            'spatial_context': result[18],
            'related_documents': json.loads(result[19]) if result[19] else [],
            'generated_at': result[21]
        }

        # 生成 PDF
        pdf_path = _generate_pdf(summary)

        # 返回文件
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f"{summary['document_title']}_缩影.pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出 PDF 失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/word")
async def export_summary_word(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    导出单个文档缩影为 Word

    返回 Word 文件下载
    """

    try:
        # 查询缩影
        result = db.execute(text("""
            SELECT s.*, d.original_filename
            FROM file_summaries s
            JOIN project_documents d ON s.document_id = d.id
            WHERE s.document_id = :document_id
        """), {'document_id': document_id}).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Summary not found")

        # 解析数据
        summary = {
            'document_title': result[-1],
            'one_line_summary': result[3],
            'full_summary': result[4],
            'top_keywords': json.loads(result[5]) if result[5] else [],
            'top_entities': json.loads(result[6]) if result[6] else [],
            'top_topics': json.loads(result[7]) if result[7] else [],
            'word_count': result[9],
            'chunk_count': result[10],
            'primary_dimension': result[14],
            'secondary_dimensions': json.loads(result[15]) if result[15] else [],
            'time_start': result[16],
            'time_end': result[17],
            'spatial_context': result[18],
            'related_documents': json.loads(result[19]) if result[19] else [],
            'generated_at': result[21]
        }

        # 生成 Word
        word_path = _generate_word(summary)

        # 返回文件
        return FileResponse(
            word_path,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename=f"{summary['document_title']}_缩影.docx"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出 Word 失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/pdf")
async def export_project_summaries_pdf(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    批量导出项目所有缩影为 PDF

    返回 PDF 文件下载
    """

    try:
        # 查询所有缩影
        results = db.execute(text("""
            SELECT s.*, d.original_filename
            FROM file_summaries s
            JOIN project_documents d ON s.document_id = d.id
            WHERE s.project_id = :project_id AND s.status = 'done'
            ORDER BY s.created_at DESC
        """), {'project_id': project_id}).fetchall()

        if not results:
            raise HTTPException(status_code=404, detail="No summaries found")

        # 解析数据
        summaries = []
        for row in results:
            summaries.append({
                'document_title': row[-1],
                'one_line_summary': row[3],
                'full_summary': row[4],
                'top_keywords': json.loads(row[5]) if row[5] else [],
                'top_entities': json.loads(row[6]) if row[6] else [],
                'top_topics': json.loads(row[7]) if row[7] else [],
                'word_count': row[9],
                'chunk_count': row[10],
                'primary_dimension': row[14],
                'secondary_dimensions': json.loads(row[15]) if row[15] else [],
                'time_start': row[16],
                'time_end': row[17],
                'spatial_context': row[18],
                'related_documents': json.loads(row[19]) if row[19] else [],
                'generated_at': row[21]
            })

        # 生成 PDF
        pdf_path = _generate_batch_pdf(summaries, project_id)

        # 返回文件
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f"项目{project_id}_所有缩影.pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量导出 PDF 失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _generate_pdf(summary: dict) -> str:
    """生成单个缩影的 PDF"""

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # 注册中文字体（假设系统有 SimSun）
        try:
            pdfmetrics.registerFont(TTFont('SimSun', '/System/Library/Fonts/STHeiti Medium.ttc'))
            font_name = 'SimSun'
        except:
            font_name = 'Helvetica'

        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()

        # 创建 PDF
        doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
        story = []

        # 样式
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            spaceAfter=6
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=6
        )

        # 标题
        story.append(Paragraph(f"文档缩影：{summary['document_title']}", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # 一句话摘要
        story.append(Paragraph("一句话摘要", heading_style))
        story.append(Paragraph(summary['one_line_summary'], normal_style))
        story.append(Spacer(1, 0.1 * inch))

        # 完整摘要
        story.append(Paragraph("完整摘要", heading_style))
        story.append(Paragraph(summary['full_summary'].replace('\n', '<br/>'), normal_style))
        story.append(Spacer(1, 0.1 * inch))

        # 关键词
        if summary['top_keywords']:
            story.append(Paragraph("关键词", heading_style))
            keywords_text = "、".join([kw['word'] for kw in summary['top_keywords']])
            story.append(Paragraph(keywords_text, normal_style))
            story.append(Spacer(1, 0.1 * inch))

        # 量化指标
        story.append(Paragraph("量化指标", heading_style))
        metrics_text = f"字数：{summary['word_count']} | 分块数：{summary['chunk_count']} | 维度：{summary['primary_dimension']}"
        story.append(Paragraph(metrics_text, normal_style))

        # 生成 PDF
        doc.build(story)

        return temp_file.name

    except ImportError:
        raise Exception("未安装 reportlab 库，请运行: pip install reportlab")
    except Exception as e:
        logger.error(f"生成 PDF 失败: {e}", exc_info=True)
        raise


def _generate_word(summary: dict) -> str:
    """生成单个缩影的 Word 文档"""

    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        temp_file.close()

        # 创建 Word 文档
        doc = Document()

        # 标题
        title = doc.add_heading(f"文档缩影：{summary['document_title']}", 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 一句话摘要
        doc.add_heading("一句话摘要", level=2)
        doc.add_paragraph(summary['one_line_summary'])

        # 完整摘要
        doc.add_heading("完整摘要", level=2)
        doc.add_paragraph(summary['full_summary'])

        # 关键词
        if summary['top_keywords']:
            doc.add_heading("关键词", level=2)
            keywords_text = "、".join([kw['word'] for kw in summary['top_keywords']])
            doc.add_paragraph(keywords_text)

        # 核心实体
        if summary['top_entities']:
            doc.add_heading("核心实体", level=2)
            entities_text = "、".join([e['name'] for e in summary['top_entities']])
            doc.add_paragraph(entities_text)

        # 核心主题
        if summary['top_topics']:
            doc.add_heading("核心主题", level=2)
            topics_text = "、".join([f"{t['topic_name']}({t['weight']})" for t in summary['top_topics']])
            doc.add_paragraph(topics_text)

        # 量化指标
        doc.add_heading("量化指标", level=2)
        metrics_text = f"字数：{summary['word_count']} | 分块数：{summary['chunk_count']} | 维度：{summary['primary_dimension']}"
        doc.add_paragraph(metrics_text)

        # 时空上下文
        if summary['time_start'] or summary['spatial_context']:
            doc.add_heading("时空上下文", level=2)
            context_parts = []
            if summary['time_start']:
                time_text = summary['time_start']
                if summary['time_end'] and summary['time_end'] != summary['time_start']:
                    time_text += f" - {summary['time_end']}"
                context_parts.append(f"时间：{time_text}")
            if summary['spatial_context']:
                context_parts.append(f"地点：{summary['spatial_context']}")
            doc.add_paragraph(" | ".join(context_parts))

        # 关联文档
        if summary['related_documents']:
            doc.add_heading("关联文档", level=2)
            for rel_doc in summary['related_documents']:
                doc.add_paragraph(
                    f"• {rel_doc['title']} (相似度: {rel_doc['similarity']})",
                    style='List Bullet'
                )

        # 生成信息
        doc.add_paragraph()
        doc.add_paragraph(f"生成时间：{summary['generated_at']}", style='Caption')

        # 保存
        doc.save(temp_file.name)

        return temp_file.name

    except ImportError:
        raise Exception("未安装 python-docx 库，请运行: pip install python-docx")
    except Exception as e:
        logger.error(f"生成 Word 失败: {e}", exc_info=True)
        raise


def _generate_batch_pdf(summaries: list, project_id: int) -> str:
    """批量生成缩影的 PDF"""

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # 注册中文字体
        try:
            pdfmetrics.registerFont(TTFont('SimSun', '/System/Library/Fonts/STHeiti Medium.ttc'))
            font_name = 'SimSun'
        except:
            font_name = 'Helvetica'

        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()

        # 创建 PDF
        doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
        story = []

        # 样式
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            spaceAfter=6
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=6
        )

        # 封面
        story.append(Paragraph(f"项目 {project_id} 文档缩影汇总", title_style))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(f"总文档数：{len(summaries)}", normal_style))
        story.append(Paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        story.append(PageBreak())

        # 每个缩影
        for i, summary in enumerate(summaries, 1):
            story.append(Paragraph(f"{i}. {summary['document_title']}", heading_style))
            story.append(Paragraph(summary['one_line_summary'], normal_style))
            story.append(Spacer(1, 0.1 * inch))

            # 关键词
            if summary['top_keywords']:
                keywords_text = "关键词：" + "、".join([kw['word'] for kw in summary['top_keywords'][:5]])
                story.append(Paragraph(keywords_text, normal_style))

            # 量化指标
            metrics_text = f"字数：{summary['word_count']} | 分块数：{summary['chunk_count']} | 维度：{summary['primary_dimension']}"
            story.append(Paragraph(metrics_text, normal_style))

            story.append(Spacer(1, 0.2 * inch))

            # 每10个缩影分页
            if i % 10 == 0 and i < len(summaries):
                story.append(PageBreak())

        # 生成 PDF
        doc.build(story)

        return temp_file.name

    except ImportError:
        raise Exception("未安装 reportlab 库，请运行: pip install reportlab")
    except Exception as e:
        logger.error(f"批量生成 PDF 失败: {e}", exc_info=True)
        raise
