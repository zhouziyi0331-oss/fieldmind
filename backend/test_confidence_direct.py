#!/usr/bin/env python3
"""
直接测试置信度计算逻辑
"""
import sys
import os
sys.path.insert(0, 'src')

from app.services.agents.knowledge_agent import Relation, Entity, KnowledgeAgent

# 创建测试实体
entities = [
    Entity(
        实体ID='e1',
        实体名称='张三',
        实体类型='人物',
        提及次数=10,
        出现文档=['doc1'],
        上下文片段=['张三是老师'],
        关联实体=[],
        首次出现时间戳=0.0
    ),
    Entity(
        实体ID='e2',
        实体名称='李四',
        实体类型='人物',
        提及次数=3,
        出现文档=['doc1'],
        上下文片段=['李四是学生'],
        关联实体=[],
        首次出现时间戳=0.0
    ),
    Entity(
        实体ID='e3',
        实体名称='北京',
        实体类型='地名',
        提及次数=5,
        出现文档=['doc1'],
        上下文片段=['在北京'],
        关联实体=[],
        首次出现时间戳=0.0
    )
]

agent = KnowledgeAgent()

print("="*60)
print("置信度计算测试")
print("="*60)

test_cases = [
    {
        "name": "理想情况 - 完整句子，高频实体，LLM提取",
        "relation": Relation(
            关系ID='r1',
            主体='张三',
            关系类型='教授',
            客体='李四',
            上下文='张三老师在教室里耐心地教李四学习数学，李四认真听讲。',
            时间戳=0.0,
            来源文档='doc1',
            置信度=0.0
        ),
        "method": "llm"
    },
    {
        "name": "中等情况 - 规则提取，中等长度",
        "relation": Relation(
            关系ID='r2',
            主体='张三',
            关系类型='教授',
            客体='李四',
            上下文='张三教李四数学。',
            时间戳=0.0,
            来源文档='doc1',
            置信度=0.0
        ),
        "method": "rule"
    },
    {
        "name": "弱情况 - 共现推断，短上下文",
        "relation": Relation(
            关系ID='r3',
            主体='张三',
            关系类型='关联',
            客体='李四',
            上下文='张三和李四',
            时间戳=0.0,
            来源文档='doc1',
            置信度=0.0
        ),
        "method": "cooccur"
    },
    {
        "name": "地名关系 - 位于类型",
        "relation": Relation(
            关系ID='r4',
            主体='张三',
            关系类型='位于',
            客体='北京',
            上下文='张三在北京工作。',
            时间戳=0.0,
            来源文档='doc1',
            置信度=0.0
        ),
        "method": "rule"
    },
    {
        "name": "低频实体 - 只出现一次",
        "relation": Relation(
            关系ID='r5',
            主体='未知人',
            关系类型='教授',
            客体='李四',
            上下文='未知人教李四。',
            时间戳=0.0,
            来源文档='doc1',
            置信度=0.0
        ),
        "method": "rule"
    },
    {
        "name": "超长上下文 - 信息密度低",
        "relation": Relation(
            关系ID='r6',
            主体='张三',
            关系类型='教授',
            客体='李四',
            上下文='走吧 走走 去 哎 對 ' * 50,  # 重复无意义文本
            时间戳=0.0,
            来源文档='doc1',
            置信度=0.0
        ),
        "method": "cooccur"
    }
]

print("\n测试用例：\n")
results = []
for i, test in enumerate(test_cases, 1):
    rel = test["relation"]
    method = test["method"]

    conf = agent._calculate_relation_confidence(rel, entities, method)
    results.append(conf)

    print(f"{i}. {test['name']}")
    print(f"   上下文: {rel.上下文[:40]}..." if len(rel.上下文) > 40 else f"   上下文: {rel.上下文}")
    print(f"   关系: {rel.主体} --[{rel.关系类型}]--> {rel.客体}")
    print(f"   提取方式: {method}")
    print(f"   置信度: {conf:.3f}")
    print()

print("="*60)
print("结果分析")
print("="*60)
print(f"最高置信度: {max(results):.3f}")
print(f"最低置信度: {min(results):.3f}")
print(f"平均置信度: {sum(results)/len(results):.3f}")
print(f"不同值数量: {len(set(results))}")

# 验证期望
print("\n验证：")
if results[0] > results[1] > results[2]:
    print("✅ LLM > 规则 > 共现")
else:
    print(f"❌ 提取方式排序错误: LLM={results[0]:.3f}, 规则={results[1]:.3f}, 共现={results[2]:.3f}")

if results[1] > results[4]:
    print("✅ 高频实体 > 低频实体")
else:
    print(f"❌ 实体重要性排序错误: 高频={results[1]:.3f}, 低频={results[4]:.3f}")

if results[1] > results[5]:
    print("✅ 正常上下文 > 超长无意义上下文")
else:
    print(f"❌ 上下文质量排序错误: 正常={results[1]:.3f}, 超长={results[5]:.3f}")

if len(set(results)) >= 4:
    print(f"✅ 置信度分布合理（{len(set(results))}种不同值）")
else:
    print(f"⚠️ 置信度分布单一（仅{len(set(results))}种不同值）")

print("\n" + "="*60)
