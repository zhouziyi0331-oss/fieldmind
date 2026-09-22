#!/usr/bin/env python3
"""
Week 3 Day 5: 数据一致性验证脚本

功能：
1. 检查 PostgreSQL, Neo4j, ChromaDB 三个数据库的数据一致性
2. 验证 ID 格式正确性
3. 检查同步状态标记
4. 生成详细的一致性报告

运行模式：
- 真实模式：连接实际数据库
- Mock 模式：使用模拟数据测试

执行时间：2025-01-XX
作者：FieldMind Architecture Team
"""

import os
import sys
import sqlite3
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# ============================================================================
# 配置
# ============================================================================

MOCK_MODE = False  # 设置为 False 使用真实数据库

# 数据库路径
DB_PATH = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"

# ID 格式验证正则
ID_PATTERN = re.compile(r'^[a-z]{2,4}_[a-f0-9]{12}$')

# 支持的 ID 前缀
VALID_PREFIXES = {
    'ent': 'Entity',
    'chk': 'Chunk',
    'doc': 'Document',
    'rel': 'Relation',
    'usr': 'User',
    'prj': 'Project',
    'tsk': 'Task'
}


# ============================================================================
# Mock 数据（用于测试）
# ============================================================================

class MockDatabase:
    """模拟数据库，用于测试"""

    def __init__(self):
        # PostgreSQL 模拟数据
        self.pg_entities = [
            {'entity_id': f'ent_{i:012x}', 'name': f'Entity {i}', 'entity_type': 'Person'}
            for i in range(1, 1133)  # 1,132 entities
        ]

        self.pg_chunks = [
            {
                'chunk_id': f'chk_{i:012x}',
                'content': f'Chunk content {i}',
                'speaker_id': f'ent_{(i % 100):012x}',
                'emotion_polarity': 0.5,
                'quality_score': 0.8,
                'synced_to_chromadb': 1 if i % 10 != 0 else 0,  # 90% 已同步
                'embedding_id': f'emb_{i:012x}' if i % 10 != 0 else None
            }
            for i in range(1, 1037)  # 1,036 chunks
        ]

        # Neo4j 模拟数据
        self.neo4j_entities = [
            {'id': f'ent_{i:012x}', 'name': f'Entity {i}', 'type': 'Person'}
            for i in range(1, 1133)  # 应该匹配 PostgreSQL
        ]

        # ChromaDB 模拟数据
        self.chromadb_chunks = [
            {'id': f'chk_{i:012x}', 'embedding': [0.1] * 384}
            for i in range(1, 1037) if i % 10 != 0  # 90% 已同步（932 个）
        ]

    def get_pg_entity_count(self) -> int:
        return len(self.pg_entities)

    def get_pg_chunk_count(self) -> int:
        return len(self.pg_chunks)

    def get_neo4j_entity_count(self) -> int:
        return len(self.neo4j_entities)

    def get_chromadb_chunk_count(self) -> int:
        return len(self.chromadb_chunks)

    def get_pg_entities_sample(self, limit: int = 100) -> List[Dict]:
        return self.pg_entities[:limit]

    def get_pg_chunks_sample(self, limit: int = 100) -> List[Dict]:
        return self.pg_chunks[:limit]

    def get_neo4j_entity_ids(self) -> set:
        return {e['id'] for e in self.neo4j_entities}

    def get_chromadb_chunk_ids(self) -> set:
        return {c['id'] for c in self.chromadb_chunks}

    def get_sync_status(self) -> Dict:
        synced = sum(1 for c in self.pg_chunks if c['synced_to_chromadb'] == 1)
        return {
            'total': len(self.pg_chunks),
            'synced': synced,
            'pending': len(self.pg_chunks) - synced
        }


# ============================================================================
# 真实数据库连接器
# ============================================================================

