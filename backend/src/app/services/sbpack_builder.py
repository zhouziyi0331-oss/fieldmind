"""
SBPACK 2.0构建器

将双轨内容（知识轨 + 技能轨）打包成.sbpack文件
遵循规范：05-SBPACK-2.0封装与验收清单.md
"""
import json
import hashlib
import zipfile
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.models.sbpack import SBPACKPackage, KnowledgeItem, SkillItem, KnowledgeSkillRelation

logger = logging.getLogger(__name__)


class SBPACKBuilder:
    """
    SBPACK 2.0构建器

    SBPACK结构：
    .sbpack (实际上是ZIP文件)
    ├── manifest.json          # 包清单
    ├── payload/
    │   ├── knowledge/         # 知识轨
    │   │   ├── index.json
    │   │   └── items/
    │   │       ├── concept_001.json
    │   │       └── ...
    │   ├── skills/            # 技能轨
    │   │   ├── index.json
    │   │   └── items/
    │   │       ├── skill_001/
    │   │       │   ├── canonical/
    │   │       │   │   └── SKILL.md
    │   │       │   ├── test-prompts.json
    │   │       │   └── metadata.json
    │   │       └── ...
    │   └── relations/         # 关系
    │       └── index.json
    ├── provenance/            # 溯源信息
    │   ├── source.json
    │   ├── producers.json
    │   └── freezes.json
    └── audit/                 # 审计信息
        ├── verification.json
        └── production-audit.json
    """

    def __init__(self, db: Session, output_dir: str = "./output"):
        self.db = db
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def build(self, package_id: int) -> Dict[str, Any]:
        """
        构建SBPACK文件

        参数:
            package_id: SBPACK包ID

        返回:
            构建结果
        """
        logger.info(f"开始构建SBPACK，package_id={package_id}")

        # 1. 加载包信息
        package = self.db.query(SBPACKPackage).filter(
            SBPACKPackage.id == package_id
        ).first()

        if not package:
            raise ValueError(f"Package {package_id} not found")

        # 2. 检查双轨是否冻结
        if not package.knowledge_frozen:
            raise ValueError("知识轨尚未冻结，无法构建SBPACK")

        if not package.skill_frozen:
            raise ValueError("技能轨尚未冻结，无法构建SBPACK")

        # 3. 创建临时构建目录
        build_dir = self.output_dir / f"sbpack_build_{package_id}"
        build_dir.mkdir(exist_ok=True)

        try:
            # 4. 构建各个部分
            manifest = self._build_manifest(package)
            self._build_knowledge_track(package, build_dir)
            self._build_skill_track(package, build_dir)
            self._build_relations(package, build_dir)
            self._build_provenance(package, build_dir)
            self._build_audit(package, build_dir)

            # 5. 写入manifest
            manifest_path = build_dir / "manifest.json"
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

            # 6. 打包成.sbpack（ZIP格式）
            sbpack_path = self._create_sbpack_file(package, build_dir)

            # 7. 计算文件哈希
            sbpack_hash = self._calculate_file_hash(sbpack_path)

            # 8. 更新包状态
            package.is_built = True
            package.build_path = str(sbpack_path)
            self.db.commit()

            logger.info(f"SBPACK构建完成: {sbpack_path}")

            return {
                "success": True,
                "package_id": package_id,
                "sbpack_path": str(sbpack_path),
                "sbpack_hash": sbpack_hash,
                "knowledge_count": package.knowledge_count,
                "skill_count": package.skill_count,
                "relation_count": package.relation_count
            }

        except Exception as e:
            logger.error(f"构建SBPACK失败: {str(e)}", exc_info=True)
            raise

        finally:
            # 清理临时目录（可选，保留用于调试）
            # shutil.rmtree(build_dir)
            pass

    def _build_manifest(self, package: SBPACKPackage) -> Dict[str, Any]:
        """构建manifest.json"""
        return {
            "version": "2.0.0",
            "protocol": "SBPACK",
            "protocolVersion": "2.0.0",
            "packageId": package.id,
            "packageName": package.package_name,
            "createdAt": datetime.utcnow().isoformat(),
            "source": {
                "title": package.source_title,
                "author": package.source_author,
                "type": package.source_type,
                "url": package.source_url,
                "sha256": package.source_sha256
            },
            "content": {
                "knowledge": {
                    "count": package.knowledge_count,
                    "frozen": package.knowledge_frozen,
                    "freezeHash": package.knowledge_freeze_hash
                },
                "skills": {
                    "count": package.skill_count,
                    "frozen": package.skill_frozen,
                    "freezeHash": package.skill_freeze_hash
                },
                "relations": {
                    "count": package.relation_count
                }
            },
            "metadata": package.extra_metadata or {}
        }

    def _build_knowledge_track(self, package: SBPACKPackage, build_dir: Path):
        """构建知识轨"""
        knowledge_dir = build_dir / "payload" / "knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)

        items_dir = knowledge_dir / "items"
        items_dir.mkdir(exist_ok=True)

        # 加载所有知识点
        knowledge_items = self.db.query(KnowledgeItem).filter(
            KnowledgeItem.package_id == package.id
        ).all()

        index = {
            "count": len(knowledge_items),
            "items": []
        }

        for item in knowledge_items:
            # 创建知识点JSON
            item_data = {
                "knowledgeId": item.knowledge_id,
                "title": item.title,
                "type": item.knowledge_type,
                "statement": item.statement,
                "explanation": item.explanation,
                "whyMatters": item.why_matters,
                "scope": item.scope,
                "conditions": item.conditions,
                "boundaries": item.boundaries,
                "counterexamples": item.counterexamples,
                "evidenceRefs": item.evidence_refs,
                "evidenceQuotes": item.evidence_quotes,
                "sourceCertainty": item.source_certainty,
                "extractionCertainty": item.extraction_certainty,
                "externalVerification": item.external_verification,
                "attribution": item.attribution,
                "inferenceType": item.inference_type,
                "contentHash": item.content_hash
            }

            # 写入文件
            item_filename = f"{item.knowledge_id}.json"
            item_path = items_dir / item_filename

            with open(item_path, 'w', encoding='utf-8') as f:
                json.dump(item_data, f, ensure_ascii=False, indent=2)

            # 添加到索引
            index["items"].append({
                "id": item.knowledge_id,
                "type": item.knowledge_type,
                "title": item.title,
                "file": f"items/{item_filename}"
            })

        # 写入索引
        index_path = knowledge_dir / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        logger.info(f"知识轨构建完成: {len(knowledge_items)} 个知识点")

    def _build_skill_track(self, package: SBPACKPackage, build_dir: Path):
        """构建技能轨"""
        skills_dir = build_dir / "payload" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        items_dir = skills_dir / "items"
        items_dir.mkdir(exist_ok=True)

        # 加载所有技能
        skill_items = self.db.query(SkillItem).filter(
            SkillItem.package_id == package.id
        ).all()

        index = {
            "count": len(skill_items),
            "items": []
        }

        for item in skill_items:
            # 创建技能目录
            skill_dir = items_dir / item.skill_id
            skill_dir.mkdir(exist_ok=True)

            canonical_dir = skill_dir / "canonical"
            canonical_dir.mkdir(exist_ok=True)

            # 1. 写入canonical/SKILL.md（字节保真）
            if item.canonical_content:
                skill_md_path = canonical_dir / "SKILL.md"
                with open(skill_md_path, 'w', encoding='utf-8') as f:
                    f.write(item.canonical_content)

            # 2. 写入metadata.json
            metadata = {
                "skillId": item.skill_id,
                "name": item.name,
                "displayName": item.display_name,
                "description": item.description,
                "rationale": item.rationale,
                "interpretation": item.interpretation,
                "applicationOriginal": item.application_original,
                "applicationFuture": item.application_future,
                "execution": item.execution,
                "boundaries": item.boundaries,
                "cangjieVersion": item.cangjie_version,
                "cangjieCommit": item.cangjie_commit,
                "canonicalSha256": item.canonical_sha256,
                "validation": {
                    "v1Passed": item.v1_passed,
                    "v2Passed": item.v2_passed,
                    "v3Passed": item.v3_passed
                }
            }

            metadata_path = skill_dir / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 3. 写入test-prompts.json
            if item.pressure_tests:
                tests_path = skill_dir / "test-prompts.json"
                with open(tests_path, 'w', encoding='utf-8') as f:
                    json.dump(item.pressure_tests, f, ensure_ascii=False, indent=2)

            # 添加到索引
            index["items"].append({
                "id": item.skill_id,
                "name": item.name,
                "description": item.description[:100],
                "directory": f"items/{item.skill_id}"
            })

        # 写入索引
        index_path = skills_dir / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        logger.info(f"技能轨构建完成: {len(skill_items)} 个技能")

    def _build_relations(self, package: SBPACKPackage, build_dir: Path):
        """构建关系"""
        relations_dir = build_dir / "payload" / "relations"
        relations_dir.mkdir(parents=True, exist_ok=True)

        # 加载所有关系
        relations = self.db.query(KnowledgeSkillRelation).filter(
            KnowledgeSkillRelation.package_id == package.id
        ).all()

        relations_data = {
            "count": len(relations),
            "relations": []
        }

        for rel in relations:
            relations_data["relations"].append({
                "knowledgeId": rel.knowledge_id,
                "skillId": rel.skill_id,
                "relationType": rel.relation_type,
                "strength": rel.strength,
                "evidence": rel.evidence
            })

        # 写入索引
        index_path = relations_dir / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(relations_data, f, ensure_ascii=False, indent=2)

        logger.info(f"关系构建完成: {len(relations)} 个关系")

    def _build_provenance(self, package: SBPACKPackage, build_dir: Path):
        """构建溯源信息"""
        provenance_dir = build_dir / "provenance"
        provenance_dir.mkdir(parents=True, exist_ok=True)

        # 1. 来源信息
        source_data = {
            "title": package.source_title,
            "author": package.source_author,
            "type": package.source_type,
            "url": package.source_url,
            "sha256": package.source_sha256
        }

        source_path = provenance_dir / "source.json"
        with open(source_path, 'w', encoding='utf-8') as f:
            json.dump(source_data, f, ensure_ascii=False, indent=2)

        # 2. 生产者快照
        from app.models.sbpack import ProducerSnapshot
        snapshots = self.db.query(ProducerSnapshot).filter(
            ProducerSnapshot.package_id == package.id
        ).all()

        producers_data = {
            "snapshots": [
                {
                    "role": s.role,
                    "modelName": s.model_name,
                    "modelVersion": s.model_version,
                    "runId": s.run_id,
                    "snapshotHash": s.snapshot_hash,
                    "createdAt": s.created_at.isoformat()
                }
                for s in snapshots
            ]
        }

        producers_path = provenance_dir / "producers.json"
        with open(producers_path, 'w', encoding='utf-8') as f:
            json.dump(producers_data, f, ensure_ascii=False, indent=2)

        # 3. 冻结信息
        freezes_data = {
            "knowledge": {
                "frozen": package.knowledge_frozen,
                "frozenAt": package.knowledge_frozen_at.isoformat() if package.knowledge_frozen_at else None,
                "freezeHash": package.knowledge_freeze_hash
            },
            "skill": {
                "frozen": package.skill_frozen,
                "frozenAt": package.skill_frozen_at.isoformat() if package.skill_frozen_at else None,
                "freezeHash": package.skill_freeze_hash
            }
        }

        freezes_path = provenance_dir / "freezes.json"
        with open(freezes_path, 'w', encoding='utf-8') as f:
            json.dump(freezes_data, f, ensure_ascii=False, indent=2)

    def _build_audit(self, package: SBPACKPackage, build_dir: Path):
        """构建审计信息"""
        audit_dir = build_dir / "audit"
        audit_dir.mkdir(parents=True, exist_ok=True)

        # 验收信息
        verification_data = {
            "status": package.verification_status,
            "report": package.verification_report,
            "verifiedAt": datetime.utcnow().isoformat()
        }

        verification_path = audit_dir / "verification.json"
        with open(verification_path, 'w', encoding='utf-8') as f:
            json.dump(verification_data, f, ensure_ascii=False, indent=2)

    def _create_sbpack_file(self, package: SBPACKPackage, build_dir: Path) -> Path:
        """创建.sbpack文件（ZIP格式）"""
        sbpack_filename = f"{package.package_name}.sbpack"
        sbpack_path = self.output_dir / sbpack_filename

        with zipfile.ZipFile(sbpack_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(build_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(build_dir)
                    zipf.write(file_path, arcname)

        return sbpack_path

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件SHA-256"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
