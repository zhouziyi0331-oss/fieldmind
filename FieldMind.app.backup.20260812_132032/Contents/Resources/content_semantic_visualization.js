/**
 * FieldMind 文档内容语义理解 - 前端可视化
 * 包含：文档关联图谱、语义时间线
 */

// ==================== 全局变量 ====================
let currentSemanticAnalysis = null;

// ==================== 加载文档语义分析 ====================
async function loadContentSemanticAnalysis(projectId) {
    if (!projectId) return;

    try {
        showLoading('正在分析文档语义关联...');

        const result = await callAPI('/api/content/analyze', {
            method: 'POST',
            body: JSON.stringify({ project_id: projectId })
        });

        currentSemanticAnalysis = result;

        // 渲染图谱
        renderDocumentGraph(result.graph);

        // 渲染聚类
        renderDocumentClusters(result.clusters);

        // 渲染时间线
        renderSemanticTimeline(result.documents);

        hideLoading();
    } catch (error) {
        hideLoading();
        console.error('语义分析失败:', error);
        alert('语义分析失败：' + error.message);
    }
}

// ==================== 文档关联图谱可视化（D3.js）====================
function renderDocumentGraph(graph) {
    const container = document.getElementById('document-graph');
    if (!container) return;

    if (!graph.nodes || graph.nodes.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无文档可分析，请先上传文件</div>';
        return;
    }

    // 清空容器
    container.innerHTML = '';

    // 使用简单的力导向图（不依赖 D3.js）
    const width = container.clientWidth || 800;
    const height = 600;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.style.border = '1px solid var(--border2)';
    svg.style.borderRadius = '8px';
    svg.style.background = 'var(--surface2)';

    // 简单布局算法（圆形布局）
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 3;

    const nodes = graph.nodes.map((node, i) => {
        const angle = (i / graph.nodes.length) * 2 * Math.PI;
        return {
            ...node,
            x: centerX + radius * Math.cos(angle),
            y: centerY + radius * Math.sin(angle)
        };
    });

    // 绘制连线
    graph.links.forEach(link => {
        const source = nodes.find(n => n.id === link.source);
        const target = nodes.find(n => n.id === link.target);

        if (source && target) {
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', source.x);
            line.setAttribute('y1', source.y);
            line.setAttribute('x2', target.x);
            line.setAttribute('y2', target.y);
            line.setAttribute('stroke', link.strength === 'high' ? '#178AB7' : '#9FAC24');
            line.setAttribute('stroke-width', link.strength === 'high' ? 3 : 1);
            line.setAttribute('opacity', 0.6);

            // 添加提示
            const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
            title.textContent = `相似度: ${link.similarity}`;
            line.appendChild(title);

            svg.appendChild(line);
        }
    });

    // 绘制节点
    nodes.forEach(node => {
        // 节点圆圈
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', node.x);
        circle.setAttribute('cy', node.y);
        circle.setAttribute('r', 30);
        circle.setAttribute('fill', '#178AB7');
        circle.setAttribute('stroke', '#fff');
        circle.setAttribute('stroke-width', 2);
        circle.style.cursor = 'pointer';

        // 添加点击事件
        circle.onclick = () => showDocumentDetail(node);

        svg.appendChild(circle);

        // 节点标签
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', node.x);
        text.setAttribute('y', node.y + 50);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', 'var(--text1)');
        text.setAttribute('font-size', '12');
        text.textContent = node.label.substring(0, 10);

        svg.appendChild(text);
    });

    container.appendChild(svg);
}

// ==================== 文档详情弹窗 ====================
function showDocumentDetail(node) {
    const modal = document.createElement('div');
    modal.className = 'document-detail-modal';
    modal.innerHTML = `
        <div class="modal-overlay" onclick="closeDocumentDetail()"></div>
        <div class="modal-content">
            <div class="modal-header">
                <h3>${node.label}</h3>
                <button class="modal-close" onclick="closeDocumentDetail()">×</button>
            </div>
            <div class="modal-body">
                <div class="detail-section">
                    <h4>主题标签</h4>
                    <div class="topic-tags">
                        ${node.topics.map(t => `<span class="tag">${t}</span>`).join('')}
                    </div>
                </div>

                <div class="detail-section">
                    <h4>内容预览</h4>
                    <pre class="content-preview">${node.preview}</pre>
                </div>

                <div class="detail-section">
                    <h4>上传时间</h4>
                    <p>${node.uploaded_at}</p>
                </div>

                <div class="detail-section">
                    <h4>相似文档</h4>
                    <div id="related-docs-${node.id}" class="related-list">
                        <div class="loading">加载中...</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // 异步加载相似文档
    loadRelatedDocuments(node.id);
}

async function loadRelatedDocuments(fileId) {
    try {
        const related = await callAPI(`/api/content/related?file_id=${fileId}&project_id=${currentProjectId}`);

        const container = document.getElementById(`related-docs-${fileId}`);
        if (!container) return;

        if (related.length === 0) {
            container.innerHTML = '<div class="empty">暂无相似文档</div>';
            return;
        }

        container.innerHTML = related.map(doc => `
            <div class="related-item">
                <span class="filename">${doc.filename}</span>
                <span class="similarity">${(doc.similarity * 100).toFixed(0)}% 相似</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载相似文档失败:', error);
    }
}

