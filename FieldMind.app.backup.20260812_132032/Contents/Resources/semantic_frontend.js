/**
 * FieldMind 语义引擎前端集成
 * 同义词管理和智能合并
 */

// ==================== 全局变量 ====================
let currentSynonymGroups = [];

// ==================== 加载同义词组 ====================
async function loadSynonymGroups(projectId) {
    try {
        const groups = await callAPI(`/api/semantic/synonyms?project_id=${projectId}`);
        currentSynonymGroups = groups;
        renderSynonymGroups(groups);
    } catch (error) {
        console.error('加载同义词组失败:', error);
    }
}

// ==================== 渲染同义词组 ====================
function renderSynonymGroups(groups) {
    const container = document.getElementById('synonym-groups-container');
    if (!container) return;

    if (groups.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无同义词组，系统会自动学习</div>';
        return;
    }

    container.innerHTML = groups.map(group => `
        <div class="synonym-group-card">
            <div class="synonym-group-header">
                <span class="canonical-term">${group.canonical}</span>
                <span class="synonym-count">${group.members.length} 个同义词</span>
                <span class="created-by ${group.created_by}">${group.created_by === 'system' ? '系统' : '用户'}</span>
            </div>
            <div class="synonym-members">
                ${group.members.map(m => `
                    <div class="synonym-tag">
                        <span class="term">${m.term}</span>
                        ${group.created_by !== 'system' ? `
                            <button class="remove-btn" onclick="removeSynonym('${group.canonical}', '${m.term}')" title="删除">×</button>
                        ` : ''}
                    </div>
                `).join('')}
                <button class="add-synonym-btn" onclick="showAddSynonymDialog('${group.canonical}')">+ 添加</button>
            </div>
        </div>
    `).join('');
}

// ==================== 添加同义词对话框 ====================
function showAddSynonymDialog(canonical) {
    const term = prompt(`为"${canonical}"添加同义词：`, '');
    if (term && term.trim()) {
        addSynonym(canonical, term.trim());
    }
}

async function addSynonym(canonical, term) {
    if (!currentProjectId) {
        alert('请先选择一个项目');
        return;
    }

    try {
        await callAPI('/api/semantic/synonyms', {
            method: 'POST',
            body: JSON.stringify({
                project_id: currentProjectId,
                canonical: canonical,
                term: term
            })
        });

        alert(`已将"${term}"添加为"${canonical}"的同义词`);
        await loadSynonymGroups(currentProjectId);
    } catch (error) {
        alert('添加失败：' + error.message);
    }
}

async function removeSynonym(canonical, term) {
    if (!confirm(`确定要删除"${term}"吗？`)) {
        return;
    }

    try {
        await callAPI('/api/semantic/synonyms', {
            method: 'DELETE',
            body: JSON.stringify({
                project_id: currentProjectId,
                canonical: canonical,
                term: term
            })
        });

        alert('删除成功');
        await loadSynonymGroups(currentProjectId);
    } catch (error) {
        alert('删除失败：' + error.message);
    }
}

// ==================== AI 推荐同义词 ====================
async function suggestSynonyms(term) {
    if (!currentProjectId) {
        return [];
    }

    try {
        const suggestions = await callAPI('/api/semantic/suggest', {
            method: 'POST',
            body: JSON.stringify({
                project_id: currentProjectId,
                term: term
            })
        });

        return suggestions;
    } catch (error) {
        console.error('获取推荐失败:', error);
        return [];
    }
}

