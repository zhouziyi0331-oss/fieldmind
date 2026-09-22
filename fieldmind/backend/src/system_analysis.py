"""
FieldMind 系统现状全面分析
检查采集、处理、理解、分析、协同、复用六大层级的实现状态
"""
import os
import json
from pathlib import Path

def check_layer(layer_name, files_to_check, functions_to_check):
    """检查某一层的实现状态"""
    print(f"\n{'='*80}")
    print(f"【{layer_name}】")
    print('='*80)
    
    results = {
        "layer": layer_name,
        "files_found": [],
        "files_missing": [],
        "functions_found": [],
        "functions_missing": [],
        "completion": 0
    }
    
    # 检查文件
    for file_path in files_to_check:
        full_path = Path(file_path)
        if full_path.exists():
            results["files_found"].append(file_path)
            print(f"  ✅ 文件存在: {file_path}")
            
            # 检查文件中的关键函数
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for func_name in functions_to_check.get(file_path, []):
                    if f"def {func_name}" in content or f"async def {func_name}" in content:
                        results["functions_found"].append(f"{file_path}::{func_name}")
                        print(f"    ✅ 函数: {func_name}")
                    else:
                        results["functions_missing"].append(f"{file_path}::{func_name}")
                        print(f"    ❌ 函数缺失: {func_name}")
            except Exception as e:
                print(f"    ⚠️  读取文件失败: {e}")
        else:
            results["files_missing"].append(file_path)
            print(f"  ❌ 文件缺失: {file_path}")
    
    # 计算完成度
    total_items = len(files_to_check) + sum(len(funcs) for funcs in functions_to_check.values())
    found_items = len(results["files_found"]) + len(results["functions_found"])
    results["completion"] = int((found_items / total_items * 100)) if total_items > 0 else 0
    
    print(f"\n  完成度: {results['completion']}%")
    
    return results

# 定义六大层级需要检查的内容
layers = {
    "采集层": {
        "files": [
            "app/api/v1/documents.py",
            "app/services/file_upload_service.py",
        ],
        "functions": {
            "app/api/v1/documents.py": [
                "upload_document",
                "upload_documents_batch",
            ],
        }
    },
    
    "处理层": {
        "files": [
            "app/services/background_tasks.py",
            "app/services/document_converter.py",
            "app/services/chunking_service.py",
            "app/services/text_quantification.py",
        ],
        "functions": {
            "app/services/background_tasks.py": [
                "process_document_async",
            ],
            "app/services/chunking_service.py": [
                "chunk_text",
                "create_chunks_from_document",
            ],
            "app/services/text_quantification.py": [
                "quantify_text",
                "calculate_sentiment",
            ],
        }
    },
    
    "理解层": {
        "files": [
            "app/services/keyword_extraction.py",
            "app/services/knowledge_graph_service.py",
            "app/services/entity_extraction.py",
        ],
        "functions": {
            "app/services/keyword_extraction.py": [
                "extract_keywords",
            ],
            "app/services/knowledge_graph_service.py": [
                "build_knowledge_graph",
                "extract_entities",
                "extract_relations",
            ],
        }
    },
    
    "分析层": {
        "files": [
            "app/api/reports_real.py",
            "app/services/business_analysis_service.py",
            "app/api/v1/business_analysis.py",
        ],
        "functions": {
            "app/api/reports_real.py": [
                "generate_level1_report",
                "generate_level2_report",
                "generate_level3_report",
            ],
        }
    },
    
    "协同层": {
        "files": [
            "app/api/chat.py",
            "app/services/rag_engine.py",
            "app/models/conversation.py",
        ],
        "functions": {
            "app/api/chat.py": [
                "chat",
                "chat_stream",
            ],
            "app/services/rag_engine.py": [
                "search_relevant_chunks",
                "build_context",
            ],
        }
    },
    
    "复用层": {
        "files": [
            "app/services/skill_service.py",
            "app/models/skill.py",
            "app/api/v1/skills.py",
        ],
        "functions": {
            "app/services/skill_service.py": [
                "execute_skill",
                "get_skill_by_name",
            ],
        }
    },
}

print("FieldMind 系统现状全面分析")
print("="*80)

all_results = {}
for layer_name, layer_config in layers.items():
    result = check_layer(
        layer_name,
        layer_config["files"],
        layer_config["functions"]
    )
    all_results[layer_name] = result

# 总结
print("\n" + "="*80)
print("【总结】")
print("="*80)

for layer_name, result in all_results.items():
    print(f"{layer_name}: {result['completion']}%")

avg_completion = sum(r['completion'] for r in all_results.values()) / len(all_results)
print(f"\n整体完成度: {int(avg_completion)}%")

# 保存结果
with open('system_analysis_result.json', 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print("\n详细结果已保存到: system_analysis_result.json")
