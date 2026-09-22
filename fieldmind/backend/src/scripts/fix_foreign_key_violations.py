#!/usr/bin/env python3
"""修复数据库外键约束违规"""

import sqlite3
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = Path(__file__).parent.parent / 'data' / 'fieldmind.db'


def check_violations(conn):
    """检查外键约束违规"""
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_key_check')
    violations = cursor.fetchall()
    return violations


def fix_document_chunks_violations(conn):
    """修复 document_chunks 表的外键违规"""
    cursor = conn.cursor()

    # 查找并删除引用不存在documents的chunks
    cursor.execute('''
        SELECT dc.id, dc.document_id, dc.project_id
        FROM document_chunks dc
        LEFT JOIN documents d ON dc.document_id = d.id
        WHERE d.id IS NULL
    ''')
    orphan_docs = cursor.fetchall()

    if orphan_docs:
        print(f'  发现 {len(orphan_docs)} 条引用无效document的chunks')
        chunk_ids = [row[0] for row in orphan_docs]
        cursor.execute(f'''
            DELETE FROM document_chunks
            WHERE id IN ({','.join('?' * len(chunk_ids))})
        ''', chunk_ids)
        print(f'  已删除 {cursor.rowcount} 条孤立chunks')

    # 查找并修复引用不存在projects的chunks
    cursor.execute('''
        SELECT dc.id, dc.project_id
        FROM document_chunks dc
        LEFT JOIN projects p ON dc.project_id = p.id
        WHERE dc.project_id IS NOT NULL AND p.id IS NULL
    ''')
    orphan_projects = cursor.fetchall()

    if orphan_projects:
        print(f'  发现 {len(orphan_projects)} 条引用无效project的chunks')
        # 选项1: 删除这些chunks
        # 选项2: 将project_id设为NULL（如果允许）
        # 这里选择删除
        chunk_ids = [row[0] for row in orphan_projects]
        cursor.execute(f'''
            DELETE FROM document_chunks
            WHERE id IN ({','.join('?' * len(chunk_ids))})
        ''', chunk_ids)
        print(f'  已删除 {cursor.rowcount} 条孤立chunks')


def fix_document_artifacts_violations(conn):
    """修复 document_artifacts 表的外键违规"""
    cursor = conn.cursor()

    # 检查引用documents表的违规
    cursor.execute('''
        SELECT da.id, da.document_id
        FROM document_artifacts da
        LEFT JOIN documents d ON da.document_id = d.id
        WHERE d.id IS NULL
    ''')
    orphans = cursor.fetchall()

    if orphans:
        print(f'  发现 {len(orphans)} 条引用无效document的artifacts')
        artifact_ids = [row[0] for row in orphans]
        cursor.execute(f'''
            DELETE FROM document_artifacts
            WHERE id IN ({','.join('?' * len(artifact_ids))})
        ''', artifact_ids)
        print(f'  已删除 {cursor.rowcount} 条孤立artifacts')

    # 检查引用project_documents表的违规
    cursor.execute('''
        SELECT da.id, da.document_id
        FROM document_artifacts da
        LEFT JOIN project_documents pd ON da.document_id = pd.id
        WHERE pd.id IS NULL AND da.document_id IS NOT NULL
    ''')
    orphans_pd = cursor.fetchall()

    if orphans_pd:
        print(f'  发现 {len(orphans_pd)} 条引用无效project_document的artifacts')
        artifact_ids = [row[0] for row in orphans_pd]
        cursor.execute(f'''
            DELETE FROM document_artifacts
            WHERE id IN ({','.join('?' * len(artifact_ids))})
        ''', artifact_ids)
        print(f'  已删除 {cursor.rowcount} 条孤立artifacts')


def fix_project_documents_violations(conn):
    """修复 project_documents 表的外键违规"""
    cursor = conn.cursor()

    # 检查引用不存在的projects
    cursor.execute('''
        SELECT pd.id, pd.project_id
        FROM project_documents pd
        LEFT JOIN projects p ON pd.project_id = p.id
        WHERE p.id IS NULL
    ''')
    orphan_projects = cursor.fetchall()

    if orphan_projects:
        print(f'  发现 {len(orphan_projects)} 条引用无效project的关联')
        ids = [row[0] for row in orphan_projects]
        cursor.execute(f'''
            DELETE FROM project_documents
            WHERE id IN ({','.join('?' * len(ids))})
        ''', ids)
        print(f'  已删除 {cursor.rowcount} 条无效关联')


def fix_projects_violations(conn):
    """修复 projects 表的外键违规"""
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.id, p.owner_id
        FROM projects p
        LEFT JOIN users u ON p.owner_id = u.id
        WHERE p.owner_id IS NOT NULL AND u.id IS NULL
    ''')
    orphans = cursor.fetchall()

    if orphans:
        print(f'  发现 {len(orphans)} 条引用无效user的projects')
        print(f'  选项: 删除projects 或 设置默认owner_id')
        # 这里选择设置为NULL（如果允许）或删除
        project_ids = [row[0] for row in orphans]

        # 尝试设置为NULL
        try:
            cursor.execute(f'''
                UPDATE projects
                SET owner_id = NULL
                WHERE id IN ({','.join('?' * len(project_ids))})
            ''', project_ids)
            print(f'  已将 {cursor.rowcount} 条projects的owner_id设为NULL')
        except sqlite3.IntegrityError:
            # 如果不允许NULL，则删除
            cursor.execute(f'''
                DELETE FROM projects
                WHERE id IN ({','.join('?' * len(project_ids))})
            ''', project_ids)
            print(f'  已删除 {cursor.rowcount} 条无效projects')


def fix_chunk_keywords_violations(conn):
    """修复 chunk_keywords 表的外键违规"""
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ck.id, ck.chunk_id
        FROM chunk_keywords ck
        LEFT JOIN document_chunks dc ON ck.chunk_id = dc.id
        WHERE dc.id IS NULL
    ''')
    orphans = cursor.fetchall()

    if orphans:
        print(f'  发现 {len(orphans)} 条引用无效chunk的keywords')
        ids = [row[0] for row in orphans]
        cursor.execute(f'''
            DELETE FROM chunk_keywords
            WHERE id IN ({','.join('?' * len(ids))})
        ''', ids)
        print(f'  已删除 {cursor.rowcount} 条孤立keywords')


