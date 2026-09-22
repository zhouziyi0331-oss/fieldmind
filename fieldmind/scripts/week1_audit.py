#!/usr/bin/env python3
"""
FieldMind 系统审计脚本
第一周任务：全面了解当前系统状态
"""

import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class FieldMindAuditor:
    def __init__(self, base_path="/Users/alwan/Downloads/FieldMind"):
        self.base_path = Path(base_path)
        self.report = {
            "audit_time": datetime.now().isoformat(),
            "database": {},
            "api": {},
            "models": {},
            "files": {}
        }

    def audit_databases(self):
        """审计数据库状态"""
        print("=" * 60)
        print("1️⃣  审计数据库")
        print("=" * 60)

        # 查找所有数据库文件
        db_files = list(self.base_path.rglob("*.db"))
        db_files += list(self.base_path.rglob("*.sqlite"))

        print(f"\n找到 {len(db_files)} 个数据库文件：")

        for db_file in db_files:
            if db_file.stat().st_size == 0:
                print(f"  ⚠️  {db_file.relative_to(self.base_path)} (空文件)")
                continue

            print(f"\n  📊 {db_file.relative_to(self.base_path)}")

            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()

                # 获取所有表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                print(f"     表数量: {len(tables)}")

                db_info = {
                    "path": str(db_file.relative_to(self.base_path)),
                    "size_mb": db_file.stat().st_size / 1024 / 1024,
                    "tables": {}
                }

                # 统计每个表的记录数
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]

                        # 获取表结构
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = cursor.fetchall()

                        db_info["tables"][table] = {
                            "count": count,
                            "columns": len(columns)
                        }

                        if count > 0:
                            print(f"       {table}: {count} 条记录, {len(columns)} 列")
                    except Exception as e:
                        print(f"       {table}: 查询失败 - {e}")

                self.report["database"][str(db_file.name)] = db_info
                conn.close()

            except Exception as e:
                print(f"     ❌ 无法打开: {e}")

        return self.report["database"]

    def audit_models(self):
        """审计数据模型"""
        print("\n" + "=" * 60)
        print("2️⃣  审计数据模型")
        print("=" * 60)

        models_path = self.base_path / "backend" / "src" / "app" / "models"

        if not models_path.exists():
            print("❌ models 目录不存在")
            return

        model_files = list(models_path.glob("*.py"))
        print(f"\n找到 {len(model_files)} 个模型文件\n")

        models_info = {}

        for model_file in sorted(model_files):
            if model_file.name.startswith("__"):
                continue

            # 读取文件内容
            content = model_file.read_text(encoding='utf-8', errors='ignore')

            # 简单统计
            has_sqlalchemy = "from sqlalchemy" in content or "import sqlalchemy" in content
            has_class = "class " in content
            line_count = len(content.split('\n'))

            model_name = model_file.stem
            models_info[model_name] = {
                "lines": line_count,
                "has_sqlalchemy": has_sqlalchemy,
                "has_class": has_class
            }

            status = "✅" if has_sqlalchemy and has_class else "⚠️ "
            print(f"  {status} {model_name}.py ({line_count} 行)")

        self.report["models"] = models_info
        return models_info

    def audit_apis(self):
        """审计 API 端点"""
        print("\n" + "=" * 60)
        print("3️⃣  审计 API 端点")
        print("=" * 60)

        api_path = self.base_path / "backend" / "src" / "app" / "api"

        if not api_path.exists():
            print("❌ api 目录不存在")
            return

        api_files = list(api_path.rglob("*.py"))

        import re
        router_pattern = re.compile(r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']')
        app_pattern = re.compile(r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']')

        apis = []

        for api_file in api_files:
            if "__pycache__" in str(api_file):
                continue

            try:
                content = api_file.read_text(encoding='utf-8', errors='ignore')

                # 查找路由定义
                for pattern in [router_pattern, app_pattern]:
                    matches = pattern.findall(content)
                    for method, path in matches:
                        apis.append({
                            "method": method.upper(),
                            "path": path,
                            "file": str(api_file.relative_to(self.base_path))
                        })
            except Exception as e:
                print(f"  ⚠️  无法读取 {api_file.name}: {e}")

        print(f"\n总共找到 {len(apis)} 个 API 端点\n")

        # 按 HTTP 方法分组
        by_method = defaultdict(int)
        for api in apis:
            by_method[api["method"]] += 1

        print("按 HTTP 方法统计：")
        for method, count in sorted(by_method.items()):
            print(f"  {method}: {count} 个")

        # 找出重复的端点
        print("\n检查重复端点：")
        endpoint_map = defaultdict(list)
        for api in apis:
            key = f"{api['method']} {api['path']}"
            endpoint_map[key].append(api['file'])

        duplicates = {k: v for k, v in endpoint_map.items() if len(v) > 1}

        if duplicates:
            print(f"  ❌ 发现 {len(duplicates)} 个重复端点：")
            for endpoint, files in list(duplicates.items())[:5]:
                print(f"     {endpoint}")
                for f in files:
                    print(f"       - {f}")
        else:
            print("  ✅ 没有重复端点")

        self.report["api"] = {
            "total": len(apis),
            "by_method": dict(by_method),
            "duplicates": len(duplicates),
            "sample": apis[:10]
        }

        return apis

    def audit_file_structure(self):
        """审计文件结构"""
        print("\n" + "=" * 60)
        print("4️⃣  审计文件结构")
        print("=" * 60)

        important_dirs = [
            "backend/src/app",
            "frontend/src",
            "frontend/fieldmind-native",
            "docs"
        ]

        for dir_name in important_dirs:
            dir_path = self.base_path / dir_name
            if dir_path.exists():
                # 统计文件数
                py_files = list(dir_path.rglob("*.py"))
                ts_files = list(dir_path.rglob("*.ts"))
                tsx_files = list(dir_path.rglob("*.tsx"))
                swift_files = list(dir_path.rglob("*.swift"))

                total = len(py_files) + len(ts_files) + len(tsx_files) + len(swift_files)

                print(f"\n  📁 {dir_name}")
                print(f"     Python: {len(py_files)} 文件")
                print(f"     TypeScript: {len(ts_files) + len(tsx_files)} 文件")
                print(f"     Swift: {len(swift_files)} 文件")
                print(f"     总计: {total} 文件")
            else:
                print(f"\n  ❌ {dir_name} 不存在")

    def generate_report(self):
        """生成审计报告"""
        print("\n" + "=" * 60)
        print("5️⃣  生成审计报告")
        print("=" * 60)

        report_path = self.base_path / "fieldmind" / "WEEK1_AUDIT_REPORT.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 审计报告已保存到:")
        print(f"   {report_path}")

        # 生成 Markdown 报告
        md_report = self._generate_markdown_report()
        md_path = self.base_path / "fieldmind" / "WEEK1_AUDIT_REPORT.md"

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_report)

        print(f"   {md_path}")

    def _generate_markdown_report(self):
        """生成 Markdown 格式的报告"""
        md = f"""# FieldMind 系统审计报告
生成时间: {self.report['audit_time']}

## 📊 数据库审计

"""

        if self.report.get("database"):
            for db_name, db_info in self.report["database"].items():
                md += f"### {db_name}\n\n"
                md += f"- 大小: {db_info['size_mb']:.2f} MB\n"
                md += f"- 表数量: {len(db_info['tables'])}\n\n"

                if db_info['tables']:
                    md += "| 表名 | 记录数 | 列数 |\n"
                    md += "|------|--------|------|\n"
                    for table_name, table_info in sorted(db_info['tables'].items()):
                        md += f"| {table_name} | {table_info['count']} | {table_info['columns']} |\n"
                    md += "\n"

        md += f"""
## 🔌 API 审计

- 总端点数: {self.report['api'].get('total', 0)}
- 重复端点: {self.report['api'].get('duplicates', 0)}

"""

        if self.report['api'].get('by_method'):
            md += "### 按 HTTP 方法统计\n\n"
            for method, count in sorted(self.report['api']['by_method'].items()):
                md += f"- {method}: {count}\n"

        md += f"""
## 📦 数据模型审计

- 模型文件数: {len(self.report.get('models', {}))}

"""

        return md

    def run_full_audit(self):
        """运行完整审计"""
        print("\n" + "=" * 60)
        print("FieldMind 系统全面审计")
        print("=" * 60)
        print(f"基础路径: {self.base_path}")
        print("=" * 60)

        self.audit_databases()
        self.audit_models()
        self.audit_apis()
        self.audit_file_structure()
        self.generate_report()

        print("\n" + "=" * 60)
        print("✅ 审计完成")
        print("=" * 60)


if __name__ == "__main__":
    auditor = FieldMindAuditor()
    auditor.run_full_audit()
