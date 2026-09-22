"""
批量生成缩影脚本
Batch Generate Summaries Script

功能：
1. 为项目中所有未生成缩影的文档批量生成缩影
2. 支持指定项目ID或处理所有项目
3. 显示进度条和统计信息
4. 错误处理和日志记录

使用方式：
    # 为项目1的所有文档生成缩影
    python batch_generate_summaries.py --project-id 1

    # 为所有项目生成缩影
    python batch_generate_summaries.py --all

    # 强制重新生成已有缩影
    python batch_generate_summaries.py --project-id 1 --force
"""

import sys
import os
import argparse
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.project import ProjectDocument, Project
from app.services.summary_generator import FileSummaryGenerator, save_summary
from sqlalchemy import text
import time


def batch_generate_summaries(project_id: int = None, force: bool = False):
    """
    批量生成缩影

    Args:
        project_id: 项目ID（None表示所有项目）
        force: 是否强制重新生成已有缩影
    """

    db = SessionLocal()

    try:
        # 查询需要生成缩影的文档
        query = db.query(ProjectDocument).filter(
            ProjectDocument.status == 'completed'
        )

        if project_id:
            query = query.filter(ProjectDocument.project_id == project_id)

        documents = query.all()

        if not documents:
            print("没有找到需要生成缩影的文档")
            return

        print(f"\n{'='*60}")
        print(f"批量生成缩影任务")
        print(f"{'='*60}")
        print(f"项目ID: {project_id if project_id else '所有项目'}")
        print(f"文档数量: {len(documents)}")
        print(f"强制重新生成: {'是' if force else '否'}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        # 统计信息
        total = len(documents)
        success_count = 0
        skip_count = 0
        error_count = 0
        start_time = time.time()

        generator = FileSummaryGenerator(db)

        for i, doc in enumerate(documents, 1):
            print(f"[{i}/{total}] 处理文档: {doc.original_filename} (ID: {doc.id})")

            try:
                # 检查是否已有缩影
                if not force:
                    existing = db.execute(text("""
                        SELECT id FROM file_summaries
                        WHERE document_id = :document_id AND status = 'done'
                    """), {'document_id': doc.id}).fetchone()

                    if existing:
                        print(f"  ⏭️  跳过（已有缩影）")
                        skip_count += 1
                        continue

                # 生成缩影
                print(f"  🔄 生成中...")
                summary_data = generator.generate_summary(doc.id)

                # 保存到数据库
                save_summary(db, summary_data)

                print(f"  ✅ 成功")
                print(f"     摘要: {summary_data['one_line_summary'][:50]}...")
                print(f"     关键词: {len(summary_data['top_keywords'])} 个")
                print(f"     字数: {summary_data['word_count']}")

                success_count += 1

            except Exception as e:
                print(f"  ❌ 失败: {e}")
                error_count += 1

            # 显示进度
            progress = (i / total) * 100
            print(f"  进度: {progress:.1f}% ({i}/{total})\n")

        # 总结
        elapsed_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"批量生成完成")
        print(f"{'='*60}")
        print(f"总文档数: {total}")
        print(f"成功生成: {success_count}")
        print(f"跳过: {skip_count}")
        print(f"失败: {error_count}")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"平均耗时: {elapsed_time/total:.2f} 秒/文档")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n❌ 批量生成失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


def list_projects():
    """列出所有项目"""

    db = SessionLocal()

    try:
        projects = db.query(Project).all()

        print(f"\n{'='*60}")
        print(f"项目列表")
        print(f"{'='*60}\n")

        for project in projects:
            # 统计文档数
            doc_count = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project.id,
                ProjectDocument.status == 'completed'
            ).count()

            # 统计缩影数
            summary_count = db.execute(text("""
                SELECT COUNT(*) FROM file_summaries
                WHERE project_id = :project_id AND status = 'done'
            """), {'project_id': project.id}).scalar()

            print(f"项目ID: {project.id}")
            print(f"项目名称: {project.name}")
            print(f"文档数: {doc_count}")
            print(f"已生成缩影: {summary_count}")
            print(f"未生成缩影: {doc_count - summary_count}")
            print()

    finally:
        db.close()


def main():
    """主函数"""

    parser = argparse.ArgumentParser(
        description='批量生成文档缩影',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
    # 查看所有项目
    python batch_generate_summaries.py --list

    # 为项目1生成缩影
    python batch_generate_summaries.py --project-id 1

    # 为所有项目生成缩影
    python batch_generate_summaries.py --all

    # 强制重新生成
    python batch_generate_summaries.py --project-id 1 --force
        """
    )

    parser.add_argument('--project-id', type=int, help='项目ID')
    parser.add_argument('--all', action='store_true', help='处理所有项目')
    parser.add_argument('--force', action='store_true', help='强制重新生成已有缩影')
    parser.add_argument('--list', action='store_true', help='列出所有项目')

    args = parser.parse_args()

    # 列出项目
    if args.list:
        list_projects()
        return

    # 验证参数
    if not args.project_id and not args.all:
        parser.print_help()
        print("\n错误: 必须指定 --project-id 或 --all")
        sys.exit(1)

    # 执行批量生成
    batch_generate_summaries(
        project_id=args.project_id,
        force=args.force
    )


if __name__ == "__main__":
    main()
