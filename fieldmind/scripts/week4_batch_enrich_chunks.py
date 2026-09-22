#!/usr/bin/env python3
"""
Week 4-5: 批量增强现有 Chunks

功能：
1. 读取 document_chunks 表中的所有记录
2. 对每条记录执行数据增强
3. 更新 22 个新增字段
4. 批量处理，支持断点续传
5. 生成详细的增强报告

执行时间：2026-09-13
作者：FieldMind Architecture Team
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from typing import Dict, List

# 添加路径以便导入 chunk_enricher
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from app.services.chunk_enricher import ChunkEnricher

# ============================================================================
# 配置
# ============================================================================

DB_PATH = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
BATCH_SIZE = 50  # 每批处理的记录数
DRY_RUN = False  # 设置为 True 仅模拟

# ============================================================================
# 批量增强器
# ============================================================================

class BatchChunkEnricher:
    """批量 Chunk 增强器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.enricher = ChunkEnricher()
        self.stats = {
            'total': 0,
            'processed': 0,
            'enriched': 0,
            'skipped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
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

    def get_chunks_to_enrich(self, limit: int = None) -> List[Dict]:
        """
        获取需要增强的 chunks

        优先处理未增强的（quality_score IS NULL）
        """
        cursor = self.conn.cursor()

        query = """
            SELECT
                id, chunk_id, text, chunk_text,
                speaker, entities_count,
                quality_score
            FROM document_chunks
            WHERE quality_score IS NULL OR quality_score = 0
            ORDER BY id
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        chunks = [dict(row) for row in cursor.fetchall()]

        print(f"📊 找到 {len(chunks)} 个需要增强的 chunks")
        return chunks

    def enrich_chunk(self, chunk: Dict) -> Dict:
        """增强单个 chunk"""
        # 选择文本字段（优先使用 text，其次 chunk_text）
        text = chunk.get('text') or chunk.get('chunk_text') or ''

        if not text or len(text.strip()) == 0:
            self.stats['skipped'] += 1
            return None

        # 准备现有数据
        existing_data = {
            'entities_count': chunk.get('entities_count', 0) or 0
        }

        # 执行增强
        try:
            enriched = self.enricher.enrich(text, existing_data)
            self.stats['enriched'] += 1
            return enriched
        except Exception as e:
            print(f"❌ 增强失败 (chunk_id={chunk['chunk_id']}): {e}")
            self.stats['errors'] += 1
            return None

    def update_chunk(self, chunk_id: int, enriched_data: Dict):
        """更新 chunk 数据"""
        if DRY_RUN:
            return

        cursor = self.conn.cursor()

        # 移除内部字段
        enriched_data = {k: v for k, v in enriched_data.items() if not k.startswith('_')}

        # 构建 UPDATE 语句
        set_clauses = ', '.join([f"{k} = ?" for k in enriched_data.keys()])
        values = list(enriched_data.values())
        values.append(chunk_id)

        query = f"""
            UPDATE document_chunks
            SET {set_clauses}
            WHERE id = ?
        """

        try:
            cursor.execute(query, values)
        except Exception as e:
            print(f"❌ 更新失败 (id={chunk_id}): {e}")
            self.stats['errors'] += 1

    def process_batch(self, chunks: List[Dict]) -> int:
        """处理一批 chunks"""
        updated = 0

        for chunk in chunks:
            # 增强
            enriched = self.enrich_chunk(chunk)

            if enriched:
                # 更新数据库
                self.update_chunk(chunk['id'], enriched)
                updated += 1

            self.stats['processed'] += 1

        # 提交事务
        if not DRY_RUN:
            self.conn.commit()

        return updated

    def run(self):
        """执行批量增强"""
        print("=" * 70)
        print("批量 Chunk 数据增强")
        print(f"模式: {'DRY RUN（模拟）' if DRY_RUN else 'REAL（真实执行）'}")
        print("=" * 70)

        self.stats['start_time'] = datetime.now()

        try:
            # 获取待处理的 chunks
            print("\n[步骤 1/3] 获取待处理的 Chunks")
            chunks = self.get_chunks_to_enrich()
            self.stats['total'] = len(chunks)

            if self.stats['total'] == 0:
                print("✅ 没有需要增强的 chunks")
                return

            # 批量处理
            print(f"\n[步骤 2/3] 批量增强处理")
            print(f"批量大小: {BATCH_SIZE}")
            print()

            for i in range(0, len(chunks), BATCH_SIZE):
                batch = chunks[i:i + BATCH_SIZE]
                batch_num = i // BATCH_SIZE + 1
                total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

                print(f"处理批次 {batch_num}/{total_batches} "
                      f"(记录 {i+1}-{min(i+len(batch), len(chunks))}/{len(chunks)})...", end=' ')

                updated = self.process_batch(batch)

                print(f"✅ 增强 {updated} 条")

                # 显示进度统计
                if batch_num % 5 == 0 or batch_num == total_batches:
                    progress = (self.stats['processed'] / self.stats['total']) * 100
                    print(f"   进度: {progress:.1f}% | "
                          f"成功: {self.stats['enriched']} | "
                          f"跳过: {self.stats['skipped']} | "
                          f"错误: {self.stats['errors']}")

            # 验证结果
            print(f"\n[步骤 3/3] 验证增强结果")
            self.verify_enrichment()

            self.stats['end_time'] = datetime.now()

            # 生成报告
            self.generate_report()

        except Exception as e:
            print(f"\n❌ 批量增强失败: {e}")
            import traceback
            traceback.print_exc()
            self.stats['end_time'] = datetime.now()
            raise

    def verify_enrichment(self):
        """验证增强结果"""
        if DRY_RUN:
            print("   [DRY RUN] 跳过验证")
            return

        cursor = self.conn.cursor()

        # 统计增强字段填充率
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN quality_score IS NOT NULL AND quality_score > 0 THEN 1 ELSE 0 END) as has_quality,
                SUM(CASE WHEN emotion_polarity IS NOT NULL THEN 1 ELSE 0 END) as has_emotion,
                SUM(CASE WHEN dimension_category IS NOT NULL THEN 1 ELSE 0 END) as has_dimension,
                SUM(CASE WHEN keywords IS NOT NULL AND keywords != '[]' THEN 1 ELSE 0 END) as has_keywords
            FROM document_chunks
        """)

        row = cursor.fetchone()

        print(f"   总记录数:     {row['total']}")
        print(f"   质量评分:     {row['has_quality']} ({row['has_quality']/row['total']*100:.1f}%)")
        print(f"   情感分析:     {row['has_emotion']} ({row['has_emotion']/row['total']*100:.1f}%)")
        print(f"   维度分类:     {row['has_dimension']} ({row['has_dimension']/row['total']*100:.1f}%)")
        print(f"   关键词提取:   {row['has_keywords']} ({row['has_keywords']/row['total']*100:.1f}%)")

        # 显示增强样例
        cursor.execute("""
            SELECT chunk_id, emotion_polarity, sentiment_label,
                   dimension_category, quality_score, keywords
            FROM document_chunks
            WHERE quality_score IS NOT NULL AND quality_score > 0
            LIMIT 3
        """)

        print(f"\n   增强样例（前 3 条）:")
        for row in cursor.fetchall():
            print(f"   - chunk_id: {row['chunk_id']}")
            print(f"     情感: {row['emotion_polarity']:+.3f} ({row['sentiment_label']})")
            print(f"     维度: {row['dimension_category']}")
            print(f"     质量: {row['quality_score']:.3f}")

            keywords = json.loads(row['keywords']) if row['keywords'] else []
            keyword_words = [kw['word'] for kw in keywords[:3]]
            print(f"     关键词: {', '.join(keyword_words)}")
            print()

    def generate_report(self):
        """生成增强报告"""
        print("\n" + "=" * 70)
        print("增强报告")
        print("=" * 70)

        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        print(f"总记录数:   {self.stats['total']}")
        print(f"已处理:     {self.stats['processed']}")
        print(f"成功增强:   {self.stats['enriched']}")
        print(f"跳过:       {self.stats['skipped']}")
        print(f"错误:       {self.stats['errors']}")
        print(f"执行时间:   {duration:.2f} 秒")

        if duration > 0:
            speed = self.stats['processed'] / duration
            print(f"处理速度:   {speed:.1f} 条/秒")

        if self.stats['errors'] == 0:
            print(f"\n✅ 批量增强成功完成！")
        else:
            print(f"\n⚠️  批量增强完成，但有 {self.stats['errors']} 个错误")

        # 保存 JSON 报告
        if not DRY_RUN:
            report_path = f"/Users/alwan/Downloads/FieldMind/fieldmind/reports/enrichment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs(os.path.dirname(report_path), exist_ok=True)

            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'stats': {
                        **self.stats,
                        'start_time': self.stats['start_time'].isoformat(),
                        'end_time': self.stats['end_time'].isoformat(),
                    }
                }, f, indent=2, ensure_ascii=False)

            print(f"\n📄 报告已保存: {report_path}")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    enricher = BatchChunkEnricher(DB_PATH)

    try:
        # 连接数据库
        enricher.connect()

        # 执行批量增强
        enricher.run()

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        sys.exit(1)

    finally:
        # 关闭连接
        enricher.close()

    print("\n✅ 所有操作完成")


if __name__ == "__main__":
    main()
