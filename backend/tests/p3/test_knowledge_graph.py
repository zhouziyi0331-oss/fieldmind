"""
交互式知识图谱测试
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.knowledge_graph import (
    InteractiveKnowledgeGraph,
    GraphVisualizationService,
    NodeType,
    RelationType
)


class TestInteractiveKnowledgeGraph:
    """测试交互式知识图谱"""

    def test_add_node(self):
        """测试添加节点"""
        graph = InteractiveKnowledgeGraph()
        node = graph.add_node(
            node_id="node1",
            label="Python",
            node_type=NodeType.CONCEPT,
            properties={"description": "Programming language"}
        )
        assert node.id == "node1"
        assert node.label == "Python"
        assert node.node_type == NodeType.CONCEPT

    def test_update_node(self):
        """测试更新节点"""
        graph = InteractiveKnowledgeGraph()
        graph.add_node("node1", "Python", NodeType.CONCEPT)

        updated = graph.update_node(
            "node1",
            label="Python 3",
            properties={"version": "3.11"}
        )
        assert updated.label == "Python 3"
        assert updated.properties["version"] == "3.11"

    def test_remove_node(self):
        """测试删除节点"""
        graph = InteractiveKnowledgeGraph()
        graph.add_node("node1", "Python", NodeType.CONCEPT)

        success = graph.remove_node("node1")
        assert success == True
        assert graph.get_node("node1") is None

    def test_add_edge(self):
        """测试添加边"""
        graph = InteractiveKnowledgeGraph()
        graph.add_node("node1", "Python", NodeType.CONCEPT)
        graph.add_node("node2", "FastAPI", NodeType.CONCEPT)

        edge = graph.add_edge(
            edge_id="edge1",
            source_id="node1",
            target_id="node2",
            relation_type=RelationType.RELATED_TO,
            weight=0.8
        )
        assert edge.source_id == "node1"
        assert edge.target_id == "node2"
        assert edge.weight == 0.8

    def test_remove_edge(self):
        """测试删除边"""
        graph = InteractiveKnowledgeGraph()
        graph.add_node("node1", "Python", NodeType.CONCEPT)
        graph.add_node("node2", "FastAPI", NodeType.CONCEPT)
        graph.add_edge("edge1", "node1", "node2", RelationType.RELATED_TO)

        success = graph.remove_edge("edge1")
        assert success == True
        assert graph.get_edge("edge1") is None

    def test_get_neighbors(self):
        """测试获取邻居节点"""
        graph = InteractiveKnowledgeGraph()
        graph.add_node("node1", "Python", NodeType.CONCEPT)
        graph.add_node("node2", "FastAPI", NodeType.CONCEPT)
        graph.add_node("node3", "Django", NodeType.CONCEPT)

        graph.add_edge("edge1", "node1", "node2", RelationType.RELATED_TO)
        graph.add_edge("edge2", "node1", "node3", RelationType.RELATED_TO)

        neighbors = graph.get_neighbors("node1", direction="outgoing")
        assert len(neighbors) == 2
        neighbor_ids = [n.id for n in neighbors]
        assert "node2" in neighbor_ids
        assert "node3" in neighbor_ids

    def test_get_subgraph(self):
        """测试获取子图"""
        graph = InteractiveKnowledgeGraph()

        # 创建一个小图
        graph.add_node("node1", "Python", NodeType.CONCEPT)
        graph.add_node("node2", "FastAPI", NodeType.CONCEPT)
        graph.add_node("node3", "Django", NodeType.CONCEPT)
        graph.add_node("node4", "Flask", NodeType.CONCEPT)

        graph.add_edge("edge1", "node1", "node2", RelationType.RELATED_TO)
        graph.add_edge("edge2", "node1", "node3", RelationType.RELATED_TO)
        graph.add_edge("edge3", "node2", "node4", RelationType.RELATED_TO)

        nodes, edges = graph.get_subgraph("node1", depth=2)

        assert len(nodes) == 4
        assert len(edges) == 3

    def test_find_path(self):
        """测试寻找路径"""
        graph = InteractiveKnowledgeGraph()

        # 创建路径
        graph.add_node("node1", "A", NodeType.CONCEPT)
        graph.add_node("node2", "B", NodeType.CONCEPT)
        graph.add_node("node3", "C", NodeType.CONCEPT)

        graph.add_edge("edge1", "node1", "node2", RelationType.RELATED_TO)
        graph.add_edge("edge2", "node2", "node3", RelationType.RELATED_TO)

        path = graph.find_path("node1", "node3")
        assert path == ["node1", "node2", "node3"]

    def test_find_path_not_found(self):
        """测试寻找不存在的路径"""
        graph = InteractiveKnowledgeGraph()

        graph.add_node("node1", "A", NodeType.CONCEPT)
        graph.add_node("node2", "B", NodeType.CONCEPT)

        path = graph.find_path("node1", "node2")
        assert path is None

    def test_statistics(self):
        """测试统计信息"""
        graph = InteractiveKnowledgeGraph()

        graph.add_node("node1", "Python", NodeType.CONCEPT)
        graph.add_node("node2", "FastAPI", NodeType.CONCEPT)
        graph.add_node("doc1", "Document", NodeType.DOCUMENT)

        graph.add_edge("edge1", "node1", "node2", RelationType.RELATED_TO)

        stats = graph.get_statistics()
        assert stats["total_nodes"] == 3
        assert stats["total_edges"] == 1
        assert stats["nodes_by_type"]["concept"] == 2
        assert stats["nodes_by_type"]["document"] == 1

    def test_export_import(self):
        """测试导出和导入"""
        graph = InteractiveKnowledgeGraph()

        # 创建图
        graph.add_node("node1", "Python", NodeType.CONCEPT)
        graph.add_node("node2", "FastAPI", NodeType.CONCEPT)
        graph.add_edge("edge1", "node1", "node2", RelationType.RELATED_TO)

        # 导出
        data = graph.export_graph()
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

        # 导入到新图
        new_graph = InteractiveKnowledgeGraph()
        success = new_graph.import_graph(data)
        assert success == True
        assert len(new_graph.nodes) == 2
        assert len(new_graph.edges) == 1


class TestGraphVisualizationService:
    """测试图可视化服务"""

    def test_generate_visualization_data(self):
        """测试生成可视化数据"""
        graph = InteractiveKnowledgeGraph()
        graph.add_node("node1", "Python", NodeType.CONCEPT)
        graph.add_node("node2", "FastAPI", NodeType.CONCEPT)
        graph.add_edge("edge1", "node1", "node2", RelationType.RELATED_TO)

        viz_service = GraphVisualizationService(graph)
        data = viz_service.generate_visualization_data()

        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

        # 验证节点有位置信息
        node = data["nodes"][0]
        assert "x" in node
        assert "y" in node
        assert "color" in node
        assert "size" in node

    def test_force_layout(self):
        """测试力导向布局"""
        graph = InteractiveKnowledgeGraph()
        graph.add_node("node1", "A", NodeType.CONCEPT)
        graph.add_node("node2", "B", NodeType.CONCEPT)
        graph.add_node("node3", "C", NodeType.CONCEPT)

        graph.add_edge("edge1", "node1", "node2", RelationType.RELATED_TO)
        graph.add_edge("edge2", "node2", "node3", RelationType.RELATED_TO)

        viz_service = GraphVisualizationService(graph)
        data = viz_service.generate_visualization_data(layout="force")

        assert data["layout"] == "force"
        assert len(data["nodes"]) == 3

    def test_circular_layout(self):
        """测试圆形布局"""
        graph = InteractiveKnowledgeGraph()
        for i in range(5):
            graph.add_node(f"node{i}", f"Node {i}", NodeType.CONCEPT)

        viz_service = GraphVisualizationService(graph)
        data = viz_service.generate_visualization_data(layout="circular")

        assert data["layout"] == "circular"
        assert len(data["nodes"]) == 5

    def test_hierarchical_layout(self):
        """测试层次布局"""
        graph = InteractiveKnowledgeGraph()
        graph.add_node("root", "Root", NodeType.CONCEPT)
        graph.add_node("child1", "Child 1", NodeType.CONCEPT)
        graph.add_node("child2", "Child 2", NodeType.CONCEPT)

        graph.add_edge("edge1", "root", "child1", RelationType.PART_OF)
        graph.add_edge("edge2", "root", "child2", RelationType.PART_OF)

        viz_service = GraphVisualizationService(graph)
        data = viz_service.generate_visualization_data(layout="hierarchical")

        assert data["layout"] == "hierarchical"
        assert len(data["nodes"]) == 3

    def test_get_node_details(self):
        """测试获取节点详情"""
        graph = InteractiveKnowledgeGraph()
        graph.add_node("node1", "Python", NodeType.CONCEPT)
        graph.add_node("node2", "FastAPI", NodeType.CONCEPT)
        graph.add_edge("edge1", "node1", "node2", RelationType.RELATED_TO)

        viz_service = GraphVisualizationService(graph)
        details = viz_service.get_node_details("node1")

        assert details is not None
        assert "node" in details
        assert "neighbors" in details
        assert "outgoing_edges" in details
        assert "statistics" in details

    def test_search_nodes(self):
        """测试搜索节点"""
        graph = InteractiveKnowledgeGraph()
        graph.add_node("node1", "Python Programming", NodeType.CONCEPT)
        graph.add_node("node2", "JavaScript", NodeType.CONCEPT)
        graph.add_node("node3", "Python Guide", NodeType.DOCUMENT)

        viz_service = GraphVisualizationService(graph)
        results = viz_service.search_nodes("python")

        assert len(results) == 2
        assert results[0]["score"] >= results[1]["score"]

    def test_get_shortest_path(self):
        """测试获取最短路径"""
        graph = InteractiveKnowledgeGraph()
        graph.add_node("node1", "A", NodeType.CONCEPT)
        graph.add_node("node2", "B", NodeType.CONCEPT)
        graph.add_node("node3", "C", NodeType.CONCEPT)

        graph.add_edge("edge1", "node1", "node2", RelationType.RELATED_TO)
        graph.add_edge("edge2", "node2", "node3", RelationType.RELATED_TO)

        viz_service = GraphVisualizationService(graph)
        path = viz_service.get_shortest_path("node1", "node3")

        assert path is not None
        assert len(path["nodes"]) == 3
        assert len(path["edges"]) == 2
        assert path["length"] == 2


def test_integration_knowledge_graph():
    """集成测试：完整的知识图谱场景"""
    graph = InteractiveKnowledgeGraph()

    # 构建技术栈图谱
    graph.add_node("python", "Python", NodeType.CONCEPT)
    graph.add_node("fastapi", "FastAPI", NodeType.CONCEPT)
    graph.add_node("django", "Django", NodeType.CONCEPT)
    graph.add_node("postgresql", "PostgreSQL", NodeType.CONCEPT)
    graph.add_node("redis", "Redis", NodeType.CONCEPT)

    graph.add_edge("e1", "fastapi", "python", RelationType.DEPENDS_ON)
    graph.add_edge("e2", "django", "python", RelationType.DEPENDS_ON)
    graph.add_edge("e3", "fastapi", "postgresql", RelationType.RELATED_TO)
    graph.add_edge("e4", "fastapi", "redis", RelationType.RELATED_TO)

    # 验证图结构
    assert len(graph.nodes) == 5
    assert len(graph.edges) == 4

    # 测试邻居查询
    python_neighbors = graph.get_neighbors("python", direction="incoming")
    assert len(python_neighbors) == 2

    # 测试子图
    nodes, edges = graph.get_subgraph("fastapi", depth=2)
    assert len(nodes) >= 3

    # 测试路径
    path = graph.find_path("fastapi", "python")
    assert path is not None
    assert len(path) == 2

    # 测试可视化
    viz_service = GraphVisualizationService(graph)
    viz_data = viz_service.generate_visualization_data(layout="force")
    assert len(viz_data["nodes"]) == 5
    assert len(viz_data["edges"]) == 4

    # 测试搜索
    results = viz_service.search_nodes("fast")
    assert len(results) == 1
    assert results[0]["node"]["id"] == "fastapi"


if __name__ == "__main__":
    print("Running Interactive Knowledge Graph tests...")

    print("\n=== Testing InteractiveKnowledgeGraph ===")
    test_graph = TestInteractiveKnowledgeGraph()
    test_graph.test_add_node()
    test_graph.test_update_node()
    test_graph.test_remove_node()
    test_graph.test_add_edge()
    test_graph.test_remove_edge()
    test_graph.test_get_neighbors()
    test_graph.test_get_subgraph()
    test_graph.test_find_path()
    test_graph.test_find_path_not_found()
    test_graph.test_statistics()
    test_graph.test_export_import()
    print("✓ InteractiveKnowledgeGraph tests passed")

    print("\n=== Testing GraphVisualizationService ===")
    test_viz = TestGraphVisualizationService()
    test_viz.test_generate_visualization_data()
    test_viz.test_force_layout()
    test_viz.test_circular_layout()
    test_viz.test_hierarchical_layout()
    test_viz.test_get_node_details()
    test_viz.test_search_nodes()
    test_viz.test_get_shortest_path()
    print("✓ GraphVisualizationService tests passed")

    print("\n=== Running Integration Tests ===")
    test_integration_knowledge_graph()
    print("✓ Integration tests passed")

    print("\n✅ All knowledge graph tests passed successfully!")
