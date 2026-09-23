"""
Obsidian实时同步引擎

FieldMind ⟷ Obsidian 双向实时同步：
- 监听Obsidian vault文件变化
- 自动同步到FieldMind数据库
- FieldMind修改实时推送到Obsidian
- 冲突检测和解决
"""
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
import logging
from sqlalchemy.orm import Session

from app.core.obsidian_compat import MarkdownNote, ObsidianDataStore

logger = logging.getLogger(__name__)


class ObsidianVaultWatcher(FileSystemEventHandler):
    """
    Obsidian vault文件监听器

    监听vault目录中的所有Markdown文件变化
    """

    def __init__(self, sync_engine: 'ObsidianSyncEngine'):
        self.sync_engine = sync_engine
        self.last_sync_times: Dict[str, float] = {}

    def on_modified(self, event: FileModifiedEvent):
        """文件被修改"""
        if event.is_directory or not event.src_path.endswith('.md'):
            return

        # 防止重复触发
        current_time = time.time()
        last_time = self.last_sync_times.get(event.src_path, 0)
        if current_time - last_time < 1:  # 1秒内的重复事件忽略
            return

        self.last_sync_times[event.src_path] = current_time

        logger.info(f"检测到文件修改: {event.src_path}")
        try:
            self.sync_engine.sync_from_obsidian(Path(event.src_path))
        except Exception as e:
            logger.error(f"同步失败: {str(e)}", exc_info=True)

    def on_created(self, event: FileCreatedEvent):
        """新文件创建"""
        if event.is_directory or not event.src_path.endswith('.md'):
            return

        logger.info(f"检测到新文件: {event.src_path}")
        try:
            self.sync_engine.sync_from_obsidian(Path(event.src_path))
        except Exception as e:
            logger.error(f"同步失败: {str(e)}", exc_info=True)

    def on_deleted(self, event: FileDeletedEvent):
        """文件被删除"""
        if event.is_directory or not event.src_path.endswith('.md'):
            return

        logger.info(f"检测到文件删除: {event.src_path}")
        try:
            self.sync_engine.handle_deletion(Path(event.src_path))
        except Exception as e:
            logger.error(f"处理删除失败: {str(e)}", exc_info=True)


class ConflictResolver:
    """
    冲突解决器

    当FieldMind和Obsidian同时修改时，解决冲突
    """

    STRATEGY_FIELDMIND_WINS = "fieldmind_wins"
    STRATEGY_OBSIDIAN_WINS = "obsidian_wins"
    STRATEGY_NEWER_WINS = "newer_wins"
    STRATEGY_MERGE = "merge"

    def __init__(self, strategy: str = STRATEGY_NEWER_WINS):
        self.strategy = strategy

    def resolve(
        self,
        fieldmind_content: str,
        fieldmind_modified: datetime,
        obsidian_content: str,
        obsidian_modified: datetime
    ) -> tuple[str, str]:
        """
        解决冲突

        返回: (最终内容, 解决方式说明)
        """
        if self.strategy == self.STRATEGY_FIELDMIND_WINS:
            return fieldmind_content, "FieldMind版本优先"

        elif self.strategy == self.STRATEGY_OBSIDIAN_WINS:
            return obsidian_content, "Obsidian版本优先"

        elif self.strategy == self.STRATEGY_NEWER_WINS:
            if fieldmind_modified > obsidian_modified:
                return fieldmind_content, "FieldMind版本较新"
            else:
                return obsidian_content, "Obsidian版本较新"

        elif self.strategy == self.STRATEGY_MERGE:
            # 简单的三路合并
            merged = self._three_way_merge(fieldmind_content, obsidian_content)
            return merged, "已合并两个版本"

        return obsidian_content, "默认使用Obsidian版本"

    def _three_way_merge(self, content1: str, content2: str) -> str:
        """
        三路合并策略

        简化版：逐行比较，保留不同的部分
        """
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')

        merged_lines = []
        for i in range(max(len(lines1), len(lines2))):
            line1 = lines1[i] if i < len(lines1) else ""
            line2 = lines2[i] if i < len(lines2) else ""

            if line1 == line2:
                merged_lines.append(line1)
            else:
                # 冲突标记
                merged_lines.append(f"<<<<<<< FieldMind")
                merged_lines.append(line1)
                merged_lines.append("=======")
                merged_lines.append(line2)
                merged_lines.append(">>>>>>> Obsidian")

        return '\n'.join(merged_lines)


