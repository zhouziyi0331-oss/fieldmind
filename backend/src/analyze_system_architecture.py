"""系统架构分析工具 - 分析插件、服务、Agent的使用情况和整合机会"""
import os
import re
from pathlib import Path
from collections import defaultdict

def scan_imports(directory):
    """扫描所有Python文件的导入"""
    imports = defaultdict(list)
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 查找所有from/import语句
                        for match in re.finditer(r'^(?:from|import)\s+([\w.]+)', content, re.MULTILINE):
                            module = match.group(1)
                            imports[module].append(filepath.replace(directory + '/', ''))
                except:
                    pass
    
    return imports

def analyze_tools():
    """分析工具层"""
    print("=" * 80)
    print("🔧 工具层 (app/tools) 分析")
    print("=" * 80)
    
    tools = {
        'document': ['unified_document_converter', 'unified_document_chunker', 'unified_document_pipeline'],
        'entity': ['unified_entity_extractor'],
        'knowledge': ['unified_graph_engine'],
        'vectorization': ['unified_vectorization_engine']
    }
    
    for category, items in tools.items():
        print(f"\n📦 {category}:")
        for item in items:
            print(f"  ✓ {item}.py")
    
    return tools

def analyze_agents():
    """分析Agent层"""
    print("\n" + "=" * 80)
    print("🤖 Agent层分析")
    print("=" * 80)
    
    # 顶层Agents (app/agents)
    top_agents = ['base_agent', 'coordinator', 'entity_relation_agent', 'field_dimension_agent']
    print("\n📍 顶层Agents (app/agents):")
    for agent in top_agents:
        print(f"  ✓ {agent}.py")
    
    # 服务层Agents (app/services/agents)
    service_agents = ['base_agent', 'coordinator_agent', 'transcript_agent', 'summary_agent', 
                      'entity_agent', 'relation_agent', 'knowledge_agent', 'search_agent']
    print("\n📍 服务层Agents (app/services/agents):")
    for agent in service_agents:
        print(f"  ✓ {agent}.py")
    
    return {'top_agents': top_agents, 'service_agents': service_agents}

def analyze_services():
    """分析服务层"""
    print("\n" + "=" * 80)
    print("⚙️  服务层 (app/services) 分析")
    print("=" * 80)
    
    services_dir = 'app/services'
    services = []
    
    for file in sorted(os.listdir(services_dir)):
        if file.endswith('.py') and file != '__init__.py' and not file.endswith('.bak'):
            services.append(file[:-3])
    
    print(f"\n总计: {len(services)} 个服务文件")
    
    # 分类
    categories = {
        '文档处理': ['document_processing', 'document_parser', 'document_chunker', 'document_converter'],
        '实体&关系': ['entity_', 'relation_', 'evidence_'],
        '知识图谱': ['knowledge_', 'graph_', 'network_'],
        '向量化&检索': ['vectorization', 'embedding', 'retrieval', 'hierarchical_retriever'],
        'AI&对话': ['chat_', 'conversation_', 'memory_', 'intelligent_agent'],
        '分析': ['analysis', 'analyzer', 'classifier'],
        '其他': []
    }
    
    categorized = defaultdict(list)
    for service in services:
        matched = False
        for cat, patterns in categories.items():
            if cat == '其他':
                continue
            for pattern in patterns:
                if pattern in service:
                    categorized[cat].append(service)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            categorized['其他'].append(service)
    
    for cat, items in categorized.items():
        if items:
            print(f"\n{cat} ({len(items)}):")
            for item in sorted(items)[:10]:  # 只显示前10个
                print(f"  • {item}")
            if len(items) > 10:
                print(f"  ... 还有 {len(items) - 10} 个")
    
    return categorized

def find_unused_or_redundant():
    """查找未使用或冗余的模块"""
    print("\n" + "=" * 80)
    print("🔍 未使用/冗余模块分析")
    print("=" * 80)
    
    imports = scan_imports('app')
    
    # 检查工具层使用情况
    print("\n📊 工具层使用统计:")
    tool_modules = [
        'app.tools.document.unified_document_pipeline',
        'app.tools.document.unified_document_converter',
        'app.tools.document.unified_document_chunker',
        'app.tools.entity.unified_entity_extractor',
        'app.tools.knowledge.unified_graph_engine',
        'app.tools.vectorization.unified_vectorization_engine'
    ]
    
    for module in tool_modules:
        count = len(imports.get(module, []))
        status = "✓ 使用中" if count > 0 else "⚠️  未使用"
        print(f"  {status} {module.split('.')[-1]}: {count} 次引用")
    
    # 检查服务层Agent使用情况
    print("\n📊 服务层Agents使用统计:")
    agent_modules = [
        'app.services.agents.coordinator_agent',
        'app.services.agents.transcript_agent',
        'app.services.agents.summary_agent',
        'app.services.agents.entity_agent',
        'app.services.agents.relation_agent',
        'app.services.agents.knowledge_agent',
        'app.services.agents.search_agent'
    ]
    
    for module in agent_modules:
        count = len(imports.get(module, []))
        status = "✓ 使用中" if count > 0 else "⚠️  未使用"
        print(f"  {status} {module.split('.')[-1]}: {count} 次引用")

def suggest_integration():
    """提出整合建议"""
    print("\n" + "=" * 80)
    print("💡 系统整合建议")
    print("=" * 80)
    
    suggestions = [
        {
            'title': '建议1: Agent层整合',
            'problem': '存在两套Agent系统（app/agents + app/services/agents）',
            'solution': '将服务层8个Agents降级为工具层，保留顶层的协调器',
            'benefit': '简化架构，统一Agent调用方式',
            'files': 8,
            'impact': '中等'
        },
        {
            'title': '建议2: 文档处理整合',
            'problem': '文档处理服务分散（converter, chunker, parser, pipeline）',
            'solution': '基于已有的unified_document_pipeline统一所有文档处理逻辑',
            'benefit': '单一入口，减少重复代码',
            'files': 5,
            'impact': '高'
        },
        {
            'title': '建议3: 实体关系整合',
            'problem': '实体提取、关系抽取、证据链功能分散',
            'solution': '将entity_service + relation_service + evidence_extractor合并',
            'benefit': '上下游联动，提升性能',
            'files': 6,
            'impact': '高'
        },
        {
            'title': '建议4: 知识图谱整合',
            'problem': '知识图谱构建、网络分析功能分散',
            'solution': '基于unified_graph_engine扩展所有图谱功能',
            'benefit': '统一图谱接口，易于扩展',
            'files': 4,
            'impact': '中等'
        },
        {
            'title': '建议5: 检索系统整合',
            'problem': 'hierarchical_retriever + chat_service + conversation_memory分散',
            'solution': '构建统一的RAG检索引擎',
            'benefit': '统一检索策略，优化性能',
            'files': 3,
            'impact': '高'
        }
    ]
    
    for i, sug in enumerate(suggestions, 1):
        print(f"\n{sug['title']}")
        print(f"  问题: {sug['problem']}")
        print(f"  方案: {sug['solution']}")
        print(f"  收益: {sug['benefit']}")
        print(f"  涉及: {sug['files']} 个文件")
        print(f"  影响: {sug['impact']}")

if __name__ == '__main__':
    analyze_tools()
    analyze_agents()
    analyze_services()
    find_unused_or_redundant()
    suggest_integration()
    
    print("\n" + "=" * 80)
    print("✅ 分析完成")
    print("=" * 80)
