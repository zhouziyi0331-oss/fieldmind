"""
监控系统测试脚本

测试 Prometheus 指标收集和导出功能
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.monitoring import (
    metrics_manager,
    track_request,
    track_processing,
    track_database_operation,
    track_ai_operation,
    track_vector_operation,
    track_graph_operation,
    record_error,
)
from app.core.config import ErrorCode
import time


def log(msg):
    """简单的日志函数"""
    print(msg, flush=True)


def test_http_metrics():
    """测试 HTTP 请求指标"""
    log("=" * 60)
    log("测试 1: HTTP 请求指标")
    log("=" * 60)

    # 模拟成功的请求
    with track_request("GET", "/api/documents") as tracker:
        time.sleep(0.1)
        tracker.set_status(200)

    # 模拟失败的请求
    try:
        with track_request("POST", "/api/upload") as tracker:
            time.sleep(0.05)
            tracker.set_status(500)
            raise ValueError("模拟上传失败")
    except ValueError:
        pass

    log("✅ HTTP 请求指标追踪成功")


def test_processing_metrics():
    """测试文档处理指标"""
    log("=" * 60)
    log("测试 2: 文档处理指标")
    log("=" * 60)

    # 模拟多模态处理
    with track_processing("multimodal", "pdf") as tracker:
        time.sleep(0.2)
        tracker.set_status("success")

    # 模拟语义处理
    with track_processing("semantic", "video") as tracker:
        time.sleep(0.15)
        tracker.set_status("success")

    # 模拟失败的处理
    try:
        with track_processing("network", "audio") as tracker:
            time.sleep(0.1)
            tracker.set_status("failure")
            raise Exception("模拟处理失败")
    except Exception:
        pass

    log("✅ 文档处理指标追踪成功")


def test_database_metrics():
    """测试数据库操作指标"""
    log("=" * 60)
    log("测试 3: 数据库操作指标")
    log("=" * 60)

    # 模拟查询操作
    with track_database_operation("query", "documents") as tracker:
        time.sleep(0.05)
        tracker.set_status("success")

    # 模拟插入操作
    with track_database_operation("insert", "chunks") as tracker:
        time.sleep(0.03)
        tracker.set_status("success")

    log("✅ 数据库操作指标追踪成功")


def test_ai_metrics():
    """测试 AI 服务指标"""
    log("=" * 60)
    log("测试 4: AI 服务指标")
    log("=" * 60)

    # 模拟 OpenAI 聊天请求
    with track_ai_operation("openai", "gpt-4", "chat") as tracker:
        time.sleep(0.3)
        tracker.set_status("success")
        tracker.set_tokens(input_tokens=150, output_tokens=200)

    # 模拟 embedding 生成
    with track_ai_operation("openai", "text-embedding-3-large", "embedding") as tracker:
        time.sleep(0.1)
        tracker.set_status("success")
        tracker.set_tokens(input_tokens=500)

    log("✅ AI 服务指标追踪成功")


def test_vector_metrics():
    """测试向量数据库指标"""
    log("=" * 60)
    log("测试 5: 向量数据库指标")
    log("=" * 60)

    # 模拟向量添加
    with track_vector_operation("add", "documents") as tracker:
        time.sleep(0.08)
        tracker.set_status("success")

    # 模拟向量查询
    with track_vector_operation("query", "documents") as tracker:
        time.sleep(0.12)
        tracker.set_status("success")

    log("✅ 向量数据库指标追踪成功")


def test_graph_metrics():
    """测试图数据库指标"""
    log("=" * 60)
    log("测试 6: 图数据库指标")
    log("=" * 60)

    # 模拟创建节点
    with track_graph_operation("create_node", "Document") as tracker:
        time.sleep(0.06)
        tracker.set_status("success")

    # 模拟创建关系
    with track_graph_operation("create_rel", "REFERENCES") as tracker:
        time.sleep(0.04)
        tracker.set_status("success")

    log("✅ 图数据库指标追踪成功")


def test_error_recording():
    """测试错误记录"""
    log("=" * 60)
    log("测试 7: 错误记录")
    log("=" * 60)

    # 记录各种错误
    record_error(
        error_code=ErrorCode.DATABASE_CONNECTION_ERROR,
        error_type="DatabaseError",
        component="multimodal_processor",
        details={"message": "连接超时"}
    )

    record_error(
        error_code=ErrorCode.FILE_TOO_LARGE,
        error_type="ValueError",
        component="file_upload",
        details={"file_size": "600MB"}
    )

    log("✅ 错误记录成功")


def test_metrics_export():
    """测试指标导出"""
    log("=" * 60)
    log("测试 8: 指标导出")
    log("=" * 60)

    # 获取所有指标
    metrics_output = metrics_manager.get_metrics()

    # 验证输出格式
    assert isinstance(metrics_output, bytes), "指标输出应该是 bytes 类型"
    assert len(metrics_output) > 0, "指标输出不应为空"

    # 解码并显示前几行
    metrics_text = metrics_output.decode('utf-8')
    lines = metrics_text.split('\n')[:20]

    log("指标导出示例（前20行）：")
    log("-" * 60)
    for line in lines:
        if line and not line.startswith('#'):
            log(f"  {line}")

    log("-" * 60)
    log(f"✅ 指标导出成功，共 {len(metrics_text.split(chr(10)))} 行")


def test_system_metrics():
    """测试系统资源指标"""
    log("=" * 60)
    log("测试 9: 系统资源指标")
    log("=" * 60)

    # 更新系统指标
    metrics_manager.update_system_metrics()

    # 检查指标值
    cpu_sample = metrics_manager.system_cpu_usage_percent._value.get()
    memory_sample = metrics_manager.system_memory_usage_percent._value.get()

    log(f"  CPU 使用率: {cpu_sample:.2f}%")
    log(f"  内存使用率: {memory_sample:.2f}%")

    log("✅ 系统资源指标收集成功")


def main():
    """主测试函数"""
    log("🚀 开始测试监控系统...")
    log("")

    try:
        # 运行所有测试
        test_http_metrics()
        test_processing_metrics()
        test_database_metrics()
        test_ai_metrics()
        test_vector_metrics()
        test_graph_metrics()
        test_error_recording()
        test_system_metrics()
        test_metrics_export()

        log("")
        log("=" * 60)
        log("🎉 所有测试通过！")
        log("=" * 60)
        log("")
        log("📊 监控系统功能验证：")
        log("  ✅ HTTP 请求指标追踪")
        log("  ✅ 文档处理指标追踪")
        log("  ✅ 数据库操作指标追踪")
        log("  ✅ AI 服务指标追踪")
        log("  ✅ 向量数据库指标追踪")
        log("  ✅ 图数据库指标追踪")
        log("  ✅ 错误记录")
        log("  ✅ 系统资源监控")
        log("  ✅ Prometheus 格式导出")
        log("")
        log("🔗 启动服务后访问 http://localhost:8000/metrics 查看实时指标")
        log("")

        return True

    except Exception as e:
        log(f"❌ 测试失败: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
