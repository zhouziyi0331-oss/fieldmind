#!/usr/bin/env python3
"""
Week 6-7: 知识模式识别器

功能：
1. 从 document_chunks 中提取高质量内容
2. 识别可复用的知识模式
3. 聚类相似内容
4. 生成知识资产候选

模式类型：
- 最佳实践（quality_score > 0.8）
- 解决方案（dimension_category = 技术 + positive sentiment）
- 经验教训（negative sentiment + 质量高）
- 流程规范（包含步骤、顺序）
- 代码模板（包含代码块）

执行时间：2026-09-13
作者：FieldMind Architecture Team
"""

import os
import sys
import sqlite3
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter

# ============================================================================
# 配置
# ============================================================================

DB_PATH = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"

# 知识模式阈值
QUALITY_THRESHOLD = 0.7  # 质量评分阈值
MIN_CHUNK_LENGTH = 50    # 最小文本长度
POSITIVE_THRESHOLD = 0.3  # 正面情感阈值
NEGATIVE_THRESHOLD = -0.3 # 负面情感阈值

# 模式类型权重
PATTERN_WEIGHTS = {
    'best_practice': 1.0,     # 最佳实践
    'solution': 0.9,          # 解决方案
    'lesson_learned': 0.85,   # 经验教训
    'process': 0.8,           # 流程规范
    'code_template': 0.9,     # 代码模板
    'decision': 0.75,         # 决策记录
}


# ============================================================================
# 模式识别器
# ============================================================================

