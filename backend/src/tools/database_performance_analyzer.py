#!/usr/bin/env python3
"""
数据库性能分析工具
分析 FieldMind 数据库的查询性能，识别慢查询和瓶颈
"""
import sys
from pathlib import Path
import time
from typing import List, Dict, Any
from datetime import datetime
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from collections import defaultdict

class QueryPerformanceAnalyzer:
    """查询性能分析器"""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=False)
        self.query_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'queries': []
        })

        # 注册查询监听器
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())

        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - conn.info['query_start_time'].pop()

            # 简化 SQL 语句作为 key
            query_key = self._simplify_query(statement)

            self.query_stats[query_key]['count'] += 1
            self.query_stats[query_key]['total_time'] += total_time

            if total_time > 1.0:  # 记录超过1秒的慢查询
                self.query_stats[query_key]['queries'].append({
                    'statement': statement,
                    'time': total_time,
                    'timestamp': datetime.now().isoformat()
                })

    def _simplify_query(self, statement: str) -> str:
        """简化 SQL 语句用于分组"""
        # 移除参数值，只保留查询结构
        import re
        simplified = re.sub(r'\d+', 'N', statement)
        simplified = re.sub(r"'[^']*'", "'X'", simplified)
        return simplified[:100]  # 限制长度

    def analyze_table_indexes(self) -> List[Dict[str, Any]]:
        """分析表索引情况"""
        with self.engine.connect() as conn:
            is_sqlite = 'sqlite' in str(self.engine.url)

            if is_sqlite:
                # SQLite 查询
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master
                    WHERE type='table'
                    AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """))
                tables = [row[0] for row in result]

                index_info = []
                for table in tables:
                    # 获取表的索引
                    result = conn.execute(text(f"""
                        SELECT name, sql
                        FROM sqlite_master
                        WHERE type='index' AND tbl_name=:table
                    """), {"table": table})
                    indexes = [{'name': row[0], 'definition': row[1] or ''} for row in result]

                    # 获取行数
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    row_count = result.scalar() or 0

                    # SQLite 没有直接的表大小查询，估算
                    size = f"~{row_count * 1024} bytes"

                    index_info.append({
                        'table': table,
                        'size': size,
                        'row_count': int(row_count),
                        'indexes': indexes,
                        'index_count': len(indexes)
                    })
            else:
                # PostgreSQL 查询
                result = conn.execute(text("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """))
                tables = [row[0] for row in result]

                index_info = []
                for table in tables:
                    # 获取表的索引
                    result = conn.execute(text(f"""
                        SELECT
                            indexname,
                            indexdef
                        FROM pg_indexes
                        WHERE tablename = :table
                    """), {"table": table})

                    indexes = [{'name': row[0], 'definition': row[1]} for row in result]

                    # 获取表大小
                    result = conn.execute(text(f"""
                        SELECT pg_size_pretty(pg_total_relation_size(:table))
                    """), {"table": table})
                    size = result.scalar()

                    # 获取行数估算
                    result = conn.execute(text(f"""
                        SELECT reltuples::bigint
                        FROM pg_class
                        WHERE relname = :table
                    """), {"table": table})
                    row_count = result.scalar() or 0

                    index_info.append({
                        'table': table,
                        'size': size,
                        'row_count': int(row_count),
                        'indexes': indexes,
                        'index_count': len(indexes)
                    })

            return index_info

    def test_common_queries(self) -> Dict[str, float]:
        """测试常见查询的性能"""
        with Session(self.engine) as session:
            queries = {
                'get_all_projects': """
                    SELECT * FROM projects
                    ORDER BY created_at DESC
                    LIMIT 10
                """,
                'get_project_documents': """
                    SELECT * FROM documents
                    WHERE project_id = 1
                    ORDER BY created_at DESC
                """,
                'get_document_chunks': """
                    SELECT * FROM chunks
                    WHERE document_id IN (
                        SELECT id FROM documents WHERE project_id = 1
                    )
                    LIMIT 100
                """,
                'search_entities': """
                    SELECT * FROM entities
                    WHERE name ILIKE '%test%'
                    LIMIT 20
                """,
                'get_user_projects': """
                    SELECT p.*
                    FROM projects p
                    WHERE p.user_id = 1
                    ORDER BY p.created_at DESC
                """
            }

            results = {}
            for name, query in queries.items():
                start = time.time()
                try:
                    session.execute(text(query))
                    duration = time.time() - start
                    results[name] = duration
                except Exception as e:
                    results[name] = f"Error: {str(e)}"

            return results

    def generate_report(self) -> Dict[str, Any]:
        """生成分析报告"""
        print("=" * 80)
        print("FieldMind 数据库性能分析报告")
        print("=" * 80)
        print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 1. 表索引分析
        print("📊 表索引分析:")
        print("-" * 80)
        index_info = self.analyze_table_indexes()

        for info in index_info:
            print(f"\n表: {info['table']}")
            print(f"  大小: {info['size']}")
            print(f"  行数: {info['row_count']:,}")
            print(f"  索引数: {info['index_count']}")

            if info['index_count'] == 1:  # 只有主键
                print(f"  ⚠️ 建议添加索引")

            if info['row_count'] > 1000 and info['index_count'] < 2:
                print(f"  ⚠️ 大表缺少索引")

        # 2. 常见查询性能测试
        print("\n\n⚡ 常见查询性能测试:")
        print("-" * 80)
        query_results = self.test_common_queries()

        for query_name, duration in query_results.items():
            if isinstance(duration, float):
                status = "✅" if duration < 0.1 else "⚠️" if duration < 1.0 else "❌"
                print(f"{status} {query_name}: {duration*1000:.2f}ms")
            else:
                print(f"❌ {query_name}: {duration}")

        # 3. 慢查询统计
        print("\n\n🐌 慢查询统计 (>1s):")
        print("-" * 80)

        slow_queries = []
        for query_key, stats in self.query_stats.items():
            if stats['queries']:
                for q in stats['queries']:
                    slow_queries.append(q)

        if slow_queries:
            for i, q in enumerate(slow_queries[:10], 1):
                print(f"\n{i}. 耗时: {q['time']:.2f}s")
                print(f"   时间: {q['timestamp']}")
                print(f"   SQL: {q['statement'][:200]}...")
        else:
            print("✅ 未发现慢查询")

        # 4. 索引建议
        print("\n\n💡 索引优化建议:")
        print("-" * 80)

        recommendations = self._generate_index_recommendations(index_info)
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['table']}")
            print(f"   原因: {rec['reason']}")
            print(f"   建议: {rec['recommendation']}")

        return {
            'timestamp': datetime.now().isoformat(),
            'table_info': index_info,
            'query_performance': query_results,
            'slow_queries': slow_queries,
            'recommendations': recommendations
        }

    def _generate_index_recommendations(self, index_info: List[Dict]) -> List[Dict]:
        """生成索引优化建议"""
        recommendations = []

        # 根据表名和常见查询模式生成建议
        index_suggestions = {
            'projects': [
                {
                    'columns': ['user_id', 'created_at'],
                    'reason': '频繁按用户查询并排序',
                    'type': 'btree'
                }
            ],
            'documents': [
                {
                    'columns': ['project_id', 'status'],
                    'reason': '频繁按项目和状态筛选',
                    'type': 'btree'
                },
                {
                    'columns': ['created_at'],
                    'reason': '频繁按时间排序',
                    'type': 'btree'
                }
            ],
            'chunks': [
                {
                    'columns': ['document_id'],
                    'reason': '频繁按文档查询分块',
                    'type': 'btree'
                },
                {
                    'columns': ['vector_id'],
                    'reason': '向量检索关联',
                    'type': 'btree'
                }
            ],
            'entities': [
                {
                    'columns': ['name'],
                    'reason': '频繁按名称搜索',
                    'type': 'btree'
                },
                {
                    'columns': ['type', 'project_id'],
                    'reason': '按类型和项目筛选',
                    'type': 'btree'
                }
            ],
            'project_chat_messages': [
                {
                    'columns': ['session_id', 'created_at'],
                    'reason': '按会话查询消息历史',
                    'type': 'btree'
                }
            ]
        }

        for info in index_info:
            table = info['table']
            if table in index_suggestions:
                for suggestion in index_suggestions[table]:
                    # 检查索引是否已存在
                    existing_indexes = [idx['definition'] for idx in info['indexes']]
                    columns_str = ', '.join(suggestion['columns'])

                    # 简单检查（实际应更精确）
                    index_exists = any(columns_str in idx for idx in existing_indexes)

                    if not index_exists and info['row_count'] > 100:
                        recommendations.append({
                            'table': table,
                            'columns': suggestion['columns'],
                            'reason': suggestion['reason'],
                            'recommendation': f"CREATE INDEX idx_{table}_{'_'.join(suggestion['columns'])} ON {table}({columns_str})"
                        })

        return recommendations


def main():
    """主函数"""
    # 从环境变量或配置读取数据库 URL
    import os

    # 尝试加载 .env
    from dotenv import load_dotenv
    load_dotenv('.env')

    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ 未配置 DATABASE_URL")
        print("请在 .env 文件中配置数据库连接")
        return 1

    # 如果是 SQLite，转换为绝对路径
    if database_url.startswith('sqlite:///'):
        db_path = database_url.replace('sqlite:///', '')
        if not db_path.startswith('/'):
            db_path = str(Path(__file__).parent.parent / db_path)
            database_url = f'sqlite:///{db_path}'

    print(f"连接数据库: {database_url}")
    print()

    # 创建分析器
    analyzer = QueryPerformanceAnalyzer(database_url)

    # 生成报告
    report = analyzer.generate_report()

    # 保存报告
    report_file = Path(__file__).parent / f"db_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n\n📄 完整报告已保存: {report_file}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
