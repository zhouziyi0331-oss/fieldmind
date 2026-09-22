"""
Large Scale Testing Script - 大规模测试脚本

从用户的下载文件夹自动选择各种类型的文件进行测试
"""

import os
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Any
import mimetypes

# API 配置
API_BASE_URL = "http://localhost:8000"
PROJECT_ID = 1

# 支持的文件类型
SUPPORTED_EXTENSIONS = {
    'text': ['.txt', '.md', '.csv', '.json'],
    'document': ['.pdf', '.docx', '.doc'],
    'audio': ['.mp3', '.wav', '.m4a', '.aac'],
    'video': ['.mp4', '.mov', '.avi'],
    'image': ['.jpg', '.jpeg', '.png', '.gif']
}


class LargeScaleTester:
    """大规模测试器"""

    def __init__(self, downloads_path: str = None):
        """
        初始化测试器

        Args:
            downloads_path: 下载文件夹路径，默认为用户的下载文件夹
        """
        if downloads_path is None:
            # 自动检测下载文件夹
            home = Path.home()
            possible_paths = [
                home / 'Downloads',
                home / '下载',
                home / 'Desktop' / 'Downloads',
            ]
            for p in possible_paths:
                if p.exists():
                    self.downloads_path = p
                    break
            else:
                self.downloads_path = home / 'Downloads'
        else:
            self.downloads_path = Path(downloads_path)

        print(f"📂 下载文件夹: {self.downloads_path}")

    def scan_files(self, max_files_per_type: int = 5) -> Dict[str, List[Path]]:
        """
        扫描下载文件夹中的文件

        Args:
            max_files_per_type: 每种类型最多选择的文件数

        Returns:
            按类型分组的文件列表
        """
        print(f"\n🔍 扫描文件夹: {self.downloads_path}")

        files_by_type = {
            'text': [],
            'document': [],
            'audio': [],
            'video': [],
            'image': []
        }

        # 扫描文件
        for file_path in self.downloads_path.iterdir():
            if not file_path.is_file():
                continue

            ext = file_path.suffix.lower()

            # 按类型分类
            for file_type, extensions in SUPPORTED_EXTENSIONS.items():
                if ext in extensions:
                    if len(files_by_type[file_type]) < max_files_per_type:
                        files_by_type[file_type].append(file_path)
                    break

        # 打印扫描结果
        total = 0
        for file_type, files in files_by_type.items():
            count = len(files)
            total += count
            if count > 0:
                print(f"  {file_type}: {count} 个文件")
                for f in files:
                    print(f"    - {f.name}")

        print(f"\n✅ 共扫描到 {total} 个文件")
        return files_by_type

    def upload_file(self, file_path: Path) -> Dict[str, Any]:
        """
        上传文件到 FieldMind

        Args:
            file_path: 文件路径

        Returns:
            上传结果
        """
        print(f"\n📤 上传: {file_path.name}")

        try:
            # 检查文件大小
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            print(f"   大小: {file_size_mb:.2f} MB")

            if file_size_mb > 100:
                print(f"   ⚠️  文件太大（>100MB），跳过")
                return {'status': 'skipped', 'reason': 'too_large'}

            # 上传
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f)}
                data = {'project_id': PROJECT_ID}

                response = requests.post(
                    f"{API_BASE_URL}/api/documents/upload",
                    files=files,
                    data=data,
                    timeout=300
                )

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 上传成功: {result.get('document_id')}")
                return result
            else:
                print(f"   ❌ 上传失败: {response.status_code}")
                print(f"   错误: {response.text[:200]}")
                return {'status': 'error', 'code': response.status_code}

        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return {'status': 'error', 'message': str(e)}

    def wait_for_processing(self, delay: int = 5):
        """等待文件处理完成"""
        print(f"\n⏳ 等待 {delay} 秒，让文件处理完成...")
        time.sleep(delay)

    def check_chunks(self) -> int:
        """检查 chunks 数量"""
        print(f"\n🔍 检查 chunks 数量...")

        try:
            import sqlite3
            conn = sqlite3.connect('data/fieldmind.db')
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM document_chunks WHERE project_id = ?
            """, (PROJECT_ID,))

            count = cursor.fetchone()[0]
            conn.close()

            print(f"   ✅ 共有 {count} 个 chunks")
            return count

        except Exception as e:
            print(f"   ❌ 检查失败: {e}")
            return 0

    def trigger_analysis(self):
        """触发 TF-IDF 和聚类分析"""
        print(f"\n🚀 触发自动分析...")

        try:
            response = requests.post(
                f"{API_BASE_URL}/api/topics/auto-analyze/{PROJECT_ID}",
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 分析任务已启动")
                return result
            else:
                print(f"   ❌ 触发失败: {response.status_code}")
                return None

        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return None

    def check_results(self):
        """检查分析结果"""
        print(f"\n📊 检查分析结果...")

        # 1. 检查关键词
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/topics/keywords/project/{PROJECT_ID}?top_n=20",
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                keywords = result.get('keywords', [])
                print(f"   ✅ 关键词: {len(keywords)} 个")
                if keywords:
                    print(f"   Top 5:")
                    for kw in keywords[:5]:
                        print(f"     - {kw['keyword']}: {kw['total_tfidf_score']:.2f}")
            else:
                print(f"   ⚠️  关键词查询失败: {response.status_code}")

        except Exception as e:
            print(f"   ❌ 关键词查询异常: {e}")

        # 2. 检查聚类
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/topics/clusters/{PROJECT_ID}",
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                clusters = result.get('clusters', [])
                print(f"   ✅ 聚类: {len(clusters)} 个")
                for cluster in clusters:
                    print(f"     - 聚类 {cluster['cluster_id']}: {cluster['cluster_label']}")
                    print(f"       Chunks: {cluster['chunk_count']}")
            else:
                print(f"   ⚠️  聚类查询失败: {response.status_code}")

        except Exception as e:
            print(f"   ❌ 聚类查询异常: {e}")

    def run_test(self, max_files_per_type: int = 5):
        """
        运行大规模测试

        Args:
            max_files_per_type: 每种类型最多上传的文件数
        """
        print("\n" + "="*60)
        print("FieldMind 大规模测试开始")
        print("="*60)

        # 1. 扫描文件
        files_by_type = self.scan_files(max_files_per_type)

        total_files = sum(len(files) for files in files_by_type.values())
        if total_files == 0:
            print("\n❌ 没有找到可测试的文件")
            return

        # 2. 上传文件
        print(f"\n" + "="*60)
        print(f"开始上传 {total_files} 个文件")
        print("="*60)

        uploaded = 0
        for file_type, files in files_by_type.items():
            for file_path in files:
                result = self.upload_file(file_path)
                if result.get('status') != 'error':
                    uploaded += 1
                # 每次上传后等待2秒
                time.sleep(2)

        print(f"\n✅ 上传完成: {uploaded}/{total_files}")

        # 3. 等待处理
        self.wait_for_processing(delay=10)

        # 4. 检查 chunks
        chunk_count = self.check_chunks()

        if chunk_count < 5:
            print(f"\n⚠️  Chunks 数量不足（{chunk_count} < 5），无法进行聚类")
            return

        # 5. 触发分析
        self.trigger_analysis()

        # 6. 等待分析完成
        self.wait_for_processing(delay=30)

        # 7. 检查结果
        self.check_results()

        print("\n" + "="*60)
        print("✅ 大规模测试完成")
        print("="*60)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='FieldMind 大规模测试')
    parser.add_argument('--path', type=str, help='下载文件夹路径（可选）')
    parser.add_argument('--max', type=int, default=5, help='每种类型最多上传的文件数')

    args = parser.parse_args()

    tester = LargeScaleTester(args.path)
    tester.run_test(max_files_per_type=args.max)


if __name__ == "__main__":
    main()
