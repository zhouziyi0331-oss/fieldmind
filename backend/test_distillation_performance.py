"""
蒸馏功能 Phase 4 - 性能测试
测试大数据量下的蒸馏性能
"""
import sys
sys.path.insert(0, 'src')

import time
import psutil
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from app.core.database import Base
from app.models.document_chunk import DocumentChunk
from app.models.entity import Entity, EntityRelation
from app.models.timeline import TimelineEvent
from app.services.distillation_engine import DistillationEngine

# 测试配置
TEST_DATABASE_URL = "sqlite:///./test_performance.db"
CHUNK_SIZES = [10, 50, 100, 500, 1000]  # 不同的数据规模


class PerformanceTest:
    """性能测试类"""

    def __init__(self):
        self.engine = create_engine(TEST_DATABASE_URL)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.results = []

    def get_memory_usage(self):
        """获取当前内存使用量(MB)"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def create_test_data(self, num_chunks, num_entities=10, num_events=5):
        """创建测试数据"""
        print(f"📝 创建测试数据: {num_chunks} chunks, {num_entities} entities, {num_events} events")

        session = self.SessionLocal()

        try:
            # 清空现有数据
            session.query(DocumentChunk).delete()
            session.query(Entity).delete()
            session.query(EntityRelation).delete()
            session.query(TimelineEvent).delete()
            session.commit()

            # 创建chunks
            sample_texts = [
                "李明表示，土地改革进展顺利，农民收入提高了30%。",
                "王教授指出，非常紧急！必须立即保护传统技艺。",
                "张华的成功案例值得推广：通过创新技术实现收入翻倍。",
                "调研发现，年轻人流失问题需要立即解决。建议建立返乡创业扶持政策。",
                "李明和王教授合作推动了文化旅游项目，张华负责茶叶销售。",
            ]

            sample_entities = [
                {"name": "李明", "type": "PERSON"},
                {"name": "王教授", "type": "PERSON"},
                {"name": "张华", "type": "PERSON"},
                {"name": "土地改革", "type": "CONCEPT"},
            ]

            sample_tags = ["土地改革", "农民收入", "文化保护", "创新", "政策建议"]
            sample_speakers = ["李明", "王教授", "张华", None, None]

            chunks = []
            for i in range(num_chunks):
                text = sample_texts[i % len(sample_texts)]
                speaker = sample_speakers[i % len(sample_speakers)]
                entities = [sample_entities[i % len(sample_entities)]]
                tags = [sample_tags[i % len(sample_tags)]]

                chunk = DocumentChunk(
                    id=i + 1,
                    chunk_id=f"chunk_{i+1}",
                    document_id=1,
                    project_id=1,
                    chunk_index=i,
                    text=text,
                    legacy_chunk_text=text,
                    text_length=len(text),
                    legacy_chunk_size=len(text),
                    speaker=speaker,
                    key_entities=json.dumps(entities),
                    domain_tags=json.dumps(tags),
                    created_at=datetime.utcnow()
                )
                chunks.append(chunk)

            session.bulk_save_objects(chunks)

            # 创建entities
            entities = []
            for i in range(num_entities):
                entity = Entity(
                    id=f"entity_{i+1}",
                    text=f"实体{i+1}",
                    type="PERSON" if i % 2 == 0 else "CONCEPT",
                    legacy_name=f"实体{i+1}",
                    legacy_entity_type="PERSON" if i % 2 == 0 else "CONCEPT"
                )
                entities.append(entity)

            session.bulk_save_objects(entities)

            # 创建relations
            relations = []
            for i in range(min(num_entities - 1, 10)):
                relation = EntityRelation(
                    source_entity_id=f"entity_{i+1}",
                    target_entity_id=f"entity_{i+2}",
                    relation_type=["合作", "领导", "指导"][i % 3],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                relations.append(relation)

            session.bulk_save_objects(relations)

            # 创建events
            events = []
            for i in range(num_events):
                event = TimelineEvent(
                    id=f"event_{i+1}",
                    project_id=1,
                    title=f"事件{i+1}",
                    date=datetime(2024, (i % 12) + 1, 1),
                    category=["政策", "会议", "经济"][i % 3],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                events.append(event)

            session.bulk_save_objects(events)

            session.commit()
            print(f"✅ 测试数据创建完成")

        except Exception as e:
            print(f"❌ 创建测试数据失败: {e}")
            session.rollback()
        finally:
            session.close()

    def test_distillation_performance(self, num_chunks):
        """测试蒸馏性能"""
        print(f"\n{'='*60}")
        print(f"🧪 测试规模: {num_chunks} chunks")
        print(f"{'='*60}")

        session = self.SessionLocal()
        engine = DistillationEngine(session)

        try:
            # 记录初始内存
            mem_before = self.get_memory_usage()

            # 执行蒸馏
            start_time = time.time()
            result = engine.distill_project(project_id=1)
            end_time = time.time()

            # 记录结束内存
            mem_after = self.get_memory_usage()

            # 计算指标
            elapsed_time = end_time - start_time
            mem_used = mem_after - mem_before
            throughput = num_chunks / elapsed_time if elapsed_time > 0 else 0

            # 记录结果
            test_result = {
                "num_chunks": num_chunks,
                "elapsed_time": elapsed_time,
                "memory_used_mb": mem_used,
                "throughput_chunks_per_sec": throughput,
                "total_units": result.get("total_units", 0),
                "breakdown": result.get("breakdown", {})
            }

            self.results.append(test_result)

            # 打印结果
            print(f"\n📊 性能指标:")
            print(f"  ⏱️  耗时: {elapsed_time:.2f} 秒")
            print(f"  💾 内存: {mem_used:.2f} MB")
            print(f"  🚀 吞吐: {throughput:.2f} chunks/秒")
            print(f"  📦 产出: {result.get('total_units', 0)} 个知识单元")

            # 详细breakdown
            if result.get("breakdown"):
                print(f"\n  📋 知识单元分布:")
                for key, count in result["breakdown"].items():
                    print(f"    - {key}: {count}")

            # 性能评估
            print(f"\n  🎯 性能评估:")
            if elapsed_time < 5:
                print(f"    ✅ 极快 (< 5秒)")
            elif elapsed_time < 10:
                print(f"    ✅ 快速 (5-10秒)")
            elif elapsed_time < 30:
                print(f"    ⚠️  中等 (10-30秒)")
            else:
                print(f"    ❌ 较慢 (> 30秒)")

            if mem_used < 50:
                print(f"    ✅ 内存占用低 (< 50MB)")
            elif mem_used < 100:
                print(f"    ⚠️  内存占用中等 (50-100MB)")
            else:
                print(f"    ❌ 内存占用高 (> 100MB)")

            return test_result

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            session.close()

    def test_query_performance(self, num_chunks):
        """测试查询性能"""
        print(f"\n  🔍 查询性能测试:")

        session = self.SessionLocal()
        engine = DistillationEngine(session)

        try:
            # 测试获取所有单元
            start = time.time()
            all_units = engine.get_distilled_units(project_id=1)
            time_all = time.time() - start

            print(f"    - 查询全部: {time_all:.3f}秒 ({len(all_units)} 个)")

            # 测试按类型查询
            start = time.time()
            insights = engine.get_distilled_units(project_id=1, unit_type="insight")
            time_filtered = time.time() - start

            print(f"    - 类型筛选: {time_filtered:.3f}秒 ({len(insights)} 个)")

            # 测试溯源查询
            if all_units:
                start = time.time()
                sources = engine.get_unit_sources(all_units[0].id)
                time_sources = time.time() - start

                print(f"    - 溯源查询: {time_sources:.3f}秒 ({len(sources)} 个)")

            # 评估
            if time_all < 0.1 and time_filtered < 0.1:
                print(f"    ✅ 查询性能优秀")
            elif time_all < 0.5:
                print(f"    ⚠️  查询性能良好")
            else:
                print(f"    ❌ 查询性能需优化")

        except Exception as e:
            print(f"    ❌ 查询测试失败: {e}")

        finally:
            session.close()

    def run_all_tests(self):
        """运行所有性能测试"""
        print("\n" + "="*60)
        print("⚡ Phase 4 性能测试 - 大数据量测试")
        print("="*60 + "\n")

        print(f"📌 测试规模: {CHUNK_SIZES}")
        print(f"📌 数据库: {TEST_DATABASE_URL}")
        print(f"📌 初始内存: {self.get_memory_usage():.2f} MB\n")

        for num_chunks in CHUNK_SIZES:
            # 创建测试数据
            self.create_test_data(
                num_chunks=num_chunks,
                num_entities=min(10 + num_chunks // 100, 50),
                num_events=min(5 + num_chunks // 200, 20)
            )

            # 测试蒸馏性能
            result = self.test_distillation_performance(num_chunks)

            # 测试查询性能
            if result:
                self.test_query_performance(num_chunks)

            print()

        # 打印总结
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📊 性能测试总结")
        print("="*60 + "\n")

        print("| Chunks | 耗时(秒) | 内存(MB) | 吞吐(c/s) | 知识单元 |")
        print("|--------|----------|----------|-----------|----------|")

        for result in self.results:
            print(f"| {result['num_chunks']:6d} | "
                  f"{result['elapsed_time']:8.2f} | "
                  f"{result['memory_used_mb']:8.2f} | "
                  f"{result['throughput_chunks_per_sec']:9.1f} | "
                  f"{result['total_units']:8d} |")

        print()

        # 性能趋势分析
        if len(self.results) > 1:
            print("📈 性能趋势:")

            # 计算时间增长率
            time_growth = []
            for i in range(1, len(self.results)):
                prev = self.results[i-1]
                curr = self.results[i]
                chunk_ratio = curr['num_chunks'] / prev['num_chunks']
                time_ratio = curr['elapsed_time'] / prev['elapsed_time']
                time_growth.append(time_ratio / chunk_ratio)

            avg_growth = sum(time_growth) / len(time_growth)

            print(f"  - 时间复杂度: {'O(n)' if avg_growth < 1.5 else 'O(n²)' if avg_growth < 3 else 'O(n³)'}")
            print(f"  - 平均增长率: {avg_growth:.2f}x")

            # 内存分析
            max_mem = max(r['memory_used_mb'] for r in self.results)
            print(f"  - 最大内存: {max_mem:.2f} MB")

            # 吞吐量分析
            avg_throughput = sum(r['throughput_chunks_per_sec'] for r in self.results) / len(self.results)
            print(f"  - 平均吞吐: {avg_throughput:.1f} chunks/秒")

        print()

        # 性能建议
        print("💡 优化建议:")

        # 检查最大规模的性能
        if self.results:
            largest_test = self.results[-1]

            if largest_test['elapsed_time'] > 60:
                print("  ⚠️  大数据量处理较慢，建议:")
                print("     - 使用批处理模式")
                print("     - 添加进度条反馈")
                print("     - 考虑后台任务队列")

            if largest_test['memory_used_mb'] > 500:
                print("  ⚠️  内存占用较高，建议:")
                print("     - 使用流式处理")
                print("     - 分批加载数据")
                print("     - 及时释放内存")

            if largest_test['throughput_chunks_per_sec'] < 10:
                print("  ⚠️  吞吐量较低，建议:")
                print("     - 优化算法复杂度")
                print("     - 减少数据库查询")
                print("     - 使用缓存机制")

            if (largest_test['elapsed_time'] < 30 and
                largest_test['memory_used_mb'] < 200 and
                largest_test['throughput_chunks_per_sec'] > 10):
                print("  ✅ 性能表现优秀，无需优化")

        print("\n" + "="*60 + "\n")


def main():
    """主函数"""
    tester = PerformanceTest()
    tester.run_all_tests()

    # 清理测试数据库
    if os.path.exists("test_performance.db"):
        print("🗑️  清理测试数据库...")
        os.remove("test_performance.db")
        print("✅ 清理完成\n")


if __name__ == "__main__":
    main()