class ObsidianSyncEngine:
    """
    Obsidian同步引擎

    核心功能：
    1. 文件监听和自动同步
    2. 双向同步（FieldMind ⟷ Obsidian）
    3. 冲突检测和解决
    4. 增量同步
    """

    def __init__(self, vault_path: Path, db: Session):
        self.vault_path = Path(vault_path)
        self.db = db
        self.data_store = ObsidianDataStore(db)
        self.conflict_resolver = ConflictResolver()
        self.observer: Optional[Observer] = None
        self.is_running = False

        # 确保vault目录存在
        self.vault_path.mkdir(parents=True, exist_ok=True)

    def start_watch(self):
        """开始监听vault变化"""
        if self.is_running:
            logger.warning("同步引擎已在运行")
            return

        self.observer = Observer()
        event_handler = ObsidianVaultWatcher(self)
        self.observer.schedule(event_handler, str(self.vault_path), recursive=True)
        self.observer.start()
        self.is_running = True

        logger.info(f"开始监听Obsidian vault: {self.vault_path}")

    def stop_watch(self):
        """停止监听"""
        if self.observer and self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            logger.info("已停止监听Obsidian vault")

    def sync_from_obsidian(self, file_path: Path):
        """
        从Obsidian同步到FieldMind

        流程：
        1. 读取Markdown文件
        2. 解析内容
        3. 检查数据库中是否存在
        4. 如果存在，检测冲突
        5. 更新或创建记录
        """
        logger.info(f"从Obsidian同步: {file_path}")

        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析Markdown
        note = self.data_store.parse_note(content, str(file_path))

        # 获取文件修改时间
        file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)

        # 计算文件路径相对vault的路径
        relative_path = file_path.relative_to(self.vault_path)

        # 检查数据库中是否存在
        from app.models.obsidian_note import ObsidianNote
        existing = self.db.query(ObsidianNote).filter(
            ObsidianNote.vault_path == str(relative_path)
        ).first()

        if existing:
            # 检测冲突
            if existing.modified_at > file_modified:
                # FieldMind版本较新，可能有冲突
                logger.warning(f"检测到潜在冲突: {file_path}")

                resolved_content, resolution = self.conflict_resolver.resolve(
                    existing.content,
                    existing.modified_at,
                    content,
                    file_modified
                )

                # 更新数据库
                existing.content = resolved_content
                existing.modified_at = datetime.utcnow()
                existing.sync_status = f"冲突已解决: {resolution}"

                # 如果选择了FieldMind版本，需要写回文件
                if resolved_content == existing.content:
                    self._write_to_vault(file_path, resolved_content)
            else:
                # Obsidian版本较新，直接更新
                existing.content = content
                existing.modified_at = datetime.utcnow()
                existing.sync_status = "已从Obsidian同步"
        else:
            # 创建新记录
            new_note = ObsidianNote(
                vault_path=str(relative_path),
                title=note.title,
                content=content,
                frontmatter=note.frontmatter,
                tags=note.tags,
                created_at=file_modified,
                modified_at=file_modified,
                sync_status="已从Obsidian导入"
            )
            self.db.add(new_note)

        self.db.commit()
        logger.info(f"同步完成: {file_path}")

    def sync_to_obsidian(self, note_id: int, note_type: str = 'note'):
        """
        从FieldMind同步到Obsidian

        流程：
        1. 从数据库加载内容
        2. 生成Markdown
        3. 写入vault文件
        4. 更新同步状态
        """
        logger.info(f"同步到Obsidian: {note_type} #{note_id}")

        # 根据类型加载数据
        if note_type == 'knowledge':
            from app.models.sbpack import KnowledgeItem
            item = self.db.query(KnowledgeItem).filter(KnowledgeItem.id == note_id).first()
            if not item:
                logger.error(f"知识点 {note_id} 不存在")
                return

            # 生成Markdown
            markdown = self._generate_knowledge_markdown(item)
            file_path = self.vault_path / "知识库" / f"{self._sanitize_filename(item.title)}.md"

        elif note_type == 'skill':
            from app.models.sbpack import SkillItem
            item = self.db.query(SkillItem).filter(SkillItem.id == note_id).first()
            if not item:
                logger.error(f"技能 {note_id} 不存在")
                return

            # 生成Markdown
            markdown = self._generate_skill_markdown(item)
            file_path = self.vault_path / "技能库" / f"{self._sanitize_filename(item.name)}.md"

        else:
            from app.models.obsidian_note import ObsidianNote
            item = self.db.query(ObsidianNote).filter(ObsidianNote.id == note_id).first()
            if not item:
                logger.error(f"笔记 {note_id} 不存在")
                return

            markdown = item.content
            file_path = self.vault_path / item.vault_path

        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        self._write_to_vault(file_path, markdown)

        logger.info(f"已同步到Obsidian: {file_path}")

    def _write_to_vault(self, file_path: Path, content: str):
        """写入vault文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def handle_deletion(self, file_path: Path):
        """处理文件删除"""
        relative_path = file_path.relative_to(self.vault_path)

        from app.models.obsidian_note import ObsidianNote
        note = self.db.query(ObsidianNote).filter(
            ObsidianNote.vault_path == str(relative_path)
        ).first()

        if note:
            # 标记为已删除，而不是直接删除
            note.sync_status = "已从Obsidian删除"
            note.deleted_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"已标记删除: {relative_path}")

    def full_sync(self, direction: str = 'bidirectional'):
        """
        完整同步

        direction: 'to_obsidian', 'from_obsidian', 'bidirectional'
        """
        logger.info(f"开始完整同步，方向: {direction}")

        if direction in ['from_obsidian', 'bidirectional']:
            # 扫描vault中的所有Markdown文件
            for md_file in self.vault_path.rglob('*.md'):
                try:
                    self.sync_from_obsidian(md_file)
                except Exception as e:
                    logger.error(f"同步失败: {md_file}, 错误: {str(e)}")

        if direction in ['to_obsidian', 'bidirectional']:
            # 同步所有知识点
            from app.models.sbpack import KnowledgeItem
            knowledge_items = self.db.query(KnowledgeItem).all()
            for item in knowledge_items:
                try:
                    self.sync_to_obsidian(item.id, 'knowledge')
                except Exception as e:
                    logger.error(f"同步知识点失败: {item.id}, 错误: {str(e)}")

            # 同步所有技能
            from app.models.sbpack import SkillItem
            skill_items = self.db.query(SkillItem).all()
            for item in skill_items:
                try:
                    self.sync_to_obsidian(item.id, 'skill')
                except Exception as e:
                    logger.error(f"同步技能失败: {item.id}, 错误: {str(e)}")

        logger.info("完整同步完成")

    def _generate_knowledge_markdown(self, item) -> str:
        """生成知识点Markdown"""
        from app.services.obsidian_exporter import ObsidianExporter
        exporter = ObsidianExporter(self.db)
        return exporter._generate_knowledge_markdown(item)

    def _generate_skill_markdown(self, item) -> str:
        """生成技能Markdown"""
        from app.services.obsidian_exporter import ObsidianExporter
        exporter = ObsidianExporter(self.db)
        return exporter._generate_skill_markdown(item)

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名"""
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in illegal_chars:
            name = name.replace(char, '_')
        return name[:100]  # 限制长度
