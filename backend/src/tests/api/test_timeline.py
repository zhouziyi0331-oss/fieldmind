"""
时间线 API 测试
测试时间线事件提取、获取和分组功能
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.main import app
from tests.conftest import client, auth_headers, test_user
from app.core.database import get_db


@pytest.fixture
def db():
    """获取数据库会话"""
    db_gen = get_db()
    db_session = next(db_gen)
    yield db_session
    db_session.close()


class TestTimelineAPI:
    """时间线 API 测试类"""

    def test_get_project_timeline_success(self, client, auth_headers):
        """测试成功获取项目时间线"""
        # 创建项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={
                "name": "Timeline Test Project",
                "description": "Project for timeline testing"
            }
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # 获取时间线（空项目）
        response = client.get(
            f"/api/timeline/projects/{project_id}/events",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "statistics" in data
        assert data["events"] == []
        assert data["statistics"]["total_events"] == 0

    def test_get_project_timeline_with_events(self, client, auth_headers, db):
        """测试获取包含事件的项目时间线"""
        from app.models.project import Project, ProjectDocument

        # 创建项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={
                "name": "Timeline Events Project",
                "description": "Project with timeline events"
            }
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # 获取项目对象
        project = db.query(Project).filter(Project.id == project_id).first()

        # 手动添加文档（包含日期信息）
        doc = ProjectDocument(
            project_id=project.id,
            filename="test_document.txt",
            original_filename="test_document.txt",
            file_path="/fake/path/test_document.txt",
            file_type="text/plain",
            file_size=1024,
            status="completed",
            text_content="2023年1月15日，公司成立。2023年3月20日，产品发布。2023年12月1日，达成目标。"
        )
        db.add(doc)
        db.commit()

        # 获取时间线
        response = client.get(
            f"/api/timeline/projects/{project_id}/events",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 3
        assert data["statistics"]["total_events"] == 3

        # 验证事件排序（按时间）
        events = data["events"]
        assert events[0]["date"] == "2023-01-15"
        assert events[1]["date"] == "2023-03-20"
        assert events[2]["date"] == "2023-12-01"

        # 验证事件内容
        assert "公司成立" in events[0]["description"]
        assert "产品发布" in events[1]["description"]

        # 验证统计信息
        assert data["statistics"]["date_range"]["start"] == "2023-01-15"
        assert data["statistics"]["date_range"]["end"] == "2023-12-01"

        # 验证按年份分组
        assert "events_by_year" in data
        assert "2023" in data["events_by_year"]
        assert len(data["events_by_year"]["2023"]) == 3

    def test_get_project_timeline_not_found(self, client, auth_headers):
        """测试获取不存在的项目时间线"""
        response = client.get(
            "/api/timeline/projects/99999/events",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "项目不存在" in response.json()["detail"]

    def test_get_grouped_timeline_by_year(self, client, auth_headers, db):
        """测试按年份分组获取时间线"""
        from app.models.project import Project, ProjectDocument

        # 创建项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={
                "name": "Grouped Timeline Project",
                "description": "Project for grouped timeline"
            }
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # 获取项目对象
        project = db.query(Project).filter(Project.id == project_id).first()

        # 添加跨年文档
        doc = ProjectDocument(
            project_id=project.id,
            filename="multi_year.txt",
            original_filename="multi_year.txt",
            file_path="/fake/path/multi_year.txt",
            file_type="text/plain",
            file_size=2048,
            status="completed",
            text_content="2022年6月1日，项目启动。2023年2月15日，完成开发。2024年1月10日，正式上线。"
        )
        db.add(doc)
        db.commit()

        # 按年份分组
        response = client.get(
            f"/api/timeline/projects/{project_id}/events/grouped",
            headers=auth_headers,
            params={"group_by": "year"}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证分组结构
        assert "groups" in data
        assert "statistics" in data
        assert len(data["groups"]) == 3

        # 验证每个年份的分组
        groups = {g["key"]: g for g in data["groups"]}
        assert "2022" in groups
        assert "2023" in groups
        assert "2024" in groups

        assert groups["2022"]["count"] == 1
        assert groups["2023"]["count"] == 1
        assert groups["2024"]["count"] == 1

    def test_get_grouped_timeline_by_month(self, client, auth_headers, db):
        """测试按月份分组获取时间线"""
        from app.models.project import Project, ProjectDocument

        # 创建项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={
                "name": "Monthly Timeline Project",
                "description": "Project for monthly timeline"
            }
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # 获取项目对象
        project = db.query(Project).filter(Project.id == project_id).first()

        # 添加同年不同月的文档
        doc = ProjectDocument(
            project_id=project.id,
            filename="monthly_events.txt",
            original_filename="monthly_events.txt",
            file_path="/fake/path/monthly_events.txt",
            file_type="text/plain",
            file_size=1536,
            status="completed",
            text_content="2023年1月5日，第一阶段。2023年1月20日，第二阶段。2023年3月15日，第三阶段。"
        )
        db.add(doc)
        db.commit()

        # 按月份分组
        response = client.get(
            f"/api/timeline/projects/{project_id}/events/grouped",
            headers=auth_headers,
            params={"group_by": "month"}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证分组
        groups = {g["key"]: g for g in data["groups"]}
        assert "2023-01" in groups
        assert "2023-03" in groups

        # 1月有2个事件
        assert groups["2023-01"]["count"] == 2
        # 3月有1个事件
        assert groups["2023-03"]["count"] == 1

    def test_get_grouped_timeline_by_document(self, client, auth_headers, db):
        """测试按文档分组获取时间线"""
        from app.models.project import Project, ProjectDocument

        # 创建项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={
                "name": "Document Grouped Project",
                "description": "Project for document grouping"
            }
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # 获取项目对象
        project = db.query(Project).filter(Project.id == project_id).first()

        # 添加多个文档
        doc1 = ProjectDocument(
            project_id=project.id,
            filename="doc1.txt",
            original_filename="doc1.txt",
            file_path="/fake/path/doc1.txt",
            file_type="text/plain",
            file_size=512,
            status="completed",
            text_content="2023年1月1日，文档1事件1。2023年2月1日，文档1事件2。"
        )
        doc2 = ProjectDocument(
            project_id=project.id,
            filename="doc2.txt",
            original_filename="doc2.txt",
            file_path="/fake/path/doc2.txt",
            file_type="text/plain",
            file_size=512,
            status="completed",
            text_content="2023年3月1日，文档2事件。"
        )
        db.add_all([doc1, doc2])
        db.commit()

        # 按文档分组
        response = client.get(
            f"/api/timeline/projects/{project_id}/events/grouped",
            headers=auth_headers,
            params={"group_by": "document"}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证分组
        groups = {g["key"]: g for g in data["groups"]}
        assert "doc1.txt" in groups
        assert "doc2.txt" in groups

        assert groups["doc1.txt"]["count"] == 2
        assert groups["doc2.txt"]["count"] == 1

    def test_timeline_date_extraction_formats(self, client, auth_headers, db):
        """测试多种日期格式的提取"""
        from app.models.project import Project, ProjectDocument

        # 创建项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={
                "name": "Date Format Test Project",
                "description": "Testing various date formats"
            }
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # 获取项目对象
        project = db.query(Project).filter(Project.id == project_id).first()

        # 添加包含多种日期格式的文档
        doc = ProjectDocument(
            project_id=project.id,
            filename="date_formats.txt",
            original_filename="date_formats.txt",
            file_path="/fake/path/date_formats.txt",
            file_type="text/plain",
            file_size=2048,
            status="completed",
            text_content="""
            中文格式：2023年5月20日，事件A发生。
            仅年月：2023年6月，事件B发生。
            仅年份：2022年，事件C发生。
            横线格式：2023-07-15，事件D发生。
            斜线格式：2023/08/25，事件E发生。
            """
        )
        db.add(doc)
        db.commit()

        # 获取时间线
        response = client.get(
            f"/api/timeline/projects/{project_id}/events",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 应该提取到5个事件
        assert len(data["events"]) >= 5

        # 验证不同格式的日期
        dates = [event["date"] for event in data["events"]]
        assert "2023-05-20" in dates  # 中文格式
        assert "2023-06" in dates      # 仅年月
        assert "2022" in dates          # 仅年份
        assert "2023-07-15" in dates   # 横线格式
        assert "2023-08-25" in dates   # 斜线格式

    def test_timeline_empty_content(self, client, auth_headers, db):
        """测试空文档内容"""
        from app.models.project import Project, ProjectDocument

        # 创建项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={
                "name": "Empty Content Project",
                "description": "Project with empty documents"
            }
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # 获取项目对象
        project = db.query(Project).filter(Project.id == project_id).first()

        # 添加空文档
        doc = ProjectDocument(
            project_id=project.id,
            filename="empty.txt",
            original_filename="empty.txt",
            file_path="/fake/path/empty.txt",
            file_type="text/plain",
            file_size=0,
            status="completed",
            text_content=""
        )
        db.add(doc)
        db.commit()

        # 获取时间线
        response = client.get(
            f"/api/timeline/projects/{project_id}/events",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["statistics"]["total_events"] == 0

    def test_timeline_with_pending_documents(self, client, auth_headers, db):
        """测试仅处理已完成状态的文档"""
        from app.models.project import Project, ProjectDocument

        # 创建项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={
                "name": "Pending Docs Project",
                "description": "Project with pending documents"
            }
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # 获取项目对象
        project = db.query(Project).filter(Project.id == project_id).first()

        # 添加已完成文档
        doc_completed = ProjectDocument(
            project_id=project.id,
            filename="completed.txt",
            original_filename="completed.txt",
            file_path="/fake/path/completed.txt",
            file_type="text/plain",
            file_size=512,
            status="completed",
            text_content="2023年1月1日，已完成的事件。"
        )

        # 添加处理中文档
        doc_pending = ProjectDocument(
            project_id=project.id,
            filename="pending.txt",
            original_filename="pending.txt",
            file_path="/fake/path/pending.txt",
            file_type="text/plain",
            file_size=512,
            status="processing",
            text_content="2023年2月1日，处理中的事件。"
        )

        db.add_all([doc_completed, doc_pending])
        db.commit()

        # 获取时间线
        response = client.get(
            f"/api/timeline/projects/{project_id}/events",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 只应该有1个事件（来自已完成的文档）
        assert len(data["events"]) == 1
        assert "已完成的事件" in data["events"][0]["description"]
        assert data["events"][0]["date"] == "2023-01-01"

    def test_grouped_timeline_empty_project(self, client, auth_headers):
        """测试空项目的分组时间线"""
        # 创建空项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={
                "name": "Empty Grouped Project",
                "description": "Empty project for grouped timeline"
            }
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # 获取分组时间线
        response = client.get(
            f"/api/timeline/projects/{project_id}/events/grouped",
            headers=auth_headers,
            params={"group_by": "year"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["groups"] == []
        assert data["statistics"]["total_events"] == 0


class TestTimelineExtractor:
    """时间线提取器单元测试"""

    def test_extractor_chinese_date_format(self):
        """测试中文日期格式提取"""
        from app.api.timeline import extractor

        text = "2023年5月20日，公司成立大会在北京举行。"
        events = extractor.extract_events(text, 1, "test.txt")

        assert len(events) == 1
        assert events[0]["date"] == "2023-05-20"
        assert "公司成立" in events[0]["description"]

    def test_extractor_english_date_format(self):
        """测试英文日期格式提取"""
        from app.api.timeline import extractor

        text = "On 2023-05-20, the company was founded."
        events = extractor.extract_events(text, 1, "test.txt")

        assert len(events) == 1
        assert events[0]["date"] == "2023-05-20"

    def test_extractor_multiple_events(self):
        """测试提取多个事件"""
        from app.api.timeline import extractor

        text = """
        2023年1月1日，项目启动。
        2023年6月15日，完成开发。
        2023年12月31日，正式发布。
        """
        events = extractor.extract_events(text, 1, "test.txt")

        assert len(events) == 3
        assert events[0]["date"] == "2023-01-01"
        assert events[1]["date"] == "2023-06-15"
        assert events[2]["date"] == "2023-12-31"

    def test_extractor_year_only(self):
        """测试仅年份提取"""
        from app.api.timeline import extractor

        text = "2022年，公司开始运营。"
        events = extractor.extract_events(text, 1, "test.txt")

        assert len(events) == 1
        assert events[0]["date"] == "2022"

    def test_extractor_ignores_short_sentences(self):
        """测试忽略短句"""
        from app.api.timeline import extractor

        # 短句（少于10个字符）应该被忽略
        text = "2023年1月1日。2023年2月1日，这是一个足够长的句子会被提取。"
        events = extractor.extract_events(text, 1, "test.txt")

        # 第一个句子太短被忽略，只应该提取第二个事件
        assert len(events) == 1
        assert "足够长的句子" in events[0]["description"]
