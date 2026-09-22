"""
WebSocket使用示例
Phase 3.7 - WebSocket实时通知系统

示例场景：
1. 基础WebSocket连接
2. 房间管理（项目级、会话级）
3. 事件发射与监听
4. Deep RAG进度推送
5. 文档处理进度推送
6. 批处理任务监控
7. 系统通知广播

作者：FieldMind Team
创建时间：2026-08-09
"""

import asyncio
import websockets
import json
import requests
from datetime import datetime


# ============ 示例1: 基础WebSocket连接 ============

async def example_01_basic_connection():
    """示例1: 建立基础WebSocket连接"""
    print("\n" + "=" * 60)
    print("示例1: 基础WebSocket连接")
    print("=" * 60)

    uri = "ws://localhost:8000/api/websocket/ws/client_001?user_id=user_123&project_id=1"

    async with websockets.connect(uri) as websocket:
        # 接收欢迎消息
        welcome = await websocket.recv()
        print(f"✅ 连接成功: {welcome}")

        # 发送心跳
        await websocket.send(json.dumps({
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }))

        # 接收心跳响应
        pong = await websocket.recv()
        print(f"💓 心跳响应: {pong}")


# ============ 示例2: 房间管理 ============

async def example_02_room_management():
    """示例2: 加入和离开房间"""
    print("\n" + "=" * 60)
    print("示例2: 房间管理")
    print("=" * 60)

    uri = "ws://localhost:8000/api/websocket/ws/client_002"

    async with websockets.connect(uri) as websocket:
        # 接收欢迎消息
        await websocket.recv()

        # 加入项目房间
        await websocket.send(json.dumps({
            "type": "join_room",
            "room_id": "project_1"
        }))

        response = await websocket.recv()
        print(f"✅ 加入房间: {response}")

        # 加入会话房间
        await websocket.send(json.dumps({
            "type": "join_room",
            "room_id": "session_abc123"
        }))

        response = await websocket.recv()
        print(f"✅ 加入会话: {response}")

        # 等待房间消息
        print("📡 等待房间消息...")
        await asyncio.sleep(5)

        # 离开房间
        await websocket.send(json.dumps({
            "type": "leave_room",
            "room_id": "project_1"
        }))

        response = await websocket.recv()
        print(f"👋 离开房间: {response}")


# ============ 示例3: HTTP广播测试 ============

def example_03_http_broadcast():
    """示例3: 通过HTTP端点广播消息"""
    print("\n" + "=" * 60)
    print("示例3: HTTP广播消息")
    print("=" * 60)

    # 全局广播
    response = requests.post(
        "http://localhost:8000/api/websocket/broadcast",
        json={
            "event": "system.notification",
            "data": {
                "title": "系统维护通知",
                "message": "系统将于今晚22:00进行维护",
                "level": "warning"
            }
        }
    )

    print(f"✅ 全局广播: {response.json()}")

    # 房间广播
    response = requests.post(
        "http://localhost:8000/api/websocket/rooms/project_1/broadcast",
        json={
            "event": "project.update",
            "data": {
                "project_id": 1,
                "message": "项目数据已更新"
            }
        }
    )

    print(f"✅ 房间广播: {response.json()}")


# ============ 示例4: 事件发射 ============

def example_04_emit_events():
    """示例4: 发射自定义事件"""
    print("\n" + "=" * 60)
    print("示例4: 事件发射")
    print("=" * 60)

    # 发射Deep RAG事件
    response = requests.post(
        "http://localhost:8000/api/websocket/events/emit",
        json={
            "event_type": "deep_rag.query.start",
            "data": {
                "session_id": "test_session_001",
                "query": "傈僳族的民歌特点",
                "user_id": "user_123"
            }
        }
    )

    print(f"✅ Deep RAG事件: {response.json()}")

    # 发射文档处理事件
    response = requests.post(
        "http://localhost:8000/api/websocket/events/emit",
        json={
            "event_type": "document.process.progress",
            "data": {
                "project_id": 1,
                "document_id": 42,
                "progress": 65,
                "stage": "embedding",
                "message": "正在生成向量嵌入..."
            }
        }
    )

    print(f"✅ 文档处理事件: {response.json()}")


# ============ 示例5: Deep RAG进度监控 ============

async def example_05_deep_rag_monitoring():
    """示例5: 监控Deep RAG查询进度"""
    print("\n" + "=" * 60)
    print("示例5: Deep RAG进度监控")
    print("=" * 60)

    session_id = "monitor_session_001"
    uri = f"ws://localhost:8000/api/websocket/ws/client_deep_rag?session_id={session_id}"

    async with websockets.connect(uri) as websocket:
        # 接收欢迎消息
        await websocket.recv()

        # 加入会话房间
        await websocket.send(json.dumps({
            "type": "join_room",
            "room_id": f"session_{session_id}"
        }))
        await websocket.recv()

        print(f"📡 监听会话 {session_id} 的事件...")

        # 在另一个线程/进程中，发起Deep RAG查询
        # 这里模拟发射事件
        import threading

        def trigger_deep_rag():
            time.sleep(1)
            # 查询开始
            requests.post(
                "http://localhost:8000/api/websocket/events/emit",
                json={
                    "event_type": "deep_rag.query.start",
                    "data": {"session_id": session_id, "query": "测试问题"}
                }
            )

            time.sleep(1)
            # 检索开始
            requests.post(
                "http://localhost:8000/api/websocket/events/emit",
                json={
                    "event_type": "deep_rag.retrieve.start",
                    "data": {"session_id": session_id, "sources": 10}
                }
            )

            time.sleep(1)
            # 检索完成
            requests.post(
                "http://localhost:8000/api/websocket/events/emit",
                json={
                    "event_type": "deep_rag.retrieve.complete",
                    "data": {"session_id": session_id, "results_count": 25}
                }
            )

            time.sleep(1)
            # LLM生成开始
            requests.post(
                "http://localhost:8000/api/websocket/events/emit",
                json={
                    "event_type": "deep_rag.llm.start",
                    "data": {"session_id": session_id, "model": "anthropic"}
                }
            )

            time.sleep(2)
            # 查询完成
            requests.post(
                "http://localhost:8000/api/websocket/events/emit",
                json={
                    "event_type": "deep_rag.query.complete",
                    "data": {
                        "session_id": session_id,
                        "answer": "这是生成的答案...",
                        "confidence": 0.89
                    }
                }
            )

        threading.Thread(target=trigger_deep_rag).start()

        # 接收事件
        import time
        for i in range(10):
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(message)
                event_type = data.get('event', 'unknown')
                print(f"📨 收到事件: {event_type}")
                print(f"   数据: {json.dumps(data.get('data', {}), ensure_ascii=False, indent=2)}")
            except asyncio.TimeoutError:
                pass


