#!/usr/bin/env python3
"""
Week 3: Chunk ID 迁移脚本

功能：
1. 为所有 document_chunks 生成新的统一 ID 格式：chk_xxxxxxxxxxxx
2. 更新 document_chunks 表的 chunk_id 字段
3. 更新所有外键引用（prev_chunk_id, next_chunk_id）
4. 记录所有 ID 映射到 id_mapping 表
5. 批量处理，支持大数据集

目标：
- 将 1,036 个 chunks 从旧格式 (doc_X_chunk_Y) 迁移到新格式 (chk_xxxxxxxxxxxx)
- 保证数据完整性和外键一致性
- 创建完整的迁移日志

执行时间：2026-01-XX
作者：FieldMind Architecture Team
"""

import os
import sys
import sqlite3
import uuid
import re
from datetime import datetime
from typing import Dict, List, Tuple

# ============================================================================
# 配置
# ============================================================================

DB_PATH = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
BATCH_SIZE = 100  # 每批处理的记录数
DRY_RUN = False   # 设置为 True 仅模拟，不实际修改数据库

# ID 前缀
CHUNK_PREFIX = "chk"

# ============================================================================
# ID 生成器
# ============================================================================

def generate_chunk_id() -> str:
    """生成新的 Chunk ID"""
    unique_part = uuid.uuid4().hex[:12]
    return f"{CHUNK_PREFIX}_{unique_part}"

def validate_chunk_id(chunk_id: str) -> bool:
    """验证 Chunk ID 格式"""
    pattern = r'^chk_[a-f0-9]{12}$'
    return bool(re.match(pattern, chunk_id))

# ============================================================================
# 数据库操作
# ============================================================================