class RealDatabase:
    """真实数据库连接器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """连接到 SQLite 数据库"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def get_pg_entity_count(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM entities WHERE entity_id IS NOT NULL")
        return cursor.fetchone()['count']

    def get_pg_chunk_count(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM document_chunks")
        return cursor.fetchone()['count']

    def get_neo4j_entity_count(self) -> int:
        # 在真实模式下，这里应该连接 Neo4j
        # 目前返回 0 表示未实现
        return 0

    def get_chromadb_chunk_count(self) -> int:
        # 在真实模式下，这里应该连接 ChromaDB
        # 目前返回 0 表示未实现
        return 0

    def get_pg_entities_sample(self, limit: int = 100) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT entity_id, name, entity_type
            FROM entities
            WHERE entity_id IS NOT NULL
            LIMIT {limit}
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_pg_chunks_sample(self, limit: int = 100) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT chunk_id, text, speaker_id, emotion_polarity,
                   quality_score, synced_to_chromadb, embedding_id
            FROM document_chunks
            LIMIT {limit}
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_neo4j_entity_ids(self) -> set:
        # 真实模式下连接 Neo4j
        return set()

    def get_chromadb_chunk_ids(self) -> set:
        # 真实模式下连接 ChromaDB
        return set()

    def get_sync_status(self) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN synced_to_chromadb = 1 THEN 1 ELSE 0 END) as synced
            FROM document_chunks
        """)
        row = cursor.fetchone()
        total = row['total']
        synced = row['synced'] or 0
        return {
            'total': total,
            'synced': synced,
            'pending': total - synced
        }


# ============================================================================
# 一致性检查器
# ============================================================================

class ConsistencyChecker:
    """数据一致性检查器"""

    def __init__(self, db):
        self.db = db
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'MOCK' if MOCK_MODE else 'REAL',
            'checks': {},
            'summary': {},
            'issues': []
        }

    def validate_id_format(self, id_string: str) -> Tuple[bool, Optional[str]]:
        """验证 ID 格式"""
        if not id_string:
            return False, "ID 为空"

        if not ID_PATTERN.match(id_string):
            return False, f"ID 格式不匹配: {id_string}"

        prefix = id_string.split('_')[0]
        if prefix not in VALID_PREFIXES:
            return False, f"未知的 ID 前缀: {prefix}"

        return True, None

    def check_entity_counts(self):
        """检查 1：实体数量一致性"""
        print("\n[检查 1] 实体数量一致性")
        print("-" * 60)

        pg_count = self.db.get_pg_entity_count()
        neo4j_count = self.db.get_neo4j_entity_count()

        print(f"PostgreSQL 实体数: {pg_count}")
        print(f"Neo4j 实体数:      {neo4j_count}")

        check_result = {
            'postgresql': pg_count,
            'neo4j': neo4j_count,
            'match': pg_count == neo4j_count,
            'difference': abs(pg_count - neo4j_count)
        }

        if not check_result['match']:
            issue = f"实体数量不匹配：PostgreSQL={pg_count}, Neo4j={neo4j_count}, 差异={check_result['difference']}"
            self.results['issues'].append(issue)
            print(f"⚠️  {issue}")
        else:
            print(f"✅ 实体数量一致")

        self.results['checks']['entity_counts'] = check_result

    def check_chunk_counts(self):
        """检查 2：Chunk 数量一致性"""
        print("\n[检查 2] Chunk 数量一致性")
        print("-" * 60)

        pg_count = self.db.get_pg_chunk_count()
        chromadb_count = self.db.get_chromadb_chunk_count()
        sync_status = self.db.get_sync_status()

        print(f"PostgreSQL Chunk 数:  {pg_count}")
        print(f"ChromaDB Chunk 数:    {chromadb_count}")
        print(f"标记为已同步:         {sync_status['synced']}")
        print(f"待同步:               {sync_status['pending']}")

        # ChromaDB 应该等于标记为已同步的数量
        expected_match = chromadb_count == sync_status['synced']

        check_result = {
            'postgresql_total': pg_count,
            'chromadb_total': chromadb_count,
            'marked_synced': sync_status['synced'],
            'pending_sync': sync_status['pending'],
            'match': expected_match,
            'sync_rate': f"{(sync_status['synced'] / pg_count * 100):.1f}%" if pg_count > 0 else "0%"
        }

        if not expected_match:
            issue = f"Chunk 同步状态不一致：ChromaDB={chromadb_count}, 标记已同步={sync_status['synced']}"
            self.results['issues'].append(issue)
            print(f"⚠️  {issue}")
        else:
            print(f"✅ Chunk 同步状态一致")

        print(f"📊 同步率: {check_result['sync_rate']}")

        self.results['checks']['chunk_counts'] = check_result

    def check_id_formats(self):
        """检查 3：ID 格式正确性"""
        print("\n[检查 3] ID 格式验证")
        print("-" * 60)

        # 检查实体 ID
        entities = self.db.get_pg_entities_sample(limit=100)
        entity_id_errors = []

        for entity in entities:
            is_valid, error = self.validate_id_format(entity.get('entity_id'))
            if not is_valid:
                entity_id_errors.append({
                    'entity_name': entity.get('name'),
                    'entity_id': entity.get('entity_id'),
                    'error': error
                })

        print(f"检查实体样本: {len(entities)} 个")
        print(f"ID 格式错误:   {len(entity_id_errors)} 个")

        # 检查 Chunk ID
        chunks = self.db.get_pg_chunks_sample(limit=100)
        chunk_id_errors = []

        for chunk in chunks:
            chunk_id = chunk.get('chunk_id')
            if chunk_id:
                is_valid, error = self.validate_id_format(chunk_id)
                if not is_valid:
                    chunk_id_errors.append({
                        'chunk_id': chunk_id,
                        'error': error
                    })

        print(f"检查 Chunk 样本: {len(chunks)} 个")
        print(f"ID 格式错误:     {len(chunk_id_errors)} 个")

        check_result = {
            'entities_checked': len(entities),
            'entities_errors': len(entity_id_errors),
            'chunks_checked': len(chunks),
            'chunks_errors': len(chunk_id_errors),
            'total_errors': len(entity_id_errors) + len(chunk_id_errors),
            'error_details': {
                'entities': entity_id_errors[:5],  # 只保存前 5 个
                'chunks': chunk_id_errors[:5]
            }
        }

        if check_result['total_errors'] > 0:
            issue = f"发现 {check_result['total_errors']} 个 ID 格式错误"
            self.results['issues'].append(issue)
            print(f"⚠️  {issue}")
        else:
            print(f"✅ 所有 ID 格式正确")

        self.results['checks']['id_formats'] = check_result

    def check_foreign_key_integrity(self):
        """检查 4：外键完整性"""
        print("\n[检查 4] 外键完整性验证")
        print("-" * 60)

        chunks = self.db.get_pg_chunks_sample(limit=100)
        entity_ids = self.db.get_neo4j_entity_ids() if not MOCK_MODE else {
            e['entity_id'] for e in self.db.get_pg_entities_sample(limit=1200)
        }

        orphan_chunks = []

        for chunk in chunks:
            speaker_id = chunk.get('speaker_id')
            if speaker_id and speaker_id not in entity_ids:
                orphan_chunks.append({
                    'chunk_id': chunk.get('chunk_id'),
                    'speaker_id': speaker_id
                })

        print(f"检查 Chunk 样本:     {len(chunks)} 个")
        print(f"实体 ID 集合大小:    {len(entity_ids)} 个")
        print(f"孤立的 speaker_id:   {len(orphan_chunks)} 个")

        check_result = {
            'chunks_checked': len(chunks),
            'total_entities': len(entity_ids),
            'orphan_references': len(orphan_chunks),
            'orphan_details': orphan_chunks[:5]  # 只保存前 5 个
        }

        if len(orphan_chunks) > 0:
            issue = f"发现 {len(orphan_chunks)} 个孤立的外键引用"
            self.results['issues'].append(issue)
            print(f"⚠️  {issue}")
        else:
            print(f"✅ 外键完整性正常")

        self.results['checks']['foreign_key_integrity'] = check_result

    def check_new_fields(self):
        """检查 5：新字段数据质量"""
        print("\n[检查 5] 新字段数据质量")
        print("-" * 60)

        chunks = self.db.get_pg_chunks_sample(limit=100)

        field_stats = {
            'emotion_polarity': {'filled': 0, 'null': 0, 'out_of_range': 0},
            'quality_score': {'filled': 0, 'null': 0, 'out_of_range': 0},
            'speaker_id': {'filled': 0, 'null': 0},
            'synced_to_chromadb': {'synced': 0, 'pending': 0},
        }

        for chunk in chunks:
            # emotion_polarity 应该在 [-1, 1]
            emotion = chunk.get('emotion_polarity')
            if emotion is not None:
                field_stats['emotion_polarity']['filled'] += 1
                if emotion < -1 or emotion > 1:
                    field_stats['emotion_polarity']['out_of_range'] += 1
            else:
                field_stats['emotion_polarity']['null'] += 1

            # quality_score 应该在 [0, 1]
            quality = chunk.get('quality_score')
            if quality is not None:
                field_stats['quality_score']['filled'] += 1
                if quality < 0 or quality > 1:
                    field_stats['quality_score']['out_of_range'] += 1
            else:
                field_stats['quality_score']['null'] += 1

            # speaker_id
            speaker = chunk.get('speaker_id')
            if speaker:
                field_stats['speaker_id']['filled'] += 1
            else:
                field_stats['speaker_id']['null'] += 1

            # synced_to_chromadb
            if chunk.get('synced_to_chromadb') == 1:
                field_stats['synced_to_chromadb']['synced'] += 1
            else:
                field_stats['synced_to_chromadb']['pending'] += 1

        print(f"检查样本数: {len(chunks)}")
        print(f"\nemotion_polarity:")
        print(f"  - 已填充: {field_stats['emotion_polarity']['filled']}")
        print(f"  - 空值:   {field_stats['emotion_polarity']['null']}")
        print(f"  - 超范围: {field_stats['emotion_polarity']['out_of_range']}")

        print(f"\nquality_score:")
        print(f"  - 已填充: {field_stats['quality_score']['filled']}")
        print(f"  - 空值:   {field_stats['quality_score']['null']}")
        print(f"  - 超范围: {field_stats['quality_score']['out_of_range']}")

        print(f"\nspeaker_id:")
        print(f"  - 已填充: {field_stats['speaker_id']['filled']}")
        print(f"  - 空值:   {field_stats['speaker_id']['null']}")

        print(f"\nsync 状态:")
        print(f"  - 已同步: {field_stats['synced_to_chromadb']['synced']}")
        print(f"  - 待同步: {field_stats['synced_to_chromadb']['pending']}")

        check_result = {
            'sample_size': len(chunks),
            'field_statistics': field_stats
        }

        total_errors = (
            field_stats['emotion_polarity']['out_of_range'] +
            field_stats['quality_score']['out_of_range']
        )

        if total_errors > 0:
            issue = f"发现 {total_errors} 个字段值超出范围"
            self.results['issues'].append(issue)
            print(f"\n⚠️  {issue}")
        else:
            print(f"\n✅ 新字段数据质量正常")

        self.results['checks']['new_fields'] = check_result

    def run_all_checks(self):
        """运行所有检查"""
        print("=" * 60)
        print("数据一致性验证")
        print(f"模式: {'MOCK（测试）' if MOCK_MODE else 'REAL（真实数据库）'}")
        print(f"时间: {self.results['timestamp']}")
        print("=" * 60)

        try:
            self.check_entity_counts()
            self.check_chunk_counts()
            self.check_id_formats()
            self.check_foreign_key_integrity()
            self.check_new_fields()

            # 生成摘要
            self.generate_summary()

        except Exception as e:
            print(f"\n❌ 检查过程中出错: {e}")
            import traceback
            traceback.print_exc()
            self.results['error'] = str(e)

    def generate_summary(self):
        """生成检查摘要"""
        print("\n" + "=" * 60)
        print("检查摘要")
        print("=" * 60)

        total_checks = len(self.results['checks'])
        total_issues = len(self.results['issues'])

        self.results['summary'] = {
            'total_checks': total_checks,
            'total_issues': total_issues,
            'status': 'PASS' if total_issues == 0 else 'FAIL'
        }

        print(f"总检查项:   {total_checks}")
        print(f"发现问题:   {total_issues}")
        print(f"总体状态:   {self.results['summary']['status']}")

        if total_issues > 0:
            print(f"\n问题列表:")
            for i, issue in enumerate(self.results['issues'], 1):
                print(f"  {i}. {issue}")
        else:
            print(f"\n✅ 所有检查通过！")

    def save_report(self, output_path: str):
        """保存检查报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 报告已保存: {output_path}")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    print(f"FieldMind 数据一致性验证工具")
    print(f"运行模式: {'MOCK（模拟数据）' if MOCK_MODE else 'REAL（真实数据库）'}")
    print()

    # 初始化数据库连接
    if MOCK_MODE:
        db = MockDatabase()
    else:
        db = RealDatabase(DB_PATH)
        try:
            db.connect()
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return

    # 创建检查器并运行
    checker = ConsistencyChecker(db)
    checker.run_all_checks()

    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"/Users/alwan/Downloads/FieldMind/fieldmind/reports/consistency_report_{timestamp}.json"

    # 确保目录存在
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    checker.save_report(report_path)

    # 关闭数据库连接
    if not MOCK_MODE:
        db.close()

    print("\n✅ 一致性验证完成")


if __name__ == "__main__":
    main()
