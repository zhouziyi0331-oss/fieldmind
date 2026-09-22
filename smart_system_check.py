#!/usr/bin/env python3
"""
FieldMind 智能系统检测工具
使用 system_paths.json 配置文件确保检测准确性
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class FieldMindSystemChecker:
    """系统完整性检测器"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.config = self.load_config()
        self.results = {
            "backend": {},
            "frontend": {}
        }

    def load_config(self) -> dict:
        """加载路径配置文件"""
        config_path = self.base_path / "system_paths.json"
        if not config_path.exists():
            print(f"❌ 配置文件不存在: {config_path}")
            sys.exit(1)

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def check_file(self, relative_path: str, base_dir: str = "backend/src") -> Tuple[bool, int]:
        """检查文件是否存在并返回大小"""
        full_path = self.base_path / base_dir / relative_path
        if full_path.exists():
            size = full_path.stat().st_size
            return True, size
        return False, 0

    def check_backend_module(self, module_name: str, files: dict) -> dict:
        """检查后端模块"""
        result = {
            "name": module_name,
            "total": len(files),
            "exists": 0,
            "missing": [],
            "files": {}
        }

        for file_key, file_path in files.items():
            exists, size = self.check_file(file_path)
            result["files"][file_key] = {
                "path": file_path,
                "exists": exists,
                "size": size
            }
            if exists:
                result["exists"] += 1
            else:
                result["missing"].append(file_key)

        result["percentage"] = (result["exists"] / result["total"] * 100) if result["total"] > 0 else 0
        return result

    def check_frontend_module(self, module_name: str, files: dict) -> dict:
        """检查前端模块"""
        result = {
            "name": module_name,
            "total": len(files),
            "exists": 0,
            "missing": [],
            "files": {}
        }

        for file_key, file_path in files.items():
            exists, size = self.check_file(file_path, "frontend/fieldmind-native/Sources")
            result["files"][file_key] = {
                "path": file_path,
                "exists": exists,
                "size": size
            }
            if exists:
                result["exists"] += 1
            else:
                result["missing"].append(file_key)

        result["percentage"] = (result["exists"] / result["total"] * 100) if result["total"] > 0 else 0
        return result

    def check_all(self):
        """检查所有模块"""
        print("=" * 80)
        print("FieldMind 系统完整性检测（智能版）")
        print("使用配置文件: system_paths.json")
        print("=" * 80)
        print()

        # 检查后端
        print("【后端模块检测】")
        print("-" * 80)

        backend_config = self.config.get("backend", {})
        for module_name, files in backend_config.items():
            result = self.check_backend_module(module_name, files)
            self.results["backend"][module_name] = result
            self.print_module_result(result)

        print()

        # 检查前端
        print("【前端模块检测】")
        print("-" * 80)

        frontend_config = self.config.get("frontend", {})
        for module_name, files in frontend_config.items():
            result = self.check_frontend_module(module_name, files)
            self.results["frontend"][module_name] = result
            self.print_module_result(result)

        print()
        self.print_summary()

    def print_module_result(self, result: dict):
        """打印模块检测结果"""
        percentage = result["percentage"]

        # 颜色标记
        if percentage == 100:
            status = "✅"
            color = "\033[0;32m"  # 绿色
        elif percentage >= 50:
            status = "⚠️"
            color = "\033[1;33m"  # 黄色
        else:
            status = "❌"
            color = "\033[0;31m"  # 红色

        reset = "\033[0m"

        print(f"{status} {result['name']}: {color}{percentage:.0f}%{reset} ({result['exists']}/{result['total']})")

        # 显示文件详情
        for file_key, file_info in result["files"].items():
            if file_info["exists"]:
                size_kb = file_info["size"] / 1024
                print(f"    ✓ {file_key}: {file_info['path']} ({size_kb:.1f} KB)")
            else:
                print(f"    ✗ {file_key}: {file_info['path']} (缺失)")
        print()

    def print_summary(self):
        """打印总结"""
        print("=" * 80)
        print("检测总结")
        print("=" * 80)
        print()

        # 后端总结
        backend_total = 0
        backend_exists = 0
        for module in self.results["backend"].values():
            backend_total += module["total"]
            backend_exists += module["exists"]

        backend_percentage = (backend_exists / backend_total * 100) if backend_total > 0 else 0

        # 前端总结
        frontend_total = 0
        frontend_exists = 0
        for module in self.results["frontend"].values():
            frontend_total += module["total"]
            frontend_exists += module["exists"]

        frontend_percentage = (frontend_exists / frontend_total * 100) if frontend_total > 0 else 0

        # 总体
        overall_total = backend_total + frontend_total
        overall_exists = backend_exists + frontend_exists
        overall_percentage = (overall_exists / overall_total * 100) if overall_total > 0 else 0

        print(f"后端完成度: {backend_percentage:.0f}% ({backend_exists}/{backend_total})")
        print(f"前端完成度: {frontend_percentage:.0f}% ({frontend_exists}/{frontend_total})")
        print(f"整体完成度: {overall_percentage:.0f}% ({overall_exists}/{overall_total})")
        print()

        # 缺失项
        backend_missing = backend_total - backend_exists
        frontend_missing = frontend_total - frontend_exists

        if backend_missing > 0 or frontend_missing > 0:
            print("缺失项统计:")
            if backend_missing > 0:
                print(f"  后端缺失: {backend_missing} 个")
            if frontend_missing > 0:
                print(f"  前端缺失: {frontend_missing} 个")
        else:
            print("✅ 所有模块完整！")

        print()
        print("=" * 80)

def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    base_path = script_dir

    # 如果在 scripts 目录下运行，向上一级
    if script_dir.name == "scripts":
        base_path = script_dir.parent

    checker = FieldMindSystemChecker(str(base_path))
    checker.check_all()

if __name__ == "__main__":
    main()