class KnowledgePatternRecognizer:
    """知识模式识别器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.stats = {
            'total_chunks': 0,
            'high_quality': 0,
            'patterns_found': 0,
            'by_type': defaultdict(int)
        }

    def connect(self):
        """连接数据库"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        print(f"✅ 已连接到数据库: {self.db_path}")

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("✅ 数据库连接已关闭")

    def get_high_quality_chunks(self) -> List[Dict]:
        """获取高质量 chunks"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                chunk_id, text,
                quality_score, emotion_polarity, sentiment_label,
                dimension_category, dimension_sub_category,
                keywords, completeness_score, relevance_score
            FROM document_chunks
            WHERE quality_score >= ?
              AND LENGTH(text) >= ?
            ORDER BY quality_score DESC
        """, (QUALITY_THRESHOLD, MIN_CHUNK_LENGTH))

        chunks = [dict(row) for row in cursor.fetchall()]
        self.stats['total_chunks'] = len(chunks)
        print(f"📊 找到 {len(chunks)} 个高质量 chunks")
        return chunks

    def recognize_best_practice(self, chunk: Dict) -> Optional[Dict]:
        """识别最佳实践"""
        # 条件：
        # 1. 质量评分高 (> 0.8)
        # 2. 正面情感
        # 3. 包含实践相关关键词

        if chunk['quality_score'] < 0.8:
            return None

        if chunk['emotion_polarity'] < POSITIVE_THRESHOLD:
            return None

        # 关键词检查
        keywords = json.loads(chunk['keywords']) if chunk['keywords'] else []
        keyword_words = [kw['word'] for kw in keywords]

        practice_keywords = ['实践', '方法', '技巧', '经验', '推荐', '建议', '最佳', '优秀']
        has_practice_keyword = any(pk in ' '.join(keyword_words) or pk in chunk['text']
                                   for pk in practice_keywords)

        if has_practice_keyword:
            return {
                'pattern_type': 'best_practice',
                'chunk_id': chunk['chunk_id'],
                'title': self._extract_title(chunk['text']),
                'content': chunk['text'],
                'confidence': chunk['quality_score'],
                'metadata': {
                    'quality_score': chunk['quality_score'],
                    'emotion_polarity': chunk['emotion_polarity'],
                    'dimension': chunk['dimension_category'],
                    'keywords': keyword_words[:5]
                }
            }

        return None

    def recognize_solution(self, chunk: Dict) -> Optional[Dict]:
        """识别解决方案"""
        # 条件：
        # 1. 技术维度
        # 2. 包含问题-解决方案结构
        # 3. 质量评分中等以上

        if chunk['dimension_category'] not in ['技术', '产品', '业务']:
            return None

        if chunk['quality_score'] < 0.6:
            return None

        # 检查是否包含解决方案标记
        solution_markers = ['解决', '方案', '办法', '处理', '修复', '优化', '改进']
        has_solution = any(marker in chunk['text'] for marker in solution_markers)

        # 检查是否包含问题标记
        problem_markers = ['问题', '错误', 'bug', 'issue', '故障', '异常']
        has_problem = any(marker in chunk['text'] for marker in problem_markers)

        if has_solution and has_problem:
            return {
                'pattern_type': 'solution',
                'chunk_id': chunk['chunk_id'],
                'title': self._extract_title(chunk['text']),
                'content': chunk['text'],
                'confidence': chunk['quality_score'] * 0.9,
                'metadata': {
                    'quality_score': chunk['quality_score'],
                    'dimension': chunk['dimension_category'],
                    'sentiment': chunk['sentiment_label']
                }
            }

        return None

    def recognize_lesson_learned(self, chunk: Dict) -> Optional[Dict]:
        """识别经验教训"""
        # 条件：
        # 1. 负面情感或中性
        # 2. 包含反思、教训关键词
        # 3. 质量评分高

        if chunk['quality_score'] < 0.7:
            return None

        # 教训关键词
        lesson_keywords = ['教训', '经验', '反思', '总结', '启示', '学到', '吸取', '避免']
        has_lesson = any(keyword in chunk['text'] for keyword in lesson_keywords)

        # 可以是负面情感（失败经验）或正面情感（成功总结）
        if has_lesson:
            return {
                'pattern_type': 'lesson_learned',
                'chunk_id': chunk['chunk_id'],
                'title': self._extract_title(chunk['text']),
                'content': chunk['text'],
                'confidence': chunk['quality_score'] * 0.85,
                'metadata': {
                    'quality_score': chunk['quality_score'],
                    'emotion_polarity': chunk['emotion_polarity'],
                    'sentiment_label': chunk['sentiment_label']
                }
            }

        return None

    def recognize_process(self, chunk: Dict) -> Optional[Dict]:
        """识别流程规范"""
        # 条件：
        # 1. 包含步骤标记
        # 2. 管理或业务维度
        # 3. 结构完整性高

        if chunk['completeness_score'] < 0.7:
            return None

        # 步骤标记检查
        step_patterns = [
            r'第[一二三四五六七八九十\d]+步',
            r'步骤[一二三四五\d]+',
            r'\d+\.',
            r'首先|其次|然后|最后|接着'
        ]

        has_steps = any(re.search(pattern, chunk['text']) for pattern in step_patterns)

        if has_steps:
            return {
                'pattern_type': 'process',
                'chunk_id': chunk['chunk_id'],
                'title': self._extract_title(chunk['text']),
                'content': chunk['text'],
                'confidence': chunk['completeness_score'] * 0.8,
                'metadata': {
                    'completeness_score': chunk['completeness_score'],
                    'dimension': chunk['dimension_category']
                }
            }

        return None

    def recognize_code_template(self, chunk: Dict) -> Optional[Dict]:
        """识别代码模板"""
        # 条件：
        # 1. 技术维度
        # 2. 包含代码块标记
        # 3. 质量评分中等以上

        if chunk['dimension_category'] != '技术':
            return None

        if chunk['quality_score'] < 0.6:
            return None

        # 代码块标记
        code_markers = ['```', 'def ', 'function ', 'class ', 'import ', 'const ', 'var ']
        has_code = any(marker in chunk['text'] for marker in code_markers)

        if has_code:
            return {
                'pattern_type': 'code_template',
                'chunk_id': chunk['chunk_id'],
                'title': self._extract_title(chunk['text']),
                'content': chunk['text'],
                'confidence': chunk['quality_score'] * 0.9,
                'metadata': {
                    'quality_score': chunk['quality_score'],
                    'dimension': chunk['dimension_category']
                }
            }

        return None

    def recognize_decision(self, chunk: Dict) -> Optional[Dict]:
        """识别决策记录"""
        # 条件：
        # 1. 包含决策关键词
        # 2. 管理或业务维度
        # 3. 完整性高

        if chunk['dimension_category'] not in ['管理', '业务', '产品']:
            return None

        decision_keywords = ['决定', '决策', '选择', '采用', '方案', '计划']
        has_decision = any(keyword in chunk['text'] for keyword in decision_keywords)

        if has_decision and chunk['completeness_score'] >= 0.6:
            return {
                'pattern_type': 'decision',
                'chunk_id': chunk['chunk_id'],
                'title': self._extract_title(chunk['text']),
                'content': chunk['text'],
                'confidence': chunk['completeness_score'] * 0.75,
                'metadata': {
                    'completeness_score': chunk['completeness_score'],
                    'dimension': chunk['dimension_category']
                }
            }

        return None

    def _extract_title(self, text: str, max_length: int = 50) -> str:
        """提取标题（使用前 N 个字符）"""
        # 尝试提取第一句话
        first_sentence = text.split('。')[0].split('.')[0].strip()

        if len(first_sentence) <= max_length:
            return first_sentence
        else:
            return first_sentence[:max_length] + '...'

    def recognize_all_patterns(self, chunks: List[Dict]) -> List[Dict]:
        """识别所有模式"""
        print("\n🔍 识别知识模式...")

        patterns = []

        for chunk in chunks:
            # 尝试所有识别器
            recognizers = [
                self.recognize_best_practice,
                self.recognize_solution,
                self.recognize_lesson_learned,
                self.recognize_process,
                self.recognize_code_template,
                self.recognize_decision,
            ]

            for recognizer in recognizers:
                pattern = recognizer(chunk)
                if pattern:
                    patterns.append(pattern)
                    self.stats['patterns_found'] += 1
                    self.stats['by_type'][pattern['pattern_type']] += 1
                    break  # 每个 chunk 只匹配一种模式

        print(f"✅ 识别到 {len(patterns)} 个知识模式")
        return patterns

    def cluster_patterns(self, patterns: List[Dict]) -> Dict[str, List[Dict]]:
        """按类型聚类模式"""
        clustered = defaultdict(list)

        for pattern in patterns:
            clustered[pattern['pattern_type']].append(pattern)

        # 按置信度排序
        for pattern_type in clustered:
            clustered[pattern_type].sort(key=lambda x: x['confidence'], reverse=True)

        return dict(clustered)

    def generate_report(self, patterns: List[Dict], clustered: Dict[str, List[Dict]]):
        """生成识别报告"""
        print("\n" + "=" * 70)
        print("知识模式识别报告")
        print("=" * 70)

        print(f"\n总 Chunks 数:     {self.stats['total_chunks']}")
        print(f"识别到的模式:     {self.stats['patterns_found']}")
        print(f"识别率:           {self.stats['patterns_found']/self.stats['total_chunks']*100:.1f}%")

        print(f"\n按类型统计:")
        for pattern_type, count in self.stats['by_type'].items():
            type_name = {
                'best_practice': '最佳实践',
                'solution': '解决方案',
                'lesson_learned': '经验教训',
                'process': '流程规范',
                'code_template': '代码模板',
                'decision': '决策记录',
            }.get(pattern_type, pattern_type)

            print(f"  {type_name:12s}: {count:4d} 个")

        # 显示每种类型的 Top 3
        print(f"\n✨ 各类型 Top 3 示例:")
        for pattern_type, items in clustered.items():
            type_name = {
                'best_practice': '最佳实践',
                'solution': '解决方案',
                'lesson_learned': '经验教训',
                'process': '流程规范',
                'code_template': '代码模板',
                'decision': '决策记录',
            }.get(pattern_type, pattern_type)

            print(f"\n【{type_name}】")
            for i, item in enumerate(items[:3], 1):
                print(f"  {i}. {item['title']}")
                print(f"     置信度: {item['confidence']:.3f} | ID: {item['chunk_id']}")

    def save_patterns(self, patterns: List[Dict], output_dir: str):
        """保存识别结果"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"knowledge_patterns_{timestamp}.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'stats': dict(self.stats),
                'patterns': patterns
            }, f, indent=2, ensure_ascii=False)

        print(f"\n📄 结果已保存: {output_file}")

    def run(self):
        """执行识别流程"""
        print("=" * 70)
        print("知识模式识别")
        print("=" * 70)

        try:
            # 1. 获取高质量 chunks
            print("\n[步骤 1/4] 获取高质量 Chunks")
            chunks = self.get_high_quality_chunks()

            if len(chunks) == 0:
                print("⚠️  没有找到高质量 chunks")
                return

            # 2. 识别模式
            print("\n[步骤 2/4] 识别知识模式")
            patterns = self.recognize_all_patterns(chunks)

            # 3. 聚类
            print("\n[步骤 3/4] 聚类分析")
            clustered = self.cluster_patterns(patterns)

            # 4. 生成报告
            print("\n[步骤 4/4] 生成报告")
            self.generate_report(patterns, clustered)

            # 5. 保存结果
            output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/knowledge_assets"
            self.save_patterns(patterns, output_dir)

        except Exception as e:
            print(f"\n❌ 识别失败: {e}")
            import traceback
            traceback.print_exc()
            raise


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    recognizer = KnowledgePatternRecognizer(DB_PATH)

    try:
        # 连接数据库
        recognizer.connect()

        # 执行识别
        recognizer.run()

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        sys.exit(1)

    finally:
        # 关闭连接
        recognizer.close()

    print("\n✅ 所有操作完成")


if __name__ == "__main__":
    main()