// ==================== 显示关键词详情（含同义词信息）====================
async function showKeywordDetail(keyword) {
    // 找到该关键词的同义词组
    const group = currentSynonymGroups.find(g => g.canonical === keyword);

    const modal = document.createElement('div');
    modal.className = 'keyword-detail-modal';
    modal.innerHTML = `
        <div class="modal-overlay" onclick="closeKeywordDetail()"></div>
        <div class="modal-content">
            <div class="modal-header">
                <h3>${keyword}</h3>
                <button class="modal-close" onclick="closeKeywordDetail()">×</button>
            </div>
            <div class="modal-body">
                ${group ? `
                    <div class="detail-section">
                        <h4>包含的同义词</h4>
                        <div class="synonym-list">
                            ${group.members.map(m => `
                                <span class="synonym-badge">${m.term}</span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <div class="detail-section">
                    <h4>AI 推荐的相似词</h4>
                    <div id="suggested-synonyms-${keyword}" class="suggested-list">
                        <div class="loading">加载中...</div>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>添加新的同义词</h4>
                    <div class="add-synonym-form">
                        <input type="text" id="new-synonym-input" placeholder="输入同义词">
                        <button class="btn btn-primary" onclick="addSynonymFromDetail('${keyword}')">添加</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // 异步加载 AI 推荐
    const suggestions = await suggestSynonyms(keyword);
    const suggestedContainer = document.getElementById(`suggested-synonyms-${keyword}`);
    if (suggestions.length > 0) {
        suggestedContainer.innerHTML = suggestions.map(s => `
            <div class="suggested-synonym-item">
                <span class="term">${s.term}</span>
                <span class="score">${(s.combined_score * 100).toFixed(0)}% 相似</span>
                <button class="btn btn-sm" onclick="addSynonym('${keyword}', '${s.term}')">添加</button>
            </div>
        `).join('');
    } else {
        suggestedContainer.innerHTML = '<div class="empty">暂无推荐</div>';
    }
}

function closeKeywordDetail() {
    const modal = document.querySelector('.keyword-detail-modal');
    if (modal) {
        modal.remove();
    }
}

function addSynonymFromDetail(canonical) {
    const input = document.getElementById('new-synonym-input');
    const term = input.value.trim();

    if (!term) {
        alert('请输入同义词');
        return;
    }

    addSynonym(canonical, term).then(() => {
        closeKeywordDetail();
    });
}

// ==================== 修改关键词云渲染（显示合并信息）====================
function renderKeywordCloud(keywords) {
    const container = document.getElementById('keyword-cloud');
    if (!container) return;

    if (keywords.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无关键词</div>';
        return;
    }

    // 按频次排序
    keywords.sort((a, b) => b.frequency - a.frequency);

    // 计算字体大小
    const maxFreq = keywords[0].frequency;
    const minFreq = keywords[keywords.length - 1].frequency;

    container.innerHTML = keywords.map(kw => {
        const fontSize = 12 + (kw.frequency - minFreq) / (maxFreq - minFreq || 1) * 24;

        return `
            <div class="keyword-item ${kw.is_merged ? 'merged' : ''}"
                 style="font-size: ${fontSize}px"
                 onclick="showKeywordDetail('${kw.keyword}')">
                <span class="keyword-text">${kw.keyword}</span>
                <span class="keyword-count">${kw.frequency}</span>
                ${kw.is_merged ? `
                    <span class="merged-badge" title="合并了 ${kw.raw_terms.length} 个同义词">
                        🔗 ${kw.raw_terms.length}
                    </span>
                ` : ''}
            </div>
        `;
    }).join('');
}

// ==================== 初始化语义引擎界面 ====================
async function initSemanticEngine() {
    if (!currentProjectId) return;

    // 加载同义词组
    await loadSynonymGroups(currentProjectId);

    // 加载关键词（带语义信息）
    await loadKeywordsWithSemantic(currentProjectId);
}

async function loadKeywordsWithSemantic(projectId) {
    try {
        const keywords = await callAPI(`/api/keywords?project_id=${projectId}`);
        renderKeywordCloud(keywords);
    } catch (error) {
        console.error('加载关键词失败:', error);
    }
}

// ==================== 页面加载时初始化 ====================
// 在 loadKeywordPage() 中添加
async function loadKeywordPage() {
    if (!currentProjectId) return;

    // 原有的关键词加载
    await loadKeywordsWithSemantic(currentProjectId);

    // 加载同义词管理面板
    await loadSynonymGroups(currentProjectId);
}

// ==================== CSS 样式（添加到页面）====================
const semanticStyles = `
<style>
/* 同义词组卡片 */
.synonym-group-card {
    background: var(--surface2);
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
}

.synonym-group-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}

.canonical-term {
    font-weight: 600;
    font-size: 16px;
    color: var(--primary);
}

.synonym-count {
    color: var(--text3);
    font-size: 13px;
}

.created-by {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
}

.created-by.system {
    background: rgba(159, 172, 36, 0.2);
    color: #9FAC24;
}

.created-by.user {
    background: rgba(23, 138, 183, 0.2);
    color: var(--primary);
}

.synonym-members {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.synonym-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 10px;
    background: var(--surface3);
    border-radius: 4px;
    font-size: 14px;
}

.synonym-tag .remove-btn {
    background: none;
    border: none;
    color: var(--text3);
    cursor: pointer;
    font-size: 16px;
    padding: 0;
    width: 16px;
    height: 16px;
    line-height: 1;
}

.synonym-tag .remove-btn:hover {
    color: var(--danger);
}

.add-synonym-btn {
    padding: 5px 12px;
    background: var(--surface3);
    border: 1px dashed var(--border2);
    border-radius: 4px;
    color: var(--text2);
    cursor: pointer;
    font-size: 14px;
}

.add-synonym-btn:hover {
    border-color: var(--primary);
    color: var(--primary);
}

/* 关键词云中的合并标记 */
.keyword-item.merged {
    border-bottom: 2px solid var(--primary);
}

.merged-badge {
    display: inline-block;
    padding: 2px 6px;
    background: rgba(23, 138, 183, 0.2);
    border-radius: 3px;
    font-size: 11px;
    color: var(--primary);
    margin-left: 5px;
}

/* 关键词详情模态框 */
.keyword-detail-modal {
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

.synonym-list, .suggested-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.synonym-badge {
    padding: 5px 10px;
    background: var(--surface3);
    border-radius: 4px;
    font-size: 13px;
}

.suggested-synonym-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px;
    background: var(--surface2);
    border-radius: 4px;
}

.suggested-synonym-item .score {
    color: var(--text3);
    font-size: 12px;
}

.add-synonym-form {
    display: flex;
    gap: 10px;
}

.add-synonym-form input {
    flex: 1;
    padding: 8px;
    background: var(--surface2);
    border: 1px solid var(--border2);
    border-radius: 4px;
    color: var(--text1);
}
</style>
`;
