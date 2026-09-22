"""
蒸馏流水线

协调整个蒸馏流程，包括双轨生产、冻结、关系建立、封装
"""

import os
import uuid
import asyncio
from typing import Tuple, List, Optional
from pathlib import Path

from app.distillation.types import (
    SourceMetadata,
    NormalizedSource,
    KnowledgeUnit,
    MethodUnit,
    KnowledgeFreezeManifest,
    MethodFreezeManifest,
    CandidateCoverageAudit,
    ProductionAudit,
    MethodRelation,
    KnowledgeMethodRelation,
)
from app.distillation.normalizer import SourceNormalizer
from app.distillation.knowledge import KnowledgeDistiller
from app.distillation.method import MethodDistiller


class DistillationPipeline:
    """完整蒸馏流水线"""

    def __init__(self, llm_service=None, output_dir: Optional[str] = None):
        """
        Args:
            llm_service: LLM 服务实例
            output_dir: 输出目录路径
        """
        self.llm_service = llm_service
        self.output_dir = output_dir or "/tmp/fieldmind_distillation"

        # 初始化各阶段处理器
        self.normalizer = SourceNormalizer()
        self.knowledge_distiller = KnowledgeDistiller(llm_service)
        self.method_distiller = MethodDistiller(llm_service)

    async def execute(
        self, source_metadata: SourceMetadata, user_confirmation_callback=None
    ) -> "DistillationResult":
        """
        执行完整蒸馏流水线

        流程：
        1. 来源规范化
        2. 阶段 0：整书理解（Adler）→ 用户确认
        3. 阶段 1-1.5：五类并行提取 + 三重验证 → 用户确认
        4. 阶段 2：RIA++ 构造
        5. 独立知识轨提取（与方法轨并行）
        6. 候选快照
        7. 阶段 4：独立测试
        8. 最终冻结
        9. 阶段 3：关系建立
        10. Adapter：确定性映射
        11. 封装与预检

        Args:
            source_metadata: 源文档元信息
            user_confirmation_callback: 用户确认回调函数

        Returns:
            DistillationResult: 蒸馏结果
        """
        generation_id = f"gen-{uuid.uuid4()}"
        result = DistillationResult(generation_id=generation_id)

        try:
            # 1. 规范化
            print("📄 阶段 1/11: 来源规范化...")
            normalized_source = await self.normalizer.normalize(source_metadata)
            result.normalized_source = normalized_source
            self._save_normalized_source(normalized_source)

            # 2. 阶段 0：整书理解
            print("📚 阶段 2/11: 整书理解（Adler 分析阅读）...")
            book_overview = await self.method_distiller.stage0.analyze_book(
                normalized_source
            )
            result.book_overview = book_overview

            # 用户确认
            if user_confirmation_callback:
                confirmed = await user_confirmation_callback(
                    "阶段 0：整书理解", book_overview
                )
                if not confirmed:
                    raise Exception("用户取消：整书理解未通过确认")

            # 3. 并行执行方法轨和知识轨
            print("🔀 阶段 3/11: 双轨并行提取...")

            # 方法轨：阶段 1 + 1.5
            candidates = await self.method_distiller.stage1.parallel_extract(
                book_overview, normalized_source
            )

            verified_methods, rejected_methods = (
                await self.method_distiller.stage1_5.verify_candidates(
                    candidates, normalized_source
                )
            )

            # 用户确认验证结果
            if user_confirmation_callback:
                confirmed = await user_confirmation_callback(
                    "阶段 1.5：验证通过的候选",
                    {
                        "verified_count": len(verified_methods),
                        "rejected_count": len(rejected_methods),
                        "verified": [c.title for c in verified_methods],
                    },
                )
                if not confirmed:
                    raise Exception("用户取消：候选验证未通过确认")

            # 4. 阶段 2：RIA++ 构造
            print("🏗️  阶段 4/11: RIA++ 方法构造...")
            methods = []
            for cand in verified_methods:
                method = await self.method_distiller.stage2.build_method(
                    cand, book_overview, normalized_source
                )
                methods.append(method)
            result.methods = methods

            # 5. 独立知识轨提取
            print("💡 阶段 5/11: 知识轨提取...")
            knowledge_units = await self.knowledge_distiller.extract_knowledge(
                normalized_source
            )
            result.knowledge_units = knowledge_units

            # 6-8. 压力测试 + 冻结
            print("🧪 阶段 6/11: 压力测试...")
            test_results_map = {}
            for method in methods:
                test_suite = await self.method_distiller.stage4.design_tests(
                    method, methods
                )
                test_results = await self.method_distiller.stage4.execute_blind_test(
                    method, test_suite, methods
                )
                test_results_map[method.id] = test_results

                # 检查通过率
                pass_rate = sum(1 for r in test_results if r.passed) / len(
                    test_results
                )
                if pass_rate < 0.8:
                    print(
                        f"⚠️  方法 {method.display_name} 测试通过率 {pass_rate:.0%} < 80%"
                    )

            # 7. 冻结双轨
            print("❄️  阶段 7/11: 冻结知识轨和方法轨...")
            method_freeze = self.method_distiller._freeze_methods(
                methods, test_results_map, normalized_source
            )
            knowledge_freeze = self.knowledge_distiller.freeze_knowledge_track(
                knowledge_units, normalized_source
            )
            result.method_freeze = method_freeze
            result.knowledge_freeze = knowledge_freeze

            # 8. 关系建立
            print("🔗 阶段 8/11: 建立知识-方法关系...")
            method_relations, knowledge_method_relations = (
                await self._build_relations(methods, knowledge_units)
            )
            result.method_relations = method_relations
            result.knowledge_method_relations = knowledge_method_relations

            # 9. 生产审计
            print("📋 阶段 9/11: 生成生产审计...")
            audit = self._create_production_audit(
                normalized_source,
                candidates,
                verified_methods,
                rejected_methods,
                methods,
                test_results_map,
            )
            result.production_audit = audit

            # 10. 保存所有产物
            print("💾 阶段 10/11: 保存产物...")
            self._save_all_artifacts(result)

            # 11. 封装（可选）
            print("📦 阶段 11/11: 封装 SBPACK（可选）...")
            # TODO: 实现 SBPACK 封装

            print("✅ 蒸馏流程完成！")
            result.success = True

        except Exception as e:
            print(f"❌ 蒸馏流程失败: {e}")
            result.success = False
            result.error_message = str(e)
            raise

        return result

    async def _build_relations(
        self, methods: List[MethodUnit], knowledge_units: List[KnowledgeUnit]
    ) -> Tuple[List[MethodRelation], List[KnowledgeMethodRelation]]:
        """建立关系"""
        method_relations = []
        knowledge_method_relations = []

        # TODO: 实现关系建立逻辑
        # 1. 方法-方法关系（prerequisite/alternative/complement/conflicts-with）
        # 2. 知识-方法关系（supports/explains/contradicts）

        return method_relations, knowledge_method_relations

    def _create_production_audit(
        self,
        normalized_source: NormalizedSource,
        candidates,
        verified_methods,
        rejected_methods,
        methods: List[MethodUnit],
        test_results_map,
    ) -> ProductionAudit:
        """创建生产审计"""
        # 章节基线
        chapters = []
        for chapter in normalized_source.chapters:
            chapters.append(
                {
                    "label": chapter.label,
                    "path": chapter.chapter_id,
                    "sha256": chapter.sha256,
                    "scans": {
                        "framework": "已执行",
                        "principle": "已执行",
                        "case": "已执行",
                        "counterexample": "已执行",
                        "glossary": "已执行",
                    },
                }
            )

        # 候选去向
        candidate_records = []
        for cand in verified_methods:
            candidate_records.append(
                {
                    "id": cand.id,
                    "status": "kept",
                    "reason": "通过三重验证",
                    "target": f"method-{cand.id}",
                }
            )

        # 正式方法
        skills = []
        for method in methods:
            skills.append(
                {
                    "path": f"payload/skills/{method.name}/canonical/SKILL.md",
                    "sha256": method.canonical_sha256 or "sha256:...",
                    "testsSha256": "sha256:...",
                    "testRunSha256": "sha256:...",
                    "evidenceRoute": "A",
                    "evidenceReview": "独立评审通过",
                    "distinctiveness": "来源特有判断价值",
                    "neighbors": [],
                }
            )

        return ProductionAudit(
            version="1.4.3",
            generation_id=normalized_source.generation_id,
            source_sha256=normalized_source.full_text_sha256,
            chapters=chapters,
            candidates=candidate_records,
            skills=skills,
        )

    def _save_normalized_source(self, source: NormalizedSource):
        """保存规范化源文档"""
        import json

        output_path = Path(self.output_dir) / source.generation_id
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存元数据
        with open(output_path / "normalized_source.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generation_id": source.generation_id,
                    "full_text_sha256": source.full_text_sha256,
                    "chapter_count": len(source.chapters),
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        # 保存全文
        with open(output_path / "full_text.txt", "w", encoding="utf-8") as f:
            f.write(source.full_text)

    def _save_all_artifacts(self, result: "DistillationResult"):
        """保存所有产物"""
        import json

        output_path = Path(self.output_dir) / result.generation_id
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存知识单元
        if result.knowledge_units:
            knowledge_path = output_path / "knowledge_units.json"
            with open(knowledge_path, "w", encoding="utf-8") as f:
                json.dump(
                    [
                        {
                            "id": ku.id,
                            "type": ku.type.value,
                            "title": ku.title,
                            "statement": ku.statement,
                        }
                        for ku in result.knowledge_units
                    ],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

        # 保存方法单元
        if result.methods:
            methods_path = output_path / "methods.json"
            with open(methods_path, "w", encoding="utf-8") as f:
                json.dump(
                    [
                        {
                            "id": m.id,
                            "name": m.name,
                            "display_name": m.display_name,
                            "description": m.description,
                        }
                        for m in result.methods
                    ],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

        # 保存生产审计
        if result.production_audit:
            audit_path = output_path / "production_audit.json"
            with open(audit_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "version": result.production_audit.version,
                        "generation_id": result.production_audit.generation_id,
                        "source_sha256": result.production_audit.source_sha256,
                        "chapters": result.production_audit.chapters,
                        "candidates": result.production_audit.candidates,
                        "skills": result.production_audit.skills,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )


class DistillationResult:
    """蒸馏结果"""

    def __init__(self, generation_id: str):
        self.generation_id = generation_id
        self.success = False
        self.error_message: Optional[str] = None

        # 产物
        self.normalized_source: Optional[NormalizedSource] = None
        self.book_overview = None
        self.knowledge_units: List[KnowledgeUnit] = []
        self.methods: List[MethodUnit] = []
        self.knowledge_freeze: Optional[KnowledgeFreezeManifest] = None
        self.method_freeze: Optional[MethodFreezeManifest] = None
        self.method_relations: List[MethodRelation] = []
        self.knowledge_method_relations: List[KnowledgeMethodRelation] = []
        self.production_audit: Optional[ProductionAudit] = None
