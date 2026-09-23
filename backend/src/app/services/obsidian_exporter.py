"""
Obsidian导出服务

将SBPACK导出为Obsidian插件格式
参考标准：
- https://github.com/obsidianmd/obsidian-releases
- https://github.com/kepano/obsidian-skills
"""
import json
import zipfile
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from app.models.sbpack import SBPACKPackage, KnowledgeItem, SkillItem

logger = logging.getLogger(__name__)


class ObsidianExporter:
    """
    Obsidian导出器

    导出格式：
    1. Markdown文件（知识点和技能）
    2. 插件manifest.json
    3. 数据文件（用于插件加载）
    4. 样式和模板
    """

    def __init__(self, db: Session, output_dir: str = "./obsidian_export"):
        self.db = db
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export(self, package_id: int) -> Dict[str, Any]:
        """
        导出SBPACK为Obsidian格式

        参数:
            package_id: SBPACK包ID

        返回:
            导出结果
        """
        logger.info(f"开始导出到Obsidian: package_id={package_id}")

        # 1. 加载包数据
        package = self.db.query(SBPACKPackage).filter(
            SBPACKPackage.id == package_id
        ).first()

        if not package:
            raise ValueError(f"Package {package_id} not found")

        if not package.is_built:
            raise ValueError("Package must be built before export")

        # 2. 创建导出目录
        export_dir = self.output_dir / f"{package.package_name}_obsidian"
        export_dir.mkdir(exist_ok=True)

        # 3. 导出知识点为Markdown
        knowledge_dir = export_dir / "知识库"
        knowledge_dir.mkdir(exist_ok=True)
        self._export_knowledge_notes(package, knowledge_dir)

        # 4. 导出技能为Markdown
        skills_dir = export_dir / "技能库"
        skills_dir.mkdir(exist_ok=True)
        self._export_skill_notes(package, skills_dir)

        # 5. 创建插件文件
        plugin_dir = export_dir / ".obsidian" / "plugins" / "sbpack-reader"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        self._create_plugin_files(package, plugin_dir)

        # 6. 创建首页
        self._create_index_page(package, export_dir)

        # 7. 打包为ZIP
        zip_path = self._create_obsidian_vault_zip(package, export_dir)

        logger.info(f"Obsidian导出完成: {zip_path}")

        return {
            "success": True,
            "export_dir": str(export_dir),
            "zip_path": str(zip_path),
            "knowledge_count": package.knowledge_count,
            "skill_count": package.skill_count
        }

    def _export_knowledge_notes(self, package: SBPACKPackage, output_dir: Path):
        """导出知识点为Markdown笔记"""
        knowledge_items = self.db.query(KnowledgeItem).filter(
            KnowledgeItem.package_id == package.id
        ).all()

        # 按类型分组
        type_dirs = {}
        for item in knowledge_items:
            k_type = item.knowledge_type
            if k_type not in type_dirs:
                type_dir = output_dir / self._translate_knowledge_type(k_type)
                type_dir.mkdir(exist_ok=True)
                type_dirs[k_type] = type_dir

        # 生成Markdown文件
        for item in knowledge_items:
            type_dir = type_dirs[item.knowledge_type]
            note_path = type_dir / f"{self._sanitize_filename(item.title)}.md"

            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(self._generate_knowledge_markdown(item))

        logger.info(f"导出了 {len(knowledge_items)} 个知识点")

    def _export_skill_notes(self, package: SBPACKPackage, output_dir: Path):
        """导出技能为Markdown笔记"""
        skill_items = self.db.query(SkillItem).filter(
            SkillItem.package_id == package.id
        ).all()

        for item in skill_items:
            note_path = output_dir / f"{self._sanitize_filename(item.name)}.md"

            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(self._generate_skill_markdown(item))

        logger.info(f"导出了 {len(skill_items)} 个技能")

    def _generate_knowledge_markdown(self, item: KnowledgeItem) -> str:
        """生成知识点的Markdown内容"""
        md = f"""---
type: knowledge
knowledge_type: {item.knowledge_type}
knowledge_id: {item.knowledge_id}
tags: [知识点, {item.knowledge_type}]
---

# {item.title}

## 陈述

{item.statement}

## 解释

{item.explanation}

## 为什么重要

{item.why_matters}

## 适用范围

{item.scope}
"""

        if item.conditions:
            md += f"\n## 前置条件\n\n{item.conditions}\n"

        if item.boundaries:
            md += f"\n## 边界限制\n\n{item.boundaries}\n"

        if item.counterexamples:
            md += f"\n## 反例\n\n{item.counterexamples}\n"

        # 添加证据引用
        if item.evidence_refs:
            md += "\n## 证据来源\n\n"
            for ref in item.evidence_refs:
                md += f"- Chunk {ref.get('chunk_id', 'N/A')}\n"

        return md

    def _generate_skill_markdown(self, item: SkillItem) -> str:
        """生成技能的Markdown内容"""
        md = f"""---
type: skill
skill_id: {item.skill_id}
tags: [技能, 仓颉v2.0.0]
verification: V1={item.v1_passed}, V2={item.v2_passed}, V3={item.v3_passed}
---

# {item.name}

> {item.description}

## R - Rationale (为什么需要)

{item.rationale}

## I - Interpretation (核心逻辑)

{item.interpretation}

## A1 - Application Original (原始应用)

{item.application_original}

## A2 - Application Future (未来应用)

{item.application_future}

## E - Execution (执行步骤)

"""

        # 添加执行步骤
        execution_steps = item.execution if isinstance(item.execution, list) else []
        for i, step in enumerate(execution_steps, 1):
            md += f"{i}. {step}\n"

        md += f"""

## B - Boundaries (边界)

{item.boundaries}

## 压力测试

"""

        # 添加压力测试
        if item.pressure_tests:
            tests = item.pressure_tests

            if tests.get("should_trigger"):
                md += "\n### ✅ 应该触发\n\n"
                for test in tests["should_trigger"]:
                    md += f"- {test}\n"

            if tests.get("should_not_trigger"):
                md += "\n### ❌ 不应触发\n\n"
                for test in tests["should_not_trigger"]:
                    md += f"- {test}\n"

            if tests.get("boundary_cases"):
                md += "\n### ⚠️ 边界案例\n\n"
                for test in tests["boundary_cases"]:
                    md += f"- {test}\n"

        return md

    def _create_plugin_files(self, package: SBPACKPackage, plugin_dir: Path):
        """创建Obsidian插件文件"""
        # 1. manifest.json
        manifest = {
            "id": "sbpack-reader",
            "name": "SBPACK Reader",
            "version": "1.0.0",
            "minAppVersion": "0.15.0",
            "description": f"SBPACK 2.0 Reader for {package.package_name}",
            "author": "FieldMind",
            "authorUrl": "https://fieldmind.app",
            "isDesktopOnly": False
        }

        with open(plugin_dir / "manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        # 2. data.json - 插件数据
        data = {
            "packageId": package.id,
            "packageName": package.package_name,
            "sourceTitle": package.source_title,
            "sourceAuthor": package.source_author,
            "knowledgeCount": package.knowledge_count,
            "skillCount": package.skill_count,
            "exportedAt": datetime.utcnow().isoformat()
        }

        with open(plugin_dir / "data.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 3. main.js - 简单的插件加载器
        main_js = """
class SBPACKReaderPlugin {
    async onload() {
        console.log('Loading SBPACK Reader plugin');

        // 添加ribbon图标
        this.addRibbonIcon('book', 'SBPACK Reader', () => {
            new Notice('SBPACK Reader loaded!');
        });

        // 添加命令
        this.addCommand({
            id: 'open-sbpack-view',
            name: 'Open SBPACK View',
            callback: () => {
                new Notice('Opening SBPACK view...');
            }
        });
    }

    onunload() {
        console.log('Unloading SBPACK Reader plugin');
    }
}

module.exports = SBPACKReaderPlugin;
"""

        with open(plugin_dir / "main.js", 'w', encoding='utf-8') as f:
            f.write(main_js)

        logger.info(f"Obsidian插件文件已创建: {plugin_dir}")

    def _create_index_page(self, package: SBPACKPackage, export_dir: Path):
        """创建首页"""
        index_content = f"""# {package.source_title}

**作者**: {package.source_author}
**包名**: {package.package_name}
**协议版本**: SBPACK {package.protocol_version}
**导出时间**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📚 知识库 ({package.knowledge_count}个知识点)

[[知识库/]]

## 🎯 技能库 ({package.skill_count}个技能)

[[技能库/]]

---

## 统计信息

- **知识点数量**: {package.knowledge_count}
- **技能数量**: {package.skill_count}
- **关系数量**: {package.relation_count}
- **知识轨状态**: {'已冻结' if package.knowledge_frozen else '未冻结'}
- **技能轨状态**: {'已冻结' if package.skill_frozen else '未冻结'}

---

*本库由FieldMind生成，遵循SBPACK 2.0标准*
"""

        with open(export_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(index_content)

    def _create_obsidian_vault_zip(self, package: SBPACKPackage, export_dir: Path) -> Path:
        """打包为Obsidian vault ZIP"""
        zip_filename = f"{package.package_name}_obsidian_vault.zip"
        zip_path = self.output_dir / zip_filename

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in export_dir.rglob('*'):
                for file in files:
                    file_path = root / file
                    arcname = file_path.relative_to(export_dir)
                    zipf.write(file_path, arcname)

        logger.info(f"Obsidian vault已打包: {zip_path}")
        return zip_path

    def _translate_knowledge_type(self, k_type: str) -> str:
        """翻译知识类型为中文"""
        translations = {
            "concept": "概念",
            "claim": "主张",
            "principle": "原则",
            "mechanism": "机制",
            "reportedFact": "事实",
            "argument": "论证",
            "boundary": "边界",
            "counterexample": "反例"
        }
        return translations.get(k_type, k_type)

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除或替换非法字符
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in illegal_chars:
            name = name.replace(char, '_')

        # 限制长度
        if len(name) > 100:
            name = name[:100]

        return name