class ChunkIDMigrator:
    """Chunk ID 迁移器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.stats = {
            'total_chunks': 0,
            'migrated': 0,
            'fk_updated': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        self.id_mapping = {}  # old_id -> new_id

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

    def get_all_chunks(self) -> List[Dict]:
        """获取所有 chunks"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, chunk_id, prev_chunk_id, next_chunk_id
            FROM document_chunks
            ORDER BY id
        """)
        chunks = [dict(row) for row in cursor.fetchall()]
        self.stats['total_chunks'] = len(chunks)
        return chunks

    def generate_id_mapping(self, chunks: List[Dict]) -> Dict[str, str]:
        """生成 old_id -> new_id 映射"""
        print(f"\n📝 生成 ID 映射...")
        print(f"   总 Chunk 数: {len(chunks)}")

        mapping = {}

        for chunk in chunks:
            old_id = chunk['chunk_id']
            new_id = generate_chunk_id()

            # 确保新 ID 唯一
            while new_id in mapping.values():
                new_id = generate_chunk_id()

            mapping[old_id] = new_id

        self.id_mapping = mapping
        print(f"✅ ID 映射已生成: {len(mapping)} 条")
        return mapping

    def save_id_mapping_to_db(self):
        """保存 ID 映射到 id_mapping 表"""
        if DRY_RUN:
            print(f"\n[DRY RUN] 跳过保存 ID 映射")
            return

        print(f"\n💾 保存 ID 映射到数据库...")
        cursor = self.conn.cursor()

        batch_id = f"chunks_id_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        saved_count = 0

        for old_id, new_id in self.id_mapping.items():
            try:
                cursor.execute("""
                    INSERT INTO id_mapping (
                        entity_type, table_name, old_id, new_id,
                        migration_batch
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    'chunk',
                    'document_chunks',
                    old_id,
                    new_id,
                    batch_id
                ))
                saved_count += 1
            except sqlite3.IntegrityError as e:
                print(f"⚠️  ID 映射已存在: {old_id} -> {new_id}")

        self.conn.commit()
        print(f"✅ ID 映射已保存: {saved_count} 条")

    def update_chunk_ids_batch(self, chunks: List[Dict]) -> int:
        """批量更新 chunk_id"""
        if DRY_RUN:
            print(f"\n[DRY RUN] 模拟更新 {len(chunks)} 个 chunk_id")
            return len(chunks)

        cursor = self.conn.cursor()
        updated = 0

        for chunk in chunks:
            old_id = chunk['chunk_id']
            new_id = self.id_mapping.get(old_id)

            if not new_id:
                print(f"⚠️  未找到映射: {old_id}")
                self.stats['errors'] += 1
                continue

            try:
                cursor.execute("""
                    UPDATE document_chunks
                    SET chunk_id = ?
                    WHERE id = ?
                """, (new_id, chunk['id']))
                updated += 1
            except Exception as e:
                print(f"❌ 更新失败 (id={chunk['id']}): {e}")
                self.stats['errors'] += 1

        self.conn.commit()
        return updated

    def update_foreign_keys(self, chunks: List[Dict]) -> int:
        """更新外键引用 (prev_chunk_id, next_chunk_id)"""
        if DRY_RUN:
            print(f"\n[DRY RUN] 模拟更新外键引用")
            return 0

        print(f"\n🔗 更新外键引用...")
        cursor = self.conn.cursor()
        updated = 0

        for chunk in chunks:
            old_chunk_id = chunk['chunk_id']
            new_chunk_id = self.id_mapping.get(old_chunk_id)

            # 更新 prev_chunk_id
            new_prev = None
            if chunk['prev_chunk_id']:
                new_prev = self.id_mapping.get(chunk['prev_chunk_id'])

            # 更新 next_chunk_id
            new_next = None
            if chunk['next_chunk_id']:
                new_next = self.id_mapping.get(chunk['next_chunk_id'])

            try:
                cursor.execute("""
                    UPDATE document_chunks
                    SET prev_chunk_id = ?,
                        next_chunk_id = ?
                    WHERE chunk_id = ?
                """, (new_prev, new_next, new_chunk_id))
                updated += 1
            except Exception as e:
                print(f"❌ 更新外键失败 (chunk_id={new_chunk_id}): {e}")
                self.stats['errors'] += 1

        self.conn.commit()
        print(f"✅ 外键引用已更新: {updated} 条")
        return updated

    def log_migration(self):
        """记录迁移日志"""
        if DRY_RUN:
            print(f"\n[DRY RUN] 跳过记录迁移日志")
            return

        cursor = self.conn.cursor()

        batch_id = f"chunks_id_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        metadata = {
            'total_chunks': self.stats['total_chunks'],
            'migrated': self.stats['migrated'],
            'fk_updated': self.stats['fk_updated'],
            'errors': self.stats['errors'],
            'note': f"Migrated {self.stats['migrated']} chunks to new ID format (chk_xxxxxxxxxxxx)"
        }

        cursor.execute("""
            INSERT INTO migration_log (
                batch_id, table_name, operation, records_affected,
                started_at, completed_at, status, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id,
            'document_chunks',
            'chunk_id_migration',
            self.stats['migrated'],
            self.stats['start_time'],
            self.stats['end_time'],
            'completed' if self.stats['errors'] == 0 else 'completed_with_errors',
            str(metadata)
        ))

        self.conn.commit()
        print(f"✅ 迁移日志已记录")

    def run_migration(self):
        """执行完整迁移流程"""
        print("=" * 70)
        print("Chunk ID 迁移")
        print(f"模式: {'DRY RUN（模拟）' if DRY_RUN else 'REAL（真实执行）'}")
        print("=" * 70)

        self.stats['start_time'] = datetime.now().isoformat()

        try:
            # 1. 获取所有 chunks
            print("\n[步骤 1/5] 获取所有 Chunks")
            chunks = self.get_all_chunks()
            print(f"✅ 获取成功: {len(chunks)} 条记录")

            # 2. 生成 ID 映射
            print("\n[步骤 2/5] 生成 ID 映射")
            self.generate_id_mapping(chunks)

            # 显示映射示例
            print("\n映射示例（前 5 条）:")
            for i, (old_id, new_id) in enumerate(list(self.id_mapping.items())[:5]):
                print(f"  {old_id:25s} -> {new_id}")

            # 3. 保存 ID 映射
            print("\n[步骤 3/5] 保存 ID 映射")
            self.save_id_mapping_to_db()

            # 4. 批量更新 chunk_id
            print("\n[步骤 4/5] 批量更新 chunk_id")
            print(f"批量大小: {BATCH_SIZE}")

            total_updated = 0
            for i in range(0, len(chunks), BATCH_SIZE):
                batch = chunks[i:i + BATCH_SIZE]
                updated = self.update_chunk_ids_batch(batch)
                total_updated += updated
                print(f"  批次 {i//BATCH_SIZE + 1}: 更新 {updated} 条 "
                      f"(进度: {i + len(batch)}/{len(chunks)})")

            self.stats['migrated'] = total_updated
            print(f"✅ Chunk ID 更新完成: {total_updated} 条")

            # 5. 更新外键引用
            print("\n[步骤 5/5] 更新外键引用")
            fk_updated = self.update_foreign_keys(chunks)
            self.stats['fk_updated'] = fk_updated

            self.stats['end_time'] = datetime.now().isoformat()

            # 6. 记录迁移日志
            print("\n[收尾] 记录迁移日志")
            self.log_migration()

            # 打印统计
            self.print_stats()

        except Exception as e:
            print(f"\n❌ 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            self.stats['end_time'] = datetime.now().isoformat()
            raise

    def print_stats(self):
        """打印统计信息"""
        print("\n" + "=" * 70)
        print("迁移统计")
        print("=" * 70)

        start = datetime.fromisoformat(self.stats['start_time'])
        end = datetime.fromisoformat(self.stats['end_time'])
        duration = (end - start).total_seconds()

        print(f"总 Chunk 数:       {self.stats['total_chunks']}")
        print(f"成功迁移:          {self.stats['migrated']}")
        print(f"外键更新:          {self.stats['fk_updated']}")
        print(f"错误数:            {self.stats['errors']}")
        print(f"执行时间:          {duration:.2f} 秒")
        print(f"处理速度:          {self.stats['total_chunks']/duration:.0f} 条/秒" if duration > 0 else "N/A")

        if self.stats['errors'] == 0:
            print(f"\n✅ 迁移成功完成！")
        else:
            print(f"\n⚠️  迁移完成，但有 {self.stats['errors']} 个错误")

    def verify_migration(self):
        """验证迁移结果"""
        print("\n" + "=" * 70)
        print("验证迁移结果")
        print("=" * 70)

        cursor = self.conn.cursor()

        # 检查新 ID 格式
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM document_chunks
            WHERE chunk_id LIKE 'chk_%'
        """)
        new_format_count = cursor.fetchone()['count']

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM document_chunks
            WHERE chunk_id NOT LIKE 'chk_%'
        """)
        old_format_count = cursor.fetchone()['count']

        print(f"\nID 格式统计:")
        print(f"  新格式 (chk_xxxxxxxxxxxx): {new_format_count}")
        print(f"  旧格式 (其他):              {old_format_count}")

        if old_format_count == 0:
            print(f"\n✅ 所有 Chunk ID 已迁移到新格式")
        else:
            print(f"\n⚠️  还有 {old_format_count} 个 Chunk 使用旧格式")

        # 检查 ID 映射表
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM id_mapping
            WHERE entity_type = 'chunk'
        """)
        mapping_count = cursor.fetchone()['count']
        print(f"\nID 映射记录数: {mapping_count}")

        # 检查外键引用
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM document_chunks
            WHERE prev_chunk_id IS NOT NULL
              AND prev_chunk_id NOT LIKE 'chk_%'
        """)
        bad_prev_count = cursor.fetchone()['count']

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM document_chunks
            WHERE next_chunk_id IS NOT NULL
              AND next_chunk_id NOT LIKE 'chk_%'
        """)
        bad_next_count = cursor.fetchone()['count']

        print(f"\n外键引用检查:")
        print(f"  prev_chunk_id 旧格式: {bad_prev_count}")
        print(f"  next_chunk_id 旧格式: {bad_next_count}")

        if bad_prev_count == 0 and bad_next_count == 0:
            print(f"\n✅ 所有外键引用已更新")
        else:
            print(f"\n⚠️  还有外键引用使用旧格式")

        # 显示新 ID 示例
        cursor.execute("""
            SELECT chunk_id, prev_chunk_id, next_chunk_id
            FROM document_chunks
            LIMIT 5
        """)
        print(f"\n新 ID 示例（前 5 条）:")
        for row in cursor.fetchall():
            print(f"  chunk_id:      {row['chunk_id']}")
            print(f"  prev_chunk_id: {row['prev_chunk_id'] or 'NULL'}")
            print(f"  next_chunk_id: {row['next_chunk_id'] or 'NULL'}")
            print()

# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    migrator = ChunkIDMigrator(DB_PATH)

    try:
        # 连接数据库
        migrator.connect()

        # 执行迁移
        migrator.run_migration()

        # 验证结果
        if not DRY_RUN:
            migrator.verify_migration()

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        sys.exit(1)

    finally:
        # 关闭连接
        migrator.close()

    print("\n✅ 所有操作完成")

if __name__ == "__main__":
    main()
