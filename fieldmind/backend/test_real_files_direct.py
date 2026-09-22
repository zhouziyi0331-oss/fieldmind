"""
直接通过数据库创建测试项目并上传文件测试
"""

import sys
import os
sys.path.insert(0, '/Users/alwan/Downloads/FieldMind/fieldmind/backend/src')

import sqlite3
from datetime import datetime

# 数据库路径
DB_PATH = "/Users/alwan/FieldMind/backend/src/data/fieldmind.db"

# 测试文件
TEST_FILES = {
    "pdf": "/Users/alwan/Downloads/音寨布依族村 · 文化全景深度报告.pdf",
    "image": "/Users/alwan/Downloads/e5031004fce426b0d3566eb96b5a067d.jpg",
    "excel": "/Users/alwan/Downloads/deliverables_____1___.xlsx"
}

def create_test_project():
    """创建测试项目"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查是否已有项目
    cursor.execute("SELECT id, name FROM projects LIMIT 1")
    existing = cursor.fetchone()

    if existing:
        project_id, project_name = existing
        print(f"✅ 使用现有项目: ID={project_id}, 名称={project_name}")
    else:
        # 创建新项目
        cursor.execute("""
        INSERT INTO projects (name, description, settings, owner_id, status, created_at, updated_at, last_activity_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "端到端测试项目",
            "使用真实文件测试完整数据流",
            "{}",
            1,
            "active",
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        ))
        conn.commit()
        project_id = cursor.lastrowid
        print(f"✅ 创建新项目: ID={project_id}")

    conn.close()
    return project_id

def upload_test_files(project_id):
    """通过API上传测试文件"""
    import requests

    uploaded = {}

    for file_type, file_path in TEST_FILES.items():
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            continue

        filename = os.path.basename(file_path)
        print(f"\n上传 {file_type}: {filename}")

        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f)}
                data = {'project_id': project_id}

                response = requests.post(
                    f"http://localhost:8000/api/v1/projects/{project_id}/documents/upload",
                    files=files,
                    data=data,
                    timeout=30
                )

            if response.status_code == 200:
                result = response.json()
                doc_id = result.get("id")
                uploaded[file_type] = doc_id
                print(f"✅ 上传成功，文档ID: {doc_id}")
            else:
                print(f"❌ 上传失败: {response.status_code} - {response.text[:200]}")

        except Exception as e:
            print(f"❌ 上传异常: {e}")

    return uploaded

