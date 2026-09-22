"""
依赖安全审计脚本
自动扫描 Python 依赖的安全漏洞
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path


def run_pip_audit():
    """运行 pip-audit 安全扫描"""
    print("=" * 80)
    print("运行依赖安全审计...")
    print("=" * 80)

    try:
        # 运行 pip-audit
        result = subprocess.run(
            ["pip-audit", "--format", "json"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ 未发现安全漏洞")
            return True
        else:
            # 解析 JSON 输出
            try:
                vulnerabilities = json.loads(result.stdout)
                print(f"\n⚠️ 发现 {len(vulnerabilities)} 个安全漏洞:\n")

                for vuln in vulnerabilities:
                    print(f"📦 {vuln['name']} {vuln['version']}")
                    print(f"   漏洞: {vuln['id']}")
                    print(f"   修复版本: {vuln.get('fix_versions', 'N/A')}")
                    print(f"   详情: {vuln.get('description', 'N/A')}")
                    print()

                return False
            except json.JSONDecodeError:
                print(result.stdout)
                return False

    except FileNotFoundError:
        print("❌ pip-audit 未安装")
        print("安装命令: pip install pip-audit")
        return False


def generate_report():
    """生成安全审计报告"""
    report_path = Path("security_audit_report.txt")

    with open(report_path, "w") as f:
        f.write(f"依赖安全审计报告\n")
        f.write(f"生成时间: {datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")

        # 运行审计
        result = subprocess.run(
            ["pip-audit"],
            capture_output=True,
            text=True
        )

        f.write(result.stdout)

    print(f"\n📄 报告已生成: {report_path}")


if __name__ == "__main__":
    success = run_pip_audit()
    generate_report()

    sys.exit(0 if success else 1)