def fix_chunk_entities_violations(conn):
    """修复 chunk_entities 表的外键违规"""
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ce.id, ce.chunk_id
        FROM chunk_entities ce
        LEFT JOIN document_chunks dc ON ce.chunk_id = dc.id
        WHERE dc.id IS NULL
    ''')
    orphans = cursor.fetchall()

    if orphans:
        print(f'  发现 {len(orphans)} 条引用无效chunk的entities')
        ids = [row[0] for row in orphans]
        cursor.execute(f'''
            DELETE FROM chunk_entities
            WHERE id IN ({','.join('?' * len(ids))})
        ''', ids)
        print(f'  已删除 {cursor.rowcount} 条孤立entities')


def fix_project_document_tags_violations(conn):
    """修复 project_document_tags 表的外键违规"""
    cursor = conn.cursor()

    cursor.execute('''
        SELECT pdt.id, pdt.document_id
        FROM project_document_tags pdt
        LEFT JOIN project_documents pd ON pdt.document_id = pd.id
        WHERE pd.id IS NULL
    ''')
    orphans = cursor.fetchall()

    if orphans:
        print(f'  发现 {len(orphans)} 条引用无效document的tags')
        ids = [row[0] for row in orphans]
        cursor.execute(f'''
            DELETE FROM project_document_tags
            WHERE id IN ({','.join('?' * len(ids))})
        ''', ids)
        print(f'  已删除 {cursor.rowcount} 条孤立tags')


def fix_project_document_assets_violations(conn):
    """修复 project_document_assets 表的外键违规"""
    cursor = conn.cursor()

    cursor.execute('''
        SELECT pda.id, pda.document_id
        FROM project_document_assets pda
        LEFT JOIN project_documents pd ON pda.document_id = pd.id
        WHERE pd.id IS NULL
    ''')
    orphans = cursor.fetchall()

    if orphans:
        print(f'  发现 {len(orphans)} 条引用无效document的assets')
        ids = [row[0] for row in orphans]
        cursor.execute(f'''
            DELETE FROM project_document_assets
            WHERE id IN ({','.join('?' * len(ids))})
        ''', ids)
        print(f'  已删除 {cursor.rowcount} 条孤立assets')


def fix_document_processing_results_violations(conn):
    """修复 document_processing_results 表的外键违规"""
    cursor = conn.cursor()

    cursor.execute('''
        SELECT dpr.id, dpr.document_id
        FROM document_processing_results dpr
        LEFT JOIN documents d ON dpr.document_id = d.id
        WHERE d.id IS NULL
    ''')
    orphans = cursor.fetchall()

    if orphans:
        print(f'  发现 {len(orphans)} 条引用无效document的processing_results')
        ids = [row[0] for row in orphans]
        cursor.execute(f'''
            DELETE FROM document_processing_results
            WHERE id IN ({','.join('?' * len(ids))})
        ''', ids)
        print(f'  已删除 {cursor.rowcount} 条孤立processing_results')


def main():
    """主修复流程"""
    print(f'数据库路径: {DB_PATH}')

    if not DB_PATH.exists():
        print(f'错误: 数据库不存在')
        return 1

    # 备份数据库
    backup_path = DB_PATH.with_suffix('.db.backup')
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f'已备份数据库到: {backup_path}\n')

    conn = sqlite3.connect(DB_PATH)

    try:
        # 检查初始违规
        violations = check_violations(conn)
        print(f'初始外键约束违规: {len(violations)} 条\n')

        if len(violations) == 0:
            print('✓ 无外键约束违规')
            return 0

        # 开始修复
        print('开始修复...\n')

        print('1. 修复 document_chunks 表:')
        fix_document_chunks_violations(conn)

        print('\n2. 修复 document_artifacts 表:')
        fix_document_artifacts_violations(conn)

        print('\n3. 修复 project_documents 表:')
        fix_project_documents_violations(conn)

        print('\n4. 修复 projects 表:')
        fix_projects_violations(conn)

        print('\n5. 修复 chunk_keywords 表:')
        fix_chunk_keywords_violations(conn)

        print('\n6. 修复 chunk_entities 表:')
        fix_chunk_entities_violations(conn)

        print('\n7. 修复 project_document_tags 表:')
        fix_project_document_tags_violations(conn)

        print('\n8. 修复 project_document_assets 表:')
        fix_project_document_assets_violations(conn)

        print('\n9. 修复 document_processing_results 表:')
        fix_document_processing_results_violations(conn)

        # 提交事务
        conn.commit()
        print('\n事务已提交')

        # 重新检查
        violations = check_violations(conn)
        print(f'\n修复后外键约束违规: {len(violations)} 条')

        if len(violations) == 0:
            print('✓ 所有外键约束违规已修复')
            return 0
        else:
            print(f'⚠ 仍有 {len(violations)} 条违规需要手动处理')
            for v in violations[:5]:
                print(f'  表: {v[0]}, 行ID: {v[1]}, 引用: {v[2]}')
            return 1

    except Exception as e:
        conn.rollback()
        print(f'\n错误: {e}')
        print('事务已回滚')
        return 1
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
