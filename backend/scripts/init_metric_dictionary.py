"""
指标字典初始化数据
预置20+个文本量化指标
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import text
from app.core.database import engine
from datetime import datetime


def initialize_metric_dictionary():
    """初始化指标字典"""

    print("="*60)
    print("初始化指标字典")
    print("="*60)

    # 预置指标定义
    metrics = [
        # 结构性指标
        {
            "metric_id": "M001",
            "metric_name": "字数",
            "metric_category": "结构性",
            "definition": "文本片段的字符总数（不含标点符号和空格）",
            "calculation_rule": "len([c for c in text if c.isalnum()])",
            "data_type": "int",
            "value_range": "[0, +∞)",
            "unit": "字",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },
        {
            "metric_id": "M002",
            "metric_name": "句数",
            "metric_category": "结构性",
            "definition": "文本片段中句子的数量",
            "calculation_rule": "按句号、问号、感叹号分割计数",
            "data_type": "int",
            "value_range": "[1, +∞)",
            "unit": "句",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },
        {
            "metric_id": "M003",
            "metric_name": "平均句长",
            "metric_category": "结构性",
            "definition": "每句话的平均字数",
            "calculation_rule": "总字数 / 句数",
            "data_type": "float",
            "value_range": "[1, +∞)",
            "unit": "字/句",
            "source_fields": '["M001", "M002"]',
            "algorithm_version": "v1.0"
        },

        # 情绪性指标
        {
            "metric_id": "M011",
            "metric_name": "情感极性值",
            "metric_category": "情绪性",
            "definition": "文本表达的正负面倾向程度，-1为最负面，+1为最正面，0为中性",
            "calculation_rule": "使用 SnowNLP 或 Erlangshen-RoBERTa 模型推理得分",
            "data_type": "float",
            "value_range": "[-1, 1]",
            "unit": "分",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v2.1"
        },
        {
            "metric_id": "M012",
            "metric_name": "情绪强度",
            "metric_category": "情绪性",
            "definition": "情绪表达的强烈程度，0为无情绪，1为极强情绪",
            "calculation_rule": "abs(情感极性值) * 情绪词密度",
            "data_type": "float",
            "value_range": "[0, 1]",
            "unit": "分",
            "source_fields": '["M011", "M021"]',
            "algorithm_version": "v1.0"
        },
        {
            "metric_id": "M013",
            "metric_name": "主观性",
            "metric_category": "情绪性",
            "definition": "文本的主观程度，0为完全客观，1为完全主观",
            "calculation_rule": "统计第一人称代词、情感词、评价词的比例",
            "data_type": "float",
            "value_range": "[0, 1]",
            "unit": "分",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },

        # 语言风格指标
        {
            "metric_id": "M021",
            "metric_name": "情绪词密度",
            "metric_category": "语言风格",
            "definition": "情绪词汇占总词数的比例",
            "calculation_rule": "情绪词数量 / 总词数",
            "data_type": "float",
            "value_range": "[0, 1]",
            "unit": "比例",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },
        {
            "metric_id": "M022",
            "metric_name": "感叹号数量",
            "metric_category": "语言风格",
            "definition": "文本中感叹号的出现次数",
            "calculation_rule": "text.count('！') + text.count('!')",
            "data_type": "int",
            "value_range": "[0, +∞)",
            "unit": "个",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },
        {
            "metric_id": "M023",
            "metric_name": "疑问句比例",
            "metric_category": "语言风格",
            "definition": "疑问句占总句数的比例",
            "calculation_rule": "疑问句数量 / 总句数",
            "data_type": "float",
            "value_range": "[0, 1]",
            "unit": "比例",
            "source_fields": '["chunk_text", "M002"]',
            "algorithm_version": "v1.0"
        },
        {
            "metric_id": "M024",
            "metric_name": "语气强度",
            "metric_category": "语言风格",
            "definition": "语气助词和强调词的使用频率",
            "calculation_rule": "统计'的确'、'确实'、'非常'等强调词的密度",
            "data_type": "float",
            "value_range": "[0, 1]",
            "unit": "分",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },
        {
            "metric_id": "M025",
            "metric_name": "情态动词数量",
            "metric_category": "语言风格",
            "definition": "表示可能、应该、必须等情态的动词数量",
            "calculation_rule": "统计'可能'、'应该'、'必须'、'会'等词",
            "data_type": "int",
            "value_range": "[0, +∞)",
            "unit": "个",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },

        # 内容类指标
        {
            "metric_id": "M031",
            "metric_name": "关键词数量",
            "metric_category": "内容类",
            "definition": "提取的关键词总数",
            "calculation_rule": "使用 TF-IDF 或 TextRank 算法提取",
            "data_type": "int",
            "value_range": "[0, +∞)",
            "unit": "个",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },
        {
            "metric_id": "M032",
            "metric_name": "实体数量",
            "metric_category": "内容类",
            "definition": "识别出的命名实体总数（人名、地名、机构名等）",
            "calculation_rule": "使用 NER 模型识别",
            "data_type": "int",
            "value_range": "[0, +∞)",
            "unit": "个",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },
        {
            "metric_id": "M033",
            "metric_name": "主题一致性",
            "metric_category": "内容类",
            "definition": "文本与主题的相关程度",
            "calculation_rule": "使用主题模型计算相似度",
            "data_type": "float",
            "value_range": "[0, 1]",
            "unit": "分",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },

        # 质量类指标
        {
            "metric_id": "M041",
            "metric_name": "文本质量评分",
            "metric_category": "质量类",
            "definition": "综合评估文本的可读性和规范性",
            "calculation_rule": "基于语法错误、重复率、连贯性等维度综合评分",
            "data_type": "float",
            "value_range": "[0, 1]",
            "unit": "分",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },
        {
            "metric_id": "M042",
            "metric_name": "重复率",
            "metric_category": "质量类",
            "definition": "重复内容占总内容的比例",
            "calculation_rule": "统计重复字符串的比例",
            "data_type": "float",
            "value_range": "[0, 1]",
            "unit": "比例",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },
        {
            "metric_id": "M043",
            "metric_name": "语法错误数",
            "metric_category": "质量类",
            "definition": "检测到的语法错误数量",
            "calculation_rule": "使用语法检查工具检测",
            "data_type": "int",
            "value_range": "[0, +∞)",
            "unit": "个",
            "source_fields": '["chunk_text"]',
            "algorithm_version": "v1.0"
        },

        # 时间类指标
        {
            "metric_id": "M051",
            "metric_name": "时间跨度",
            "metric_category": "时间类",
            "definition": "音频/视频片段的时长",
            "calculation_rule": "timestamp_end - timestamp_start",
            "data_type": "float",
            "value_range": "[0, +∞)",
            "unit": "秒",
            "source_fields": '["timestamp_start", "timestamp_end"]',
            "algorithm_version": "v1.0"
        },
        {
            "metric_id": "M052",
            "metric_name": "语速",
            "metric_category": "时间类",
            "definition": "每秒说话的字数",
            "calculation_rule": "字数 / 时间跨度",
            "data_type": "float",
            "value_range": "[0, +∞)",
            "unit": "字/秒",
            "source_fields": '["M001", "M051"]',
            "algorithm_version": "v1.0"
        },

        # 对比类指标
        {
            "metric_id": "M061",
            "metric_name": "与平均值偏离度",
            "metric_category": "对比类",
            "definition": "该chunk某指标值与项目平均值的偏离程度",
            "calculation_rule": "(当前值 - 平均值) / 标准差",
            "data_type": "float",
            "value_range": "(-∞, +∞)",
            "unit": "标准差",
            "source_fields": '["any_metric"]',
            "algorithm_version": "v1.0"
        }
    ]

    with engine.connect() as conn:
        for metric in metrics:
            try:
                conn.execute(text("""
                    INSERT INTO metric_dictionary (
                        metric_id, metric_name, metric_category, definition,
                        calculation_rule, data_type, value_range, unit,
                        source_fields, algorithm_version, status
                    ) VALUES (
                        :metric_id, :metric_name, :metric_category, :definition,
                        :calculation_rule, :data_type, :value_range, :unit,
                        :source_fields, :algorithm_version, 'active'
                    )
                """), metric)

                print(f"✓ 指标 {metric['metric_id']} - {metric['metric_name']} 添加成功")

            except Exception as e:
                print(f"⚠ 指标 {metric['metric_id']} 可能已存在: {e}")

        conn.commit()

    print(f"\n✅ 指标字典初始化完成，共 {len(metrics)} 个指标")


if __name__ == "__main__":
    try:
        initialize_metric_dictionary()
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
