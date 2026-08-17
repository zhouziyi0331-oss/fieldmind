-- 清理旧的测试数据
DELETE FROM relations WHERE relation_id LIKE 'test_%';
DELETE FROM entities WHERE entity_id LIKE 'test_%';
DELETE FROM knowledge_graphs WHERE id > 0;

-- 创建测试实体
INSERT INTO entities (entity_id, name, entity_type, project_id, mentions, context, confidence) VALUES
('test_entity_1', '张三', '人物', 1, 5, '张三是一位研究人员', 0.9),
('test_entity_2', '北京大学', '机构', 1, 3, '北京大学是一所知名大学', 0.9),
('test_entity_3', '人工智能', '文化概念', 1, 8, '人工智能是计算机科学的一个分支', 0.9),
('test_entity_4', '李四', '人物', 1, 4, '李四是另一位研究人员', 0.9),
('test_entity_5', '上海', '地名', 1, 6, '上海是中国的一个大城市', 0.9),
('test_entity_6', '深度学习', '文化概念', 1, 7, '深度学习是机器学习的一个分支', 0.9);

-- 创建测试关系
INSERT INTO relations (relation_id, subject_entity_id, relation_type, object_entity_id, context, confidence) VALUES
('test_rel_1', 'test_entity_1', '工作于', 'test_entity_2', '张三在北京大学工作', 0.85),
('test_rel_2', 'test_entity_1', '研究', 'test_entity_3', '张三研究人工智能', 0.85),
('test_rel_3', 'test_entity_4', '位于', 'test_entity_5', '李四位于上海', 0.85),
('test_rel_4', 'test_entity_4', '研究', 'test_entity_6', '李四研究深度学习', 0.85),
('test_rel_5', 'test_entity_3', '包含', 'test_entity_6', '人工智能包含深度学习', 0.85);

-- 创建知识图谱记录
INSERT INTO knowledge_graphs (project_id, graph_data, entity_count, relation_count, created_at) VALUES
(1, '{"nodes":[{"id":"test_entity_1","name":"张三","type":"人物","mentions":5},{"id":"test_entity_2","name":"北京大学","type":"机构","mentions":3},{"id":"test_entity_3","name":"人工智能","type":"文化概念","mentions":8},{"id":"test_entity_4","name":"李四","type":"人物","mentions":4},{"id":"test_entity_5","name":"上海","type":"地名","mentions":6},{"id":"test_entity_6","name":"深度学习","type":"文化概念","mentions":7}],"edges":[{"id":"test_rel_1","source":"test_entity_1","target":"test_entity_2","type":"工作于","confidence":0.85},{"id":"test_rel_2","source":"test_entity_1","target":"test_entity_3","type":"研究","confidence":0.85},{"id":"test_rel_3","source":"test_entity_4","target":"test_entity_5","type":"位于","confidence":0.85},{"id":"test_rel_4","source":"test_entity_4","target":"test_entity_6","type":"研究","confidence":0.85},{"id":"test_rel_5","source":"test_entity_3","target":"test_entity_6","type":"包含","confidence":0.85}]}', 6, 5, datetime('now'));

-- 验证数据
SELECT 'Entities:', COUNT(*) FROM entities WHERE entity_id LIKE 'test_%';
SELECT 'Relations:', COUNT(*) FROM relations WHERE relation_id LIKE 'test_%';
SELECT 'Knowledge Graphs:', COUNT(*) FROM knowledge_graphs;