function closeDocumentDetail() {
    const modal = document.querySelector('.document-detail-modal');
    if (modal) {
        modal.remove();
    }
}

// ==================== 文档聚类展示 ====================
function renderDocumentClusters(clusters) {
    const container = document.getElementById('document-clusters');
    if (!container) return;

    if (!clusters || clusters.length === 0) {
        container.innerHTML = '<div class="empty-state">未发现文档聚类</div>';
        return;
    }

    container.innerHTML = clusters.map(cluster => `
        <div class="cluster-card">
            <div class="cluster-header">
                <span class="cluster-title">聚类 ${cluster.cluster_id}</span>
                <span class="doc-count">${cluster.doc_count} 个文档</span>
            </div>
            <div class="cluster-body">
                <div class="core-topics">
                    <strong>核心主题：</strong>
                    ${cluster.core_topics.map(t => `<span class="tag">${t}</span>`).join('')}
                </div>
                <div class="time-span">
                    <strong>时间跨度：</strong>${cluster.time_span}
                </div>
            </div>
        </div>
    `).join('');
}

// ==================== 语义时间线 ====================
function renderSemanticTimeline(documents) {
    const container = document.getElementById('semantic-timeline');
    if (!container) return;

    if (!documents || documents.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无时间线数据</div>';
        return;
    }

    // 按时间排序
    const sortedDocs = [...documents].sort((a, b) =>
        new Date(a.uploaded_at) - new Date(b.uploaded_at)
    );

    container.innerHTML = sortedDocs.map(doc => `
        <div class="timeline-item">
            <div class="timeline-date">${doc.uploaded_at.substring(0, 10)}</div>
            <div class="timeline-content">
                <div class="timeline-title">${doc.filename}</div>
                <div class="timeline-topics">
                    ${doc.topics.slice(0, 3).map(t => `<span class="topic-tag">${t}</span>`).join('')}
                </div>
                <div class="timeline-preview">${doc.content_preview}...</div>
            </div>
        </div>
    `).join('');
}

// ==================== 初始化语义分析页面 ====================
async function loadSemanticPage() {
    if (!currentProjectId) {
        document.getElementById('document-graph').innerHTML = '<div class="empty-state">请先选择一个项目</div>';
        return;
    }

    await loadContentSemanticAnalysis(currentProjectId);
}

// ==================== 辅助函数 ====================
function showLoading(message) {
    // 简单实现
    console.log('Loading:', message);
}

function hideLoading() {
    // 简单实现
    console.log('Loading complete');
}

// ==================== CSS 样式 ====================
const semanticVisualizationStyles = `
<style>
/* 文档关联图谱 */
#document-graph {
    min-height: 600px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* 文档详情弹窗 */
.document-detail-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.detail-section {
    margin-bottom: 20px;
}

.detail-section h4 {
    font-size: 14px;
    color: var(--text2);
    margin-bottom: 10px;
}

.topic-tags, .related-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.content-preview {
    background: var(--surface3);
    padding: 10px;
    border-radius: 4px;
    white-space: pre-wrap;
    font-size: 13px;
    line-height: 1.6;
}

.related-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px;
    background: var(--surface2);
    border-radius: 4px;
    width: 100%;
}

.similarity {
    color: var(--primary);
    font-weight: 600;
}

/* 聚类卡片 */
.cluster-card {
    background: var(--surface2);
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
}

.cluster-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.cluster-title {
    font-weight: 600;
    color: var(--primary);
}

.doc-count {
    color: var(--text3);
    font-size: 13px;
}

.core-topics, .time-span {
    margin-bottom: 8px;
}

/* 语义时间线 */
#semantic-timeline {
    position: relative;
    padding-left: 20px;
}

.timeline-item {
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
    position: relative;
}

.timeline-item::before {
    content: '';
    position: absolute;
    left: -10px;
    top: 5px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--primary);
}

.timeline-date {
    min-width: 100px;
    color: var(--text3);
    font-size: 13px;
}

.timeline-content {
    flex: 1;
    background: var(--surface2);
    padding: 12px;
    border-radius: 6px;
}

.timeline-title {
    font-weight: 600;
    margin-bottom: 8px;
}

.timeline-topics {
    margin-bottom: 8px;
}

.topic-tag {
    display: inline-block;
    padding: 2px 8px;
    background: var(--surface3);
    border-radius: 3px;
    font-size: 11px;
    margin-right: 5px;
}

.timeline-preview {
    color: var(--text3);
    font-size: 13px;
}
</style>
`;
