#!/usr/bin/env python3
"""
迁移脚本：将旧的6个知识图谱服务迁移到统一图引擎
Migration script: Migrate from 6 old knowledge graph services to unified graph engine

旧服务 (Old services):
  - app.services.knowledge_graph (227行)
  - app.services.knowledge_graph_v2 (380行)
  - app.services.knowledge_graph_improved (281行)
  - app.services.knowledge_graph_service (302行)
  - app.services.knowledge_graph_builder (296行)
  - app.services.knowledge_graph_builder_optimized (330行)

新引擎 (New engine):
  - app.tools.knowledge.graph.unified_graph_engine (UnifiedKnowledgeGraphEngine, 1457行)
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# 迁移规则映射
MIGRATION_RULES = {
    # knowledge_graph (基础版本)
    "from app.services.knowledge_graph import KnowledgeGraph": {
        "new_import": "from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine",
        "replacements": [
            (r"KnowledgeGraph\(", "UnifiedKnowledgeGraphEngine("),
        ]
    },
    "from app.services.knowledge_graph import get_knowledge_graph": {
        "new_import": "from app.tools.knowledge.graph import create_knowledge_graph",
        "replacements": [
            (r"get_knowledge_graph\(", "create_knowledge_graph("),
        ]
    },

    # knowledge_graph_v2 (v2版本)
    "from app.services.knowledge_graph_v2 import KnowledgeGraphV2": {
        "new_import": "from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine",
        "replacements": [
            (r"KnowledgeGraphV2\(", "UnifiedKnowledgeGraphEngine("),
        ]
    },
    "from app.services.knowledge_graph_v2 import get_knowledge_graph_v2": {
        "new_import": "from app.tools.knowledge.graph import create_knowledge_graph",
        "replacements": [
            (r"get_knowledge_graph_v2\(", "create_knowledge_graph("),
        ]
    },

    # knowledge_graph_improved (改进版本)
    "from app.services.knowledge_graph_improved import ImprovedKnowledgeGraph": {
        "new_import": "from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine",
        "replacements": [
            (r"ImprovedKnowledgeGraph\(", "UnifiedKnowledgeGraphEngine("),
        ]
    },

    # knowledge_graph_service (服务版本)
    "from app.services.knowledge_graph_service import KnowledgeGraphService": {
        "new_import": "from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine",
        "replacements": [
            (r"KnowledgeGraphService\(", "UnifiedKnowledgeGraphEngine("),
        ]
    },
    "from app.services.knowledge_graph_service import get_knowledge_graph_service": {
        "new_import": "from app.tools.knowledge.graph import create_knowledge_graph",
        "replacements": [
            (r"get_knowledge_graph_service\(", "create_knowledge_graph("),
        ]
    },

    # knowledge_graph_builder (构建器版本)
    "from app.services.knowledge_graph_builder import KnowledgeGraphBuilder": {
        "new_import": "from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine",
        "replacements": [
            (r"KnowledgeGraphBuilder\(", "UnifiedKnowledgeGraphEngine("),
        ]
    },
    "from app.services.knowledge_graph_builder import get_entity_extraction_service": {
        "new_import": "from app.tools.entity import create_engine",
        "replacements": [
            (r"get_entity_extraction_service\(", "create_engine("),
        ]
    },

    # knowledge_graph_builder_optimized (优化版本)
    "from app.services.knowledge_graph_builder_optimized import OptimizedKnowledgeGraphBuilder": {
        "new_import": "from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine",
        "replacements": [
            (r"OptimizedKnowledgeGraphBuilder\(", "UnifiedKnowledgeGraphEngine("),
        ]
    },
}


class KnowledgeGraphMigrationScript:
    """知识图谱服务迁移脚本"""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.migrated_files: List[str] = []
        self.skipped_files: List[str] = []
        self.errors: List[Tuple[str, str]] = []

    def find_files_to_migrate(self) -> List[Path]:
        """查找需要迁移的文件"""
        files_to_migrate = []

        # 扫描整个backend/src目录
        for py_file in self.root_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")

                # 检查是否包含旧的导入
                for old_import in MIGRATION_RULES.keys():
                    if old_import in content:
                        files_to_migrate.append(py_file)
                        break
            except Exception as e:
                self.errors.append((str(py_file), f"读取文件失败: {e}"))

        return files_to_migrate

    def migrate_file(self, file_path: Path) -> bool:
        """迁移单个文件"""
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # 跟踪已添加的导入，避免重复
            new_imports_added = set()

            # 应用迁移规则
            for old_import, rule in MIGRATION_RULES.items():
                if old_import in content:
                    # 替换导入语句
                    new_import = rule["new_import"]
                    if new_import not in new_imports_added:
                        content = content.replace(old_import, new_import)
                        new_imports_added.add(new_import)
                    else:
                        # 如果新导入已存在，直接删除旧导入
                        content = content.replace(old_import + "\n", "")

                    # 应用代码替换规则
                    for pattern, replacement in rule["replacements"]:
                        content = re.sub(pattern, replacement, content)

            # 只有内容真正改变时才写入
            if content != original_content:
                # 备份原文件
                backup_path = file_path.with_suffix(".py.bak")
                file_path.rename(backup_path)

                # 写入新内容
                file_path.write_text(content, encoding="utf-8")

                self.migrated_files.append(str(file_path.relative_to(self.root_dir)))
                return True
            else:
                self.skipped_files.append(str(file_path.relative_to(self.root_dir)))
                return False

        except Exception as e:
            self.errors.append((str(file_path), f"迁移失败: {e}"))
            return False

    def run(self) -> Dict:
        """执行迁移"""
        print("=" * 60)
        print("知识图谱服务迁移脚本 (Knowledge Graph Migration)")
        print("=" * 60)
        print()

        # 查找需要迁移的文件
        print("🔍 扫描需要迁移的文件...")
        files_to_migrate = self.find_files_to_migrate()
        print(f"   找到 {len(files_to_migrate)} 个文件需要迁移\n")

        if not files_to_migrate:
            print("✅ 没有文件需要迁移")
            return {
                "total": 0,
                "migrated": 0,
                "skipped": 0,
                "errors": 0
            }

        # 迁移每个文件
        print("🔄 开始迁移...\n")
        for file_path in files_to_migrate:
            relative_path = file_path.relative_to(self.root_dir)
            print(f"   处理: {relative_path}")
            self.migrate_file(file_path)

        # 输出结果
        print("\n" + "=" * 60)
        print("迁移结果 (Migration Results)")
        print("=" * 60)
        print(f"✅ 成功迁移: {len(self.migrated_files)} 个文件")
        print(f"⏭️  跳过: {len(self.skipped_files)} 个文件")
        print(f"❌ 错误: {len(self.errors)} 个文件")
        print()

        if self.migrated_files:
            print("已迁移的文件:")
            for file in self.migrated_files:
                print(f"  ✓ {file}")
            print()

        if self.skipped_files:
            print("跳过的文件 (无需更改):")
            for file in self.skipped_files:
                print(f"  - {file}")
            print()

        if self.errors:
            print("错误:")
            for file, error in self.errors:
                print(f"  ✗ {file}: {error}")
            print()

        return {
            "total": len(files_to_migrate),
            "migrated": len(self.migrated_files),
            "skipped": len(self.skipped_files),
            "errors": len(self.errors),
            "migrated_files": self.migrated_files,
            "error_details": self.errors
        }


def main():
    """主函数"""
    import sys

    # 确定根目录
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        # 默认为backend/src目录
        root_dir = Path(__file__).parent / "app"

    # 执行迁移
    migrator = KnowledgeGraphMigrationScript(root_dir)
    results = migrator.run()

    # 返回退出码
    if results["errors"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