# ============ 示例6: 文档处理进度监控 ============

async def example_06_document_processing_monitoring():
    """示例6: 监控文档处理进度"""
    print("\n" + "=" * 60)
    print("示例6: 文档处理进度监控")
    print("=" * 60)

    project_id = 1
    uri = f"ws://localhost:8000/api/websocket/ws/client_doc_monitor?project_id={project_id}"

    async with websockets.connect(uri) as websocket:
        # 接收欢迎消息
        await websocket.recv()

        # 加入项目房间
        await websocket.send(json.dumps({
            "type": "join_room",
            "room_id": f"project_{project_id}"
        }))
        await websocket.recv()

        print(f"📡 监听项目 {project_id} 的文档处理事件...")

        # 模拟文档处理流程
        import threading

        def trigger_document_processing():
            import time
            time.sleep(1)

            stages = [
                ("upload.start", {"filename": "田野调查报告.pdf", "size": 1024000}),
                ("upload.progress", {"progress": 30}),
                ("upload.progress", {"progress": 60}),
                ("upload.progress", {"progress": 100}),
                ("upload.complete", {"document_id": 123}),
                ("process.start", {"stage": "parsing"}),
                ("process.progress", {"progress": 25, "stage": "parsing"}),
                ("process.progress", {"progress": 50, "stage": "chunking"}),
                ("process.progress", {"progress": 75, "stage": "embedding"}),
                ("process.complete", {"chunks_count": 42, "duration": 5.2}),
            ]

            for event_suffix, data in stages:
                data['project_id'] = project_id
                requests.post(
                    "http://localhost:8000/api/websocket/events/emit",
                    json={
                        "event_type": f"document.{event_suffix}",
                        "data": data
                    }
                )
                time.sleep(0.8)

        threading.Thread(target=trigger_document_processing).start()

        # 接收事件
        for i in range(15):
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(message)
                event_type = data.get('event', 'unknown')
                event_data = data.get('data', {})

                if 'progress' in event_data:
                    print(f"📊 进度更新: {event_data['progress']}% - {event_data.get('stage', '')}")
                else:
                    print(f"📨 事件: {event_type}")

            except asyncio.TimeoutError:
                pass


# ============ 示例7: 获取统计信息 ============

def example_07_get_statistics():
    """示例7: 获取WebSocket统计信息"""
    print("\n" + "=" * 60)
    print("示例7: 获取统计信息")
    print("=" * 60)

    # WebSocket统计
    response = requests.get("http://localhost:8000/api/websocket/stats")
    stats = response.json()['data']
    print(f"📊 WebSocket统计:")
    print(f"   活跃连接: {stats['active_connections']}")
    print(f"   房间数: {stats['total_rooms']}")
    print(f"   总连接数: {stats['stats']['total_connections']}")
    print(f"   总消息数: {stats['stats']['total_messages']}")

    # 事件统计
    response = requests.get("http://localhost:8000/api/websocket/events/stats")
    event_stats = response.json()['data']
    print(f"\n📊 事件统计:")
    print(f"   总事件数: {event_stats['total_events']}")
    print(f"   监听器数: {event_stats['total_listeners']}")
    print(f"   事件类型: {list(event_stats['events_by_type'].keys())[:5]}")

    # 事件历史
    response = requests.get("http://localhost:8000/api/websocket/events/history?limit=5")
    history = response.json()['data']
    print(f"\n📜 最近5个事件:")
    for event in history:
        print(f"   - {event['event']} @ {event['timestamp']}")


# ============ 主函数 ============

async def run_all_examples():
    """运行所有示例"""
    print("=" * 60)
    print("WebSocket实时通知系统 - 使用示例")
    print("=" * 60)

    # 示例1: 基础连接
    # await example_01_basic_connection()

    # 示例2: 房间管理
    # await example_02_room_management()

    # 示例3: HTTP广播（同步）
    # example_03_http_broadcast()

    # 示例4: 事件发射（同步）
    # example_04_emit_events()

    # 示例5: Deep RAG监控
    # await example_05_deep_rag_monitoring()

    # 示例6: 文档处理监控
    # await example_06_document_processing_monitoring()

    # 示例7: 统计信息（同步）
    example_07_get_statistics()


if __name__ == "__main__":
    # 运行示例
    # 注意：需要先启动FastAPI服务器
    # uvicorn app.main:app --reload

    import time

    print("\n⚠️  请确保FastAPI服务器已启动: uvicorn app.main:app --reload")
    print("按Enter继续...")
    # input()

    asyncio.run(run_all_examples())