def test_normalization(uploaded_files):
    """测试文档规范化"""
    import requests
    import time

    print("\n" + "="*80)
    print("🔧 测试文档规范化")
    print("="*80)

    for file_type, doc_id in uploaded_files.items():
        print(f"\n{'='*60}")
        print(f"测试 {file_type.upper()} (文档ID: {doc_id})")
        print(f"{'='*60}")

        # 1. 触发规范化
        print("\n1️⃣  触发规范化...")
        try:
            response = requests.post(
                f"http://localhost:8000/api/v1/files/{doc_id}/normalize",
                json={"force": True},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ 规范化已触发，状态: {result.get('status')}")
            else:
                print(f"❌ 触发失败: {response.status_code} - {response.text[:200]}")
                continue
        except Exception as e:
            print(f"❌ 触发异常: {e}")
            continue

        # 2. 等待处理
        print("\n⏳ 等待处理完成（15秒）...")
        time.sleep(15)

        # 3. 检查规范化结果
        print("\n2️⃣  检查规范化结果...")
        try:
            response = requests.get(
                f"http://localhost:8000/api/v1/files/{doc_id}/normalized",
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ 规范化完成")
                print(f"   📄 文档类型: {result.get('file_type')}")
                print(f"   📝 文本长度: {result.get('word_count')} 字")
                print(f"   📊 完整性: {result.get('completeness', {}).get('score', 0)*100:.1f}%")
                print(f"   🎯 置信度: {result.get('confidence', 0)*100:.1f}%")

                # 显示元数据
                metadata = result.get('metadata', {})
                if metadata:
                    print(f"\n   📋 元数据:")
                    for key, value in list(metadata.items())[:5]:
                        print(f"      - {key}: {value}")

            else:
                print(f"❌ 获取失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 检查异常: {e}")

        # 4. 检查脏数据报告
        print("\n3️⃣  检查脏数据报告...")
        try:
            response = requests.get(
                f"http://localhost:8000/api/v1/files/{doc_id}/dirty-data-report",
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                total = result.get('total_dirty_data', 0)
                print(f"✅ 脏数据总数: {total}")

                by_type = result.get('dirty_data_by_type', {})
                if by_type:
                    print(f"   分类统计:")
                    for dtype, count in by_type.items():
                        print(f"      - {dtype}: {count}个")
            else:
                print(f"⚠️  暂无脏数据报告")
        except Exception as e:
            print(f"❌ 检查异常: {e}")

        # 5. 检查完整性
        print("\n4️⃣  检查完整性...")
        try:
            response = requests.get(
                f"http://localhost:8000/api/v1/files/{doc_id}/completeness-check",
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                is_complete = result.get('is_complete')
                score = result.get('score', 0)

                print(f"{'✅' if is_complete else '⚠️ '} 完整性: {score*100:.1f}%")

                issues = result.get('issues', [])
                if issues:
                    print(f"   问题列表:")
                    for issue in issues[:3]:
                        print(f"      - {issue}")
            else:
                print(f"⚠️  暂无完整性检查")
        except Exception as e:
            print(f"❌ 检查异常: {e}")

def check_database_results(uploaded_files):
    """检查数据库中的结果"""
    print("\n" + "="*80)
    print("📊 检查数据库结果")
    print("="*80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for file_type, doc_id in uploaded_files.items():
        print(f"\n{'='*60}")
        print(f"{file_type.upper()} (文档ID: {doc_id})")
        print(f"{'='*60}")

        # 1. 检查规范化日志
        print("\n1️⃣  规范化日志:")
        cursor.execute("""
        SELECT file_type, normalization_rule, completeness_score, confidence, processing_time_ms
        FROM document_normalization_logs
        WHERE file_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """, (doc_id,))

        log = cursor.fetchone()
        if log:
            print(f"   ✅ 文件类型: {log[0]}")
            print(f"   ✅ 规则: {log[1]}")
            print(f"   ✅ 完整性: {log[2]*100:.1f}%")
            print(f"   ✅ 置信度: {log[3]*100:.1f}%")
            print(f"   ✅ 处理时间: {log[4]}ms")
        else:
            print("   ⚠️  无规范化日志")

        # 2. 检查规范化内容
        print("\n2️⃣  规范化内容:")
        cursor.execute("""
        SELECT content_type, COUNT(*), AVG(confidence)
        FROM file_normalized_content
        WHERE file_id = ?
        GROUP BY content_type
        """, (doc_id,))

        contents = cursor.fetchall()
        if contents:
            for content_type, count, avg_conf in contents:
                print(f"   ✅ {content_type}: {count}条，平均置信度 {avg_conf*100:.1f}%")
        else:
            print("   ⚠️  无规范化内容")

        # 3. 检查完整性检查
        print("\n3️⃣  完整性检查:")
        cursor.execute("""
        SELECT check_type, is_passed, score
        FROM file_completeness_checks
        WHERE file_id = ?
        """, (doc_id,))

        checks = cursor.fetchall()
        if checks:
            for check_type, is_passed, score in checks:
                status = "✅ 通过" if is_passed else "❌ 未通过"
                print(f"   {status} {check_type}: {score*100:.1f}%")
        else:
            print("   ⚠️  无完整性检查")

    conn.close()

def main():
    print("="*80)
    print("🚀 FieldMind 真实文件端到端测试")
    print("="*80)

    # 1. 创建项目
    print("\n步骤1: 创建测试项目")
    project_id = create_test_project()

    # 2. 上传文件
    print("\n步骤2: 上传真实文件")
    uploaded = upload_test_files(project_id)

    if not uploaded:
        print("\n❌ 没有成功上传任何文件，测试终止")
        return

    print(f"\n✅ 成功上传 {len(uploaded)} 个文件")

    # 3. 测试规范化
    test_normalization(uploaded)

    # 4. 检查数据库
    check_database_results(uploaded)

    print("\n" + "="*80)
    print("🎉 测试完成")
    print("="*80)

if __name__ == "__main__":
    main()
