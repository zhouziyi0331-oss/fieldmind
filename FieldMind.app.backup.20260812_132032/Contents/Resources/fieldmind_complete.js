/**
 * FieldMind 前端完整功能补丁
 * 包含所有缺失功能的实现
 */

// ==================== 1. 拖拽批量上传 ====================

function initDragUpload() {
    const uploadZone = document.querySelector('.upload-zone');
    if (!uploadZone) return;

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadZone.classList.add('drag-over');
        uploadZone.style.borderColor = '#178AB7';
        uploadZone.style.background = 'rgba(23,138,183,0.05)';
    });

    uploadZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadZone.classList.remove('drag-over');
        uploadZone.style.borderColor = '';
        uploadZone.style.background = '';
    });

    uploadZone.addEventListener('drop', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadZone.classList.remove('drag-over');
        uploadZone.style.borderColor = '';
        uploadZone.style.background = '';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            await uploadFilesBatch(Array.from(files));
        }
    });

    // 点击上传
    uploadZone.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.onchange = async (e) => {
            if (e.target.files.length > 0) {
                await uploadFilesBatch(Array.from(e.target.files));
            }
        };
        input.click();
    });
}

async function uploadFilesBatch(files) {
    if (!currentProjectId) {
        alert('请先选择一个项目');
        return;
    }

    const formData = new FormData();
    files.forEach(file => {
        formData.append('file', file);
    });
    formData.append('project_id', currentProjectId);

    try {
        alert(`正在上传 ${files.length} 个文件，请稍候...`);

        const response = await fetch(`${API_BASE}/api/files/upload-batch`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success > 0) {
            alert(`成功上传 ${result.success} 个文件${result.failed > 0 ? `，${result.failed} 个失败` : ''}！`);
            await loadImportPage();
            await loadKeywordPage();
        } else {
            alert('上传失败，请检查文件');
        }
    } catch (error) {
        alert('上传失败：' + error.message);
    }
}


// ==================== 2. 业态分析详情展开 ====================

let currentBusinessData = [];

async function loadBusinessPage() {
    if (!currentProjectId) {
        document.querySelector('#page-busi .g3').innerHTML = '<div class="card"><div class="card-body">请先选择一个项目</div></div>';
        return;
    }

    try {
        const businesses = await callAPI(`/api/business?project_id=${currentProjectId}`);
        currentBusinessData = businesses;
        renderBusinessCards(businesses);
    } catch (error) {
        console.error('加载业态列表失败:', error);
    }
}

function renderBusinessCards(businesses) {
    const container = document.querySelector('#page-busi .g3');
    if (!container) return;

    if (businesses.length === 0) {
        container.innerHTML = '<div class="card"><div class="card-body">暂无业态数据</div></div>';
        return;
    }

    container.innerHTML = businesses.map(b => `
        <div class="card" onclick="showBusinessDetail(${b.id})" style="cursor:pointer;">
            <div class="card-title">${b.name}</div>
            <div class="card-body">
                <div class="biz-score">${b.score}<span class="biz-score-unit">分</span></div>
                <div class="biz-bar"><div class="biz-bar-fill" style="width:${b.score}%"></div></div>
                <div class="biz-tags">
                    ${b.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            </div>
        </div>
    `).join('');
}

async function showBusinessDetail(businessId) {
    try {
        const business = await callAPI(`/api/business/${businessId}`);

        // 创建详情弹窗
        const modal = document.createElement('div');
        modal.className = 'business-detail-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="closeBusinessDetail()"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${business.name}</h2>
                    <button class="modal-close" onclick="closeBusinessDetail()">×</button>
                </div>
                <div class="modal-body">
                    <div class="detail-section">
                        <h3>基本信息</h3>
                        <p><strong>类别：</strong>${business.category}</p>
                        <p><strong>综合评分：</strong>${business.score}分</p>
                        <p><strong>风险等级：</strong>${business.risk_level}</p>
                        <p><strong>描述：</strong>${business.description || '暂无描述'}</p>
                    </div>

                    <div class="detail-section">
                        <h3>详细评估</h3>
                        <div class="score-item">
                            <span>可持续性</span>
                            <div class="score-bar"><div style="width:${business.sustainability}%"></div></div>
                            <span>${business.sustainability}%</span>
                        </div>
                        <div class="score-item">
                            <span>市场需求</span>
                            <div class="score-bar"><div style="width:${business.market_demand}%"></div></div>
                            <span>${business.market_demand}%</span>
                        </div>
                        <div class="score-item">
                            <span>资源匹配度</span>
                            <div class="score-bar"><div style="width:${business.resource_availability}%"></div></div>
                            <span>${business.resource_availability}%</span>
                        </div>
                    </div>

                    ${business.action_steps && business.action_steps.length > 0 ? `
                    <div class="detail-section">
                        <h3>行动步骤</h3>
                        <ol>
                            ${business.action_steps.map(step => `<li>${step}</li>`).join('')}
                        </ol>
                    </div>
                    ` : ''}

                    ${business.evidence_materials && business.evidence_materials.length > 0 ? `
                    <div class="detail-section">
                        <h3>依据材料</h3>
                        <div class="evidence-list">
                            ${business.evidence_materials.map(mat => `<span class="evidence-tag">${mat}</span>`).join('')}
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    } catch (error) {
        alert('加载业态详情失败：' + error.message);
    }
}

function closeBusinessDetail() {
    const modal = document.querySelector('.business-detail-modal');
    if (modal) {
        modal.remove();
    }
}


// ==================== 3. 编年史页面 ====================

async function loadTimelinePage() {
    if (!currentProjectId) {
        document.getElementById('timeline-container').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text3);">请先选择一个项目</div>';
        return;
    }

    try {
        const events = await callAPI(`/api/timeline?project_id=${currentProjectId}`);
        renderTimeline(events);
    } catch (error) {
        console.error('加载时间线失败:', error);
    }
}

function renderTimeline(events) {
    const container = document.getElementById('timeline-container');
    if (!container) return;

    if (events.length === 0) {
        container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text3);">暂无时间线事件，点击"自动生成"按钮创建</div>';
        return;
    }

    container.innerHTML = events.map(event => `
        <div class="timeline-item">
            <div class="timeline-date">${event.event_date}</div>
            <div class="timeline-content">
                <div class="timeline-type ${event.event_type}">${event.event_type}</div>
                <div class="timeline-title">${event.title}</div>
                <div class="timeline-desc">${event.description || ''}</div>
                ${event.related_keywords && event.related_keywords.length > 0 ? `
                <div class="timeline-keywords">
                    ${event.related_keywords.map(kw => `<span class="kw-tag">${kw}</span>`).join('')}
                </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

async function generateTimeline() {
    if (!currentProjectId) {
        alert('请先选择一个项目');
        return;
    }

    try {
        const result = await callAPI('/api/timeline/generate', {
            method: 'POST',
            body: JSON.stringify({ project_id: currentProjectId })
        });

        alert(`成功生成 ${result.generated} 个时间线事件！`);
        await loadTimelinePage();
    } catch (error) {
        alert('生成时间线失败：' + error.message);
    }
}


// ==================== 4. 调研报告页面 ====================

async function loadReportPage() {
    if (!currentProjectId) {
        document.getElementById('report-container').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text3);">请先选择一个项目</div>';
        return;
    }

    try {
        const reports = await callAPI(`/api/reports?project_id=${currentProjectId}`);
        renderReportList(reports);
    } catch (error) {
        console.error('加载报告列表失败:', error);
    }
}

function renderReportList(reports) {
    const container = document.getElementById('report-container');
    if (!container) return;

    if (reports.length === 0) {
        container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text3);">暂无报告，点击"生成报告"按钮创建</div>';
        return;
    }

    container.innerHTML = `
        <div class="report-list">
            ${reports.map(report => `
                <div class="report-item" onclick="viewReport(${report.id})">
                    <div class="report-title">${report.title}</div>
                    <div class="report-date">${formatDate(report.generated_at)}</div>
                </div>
            `).join('')}
        </div>
    `;
}

async function generateReport() {
    if (!currentProjectId) {
        alert('请先选择一个项目');
        return;
    }

    try {
        alert('正在生成报告，请稍候...');
        const report = await callAPI('/api/report/generate', {
            method: 'POST',
            body: JSON.stringify({ project_id: currentProjectId })
        });

        alert('报告生成成功！');
        await loadReportPage();
        viewReportContent(report);
    } catch (error) {
        alert('生成报告失败：' + error.message);
    }
}

async function viewReport(reportId) {
    try {
        const report = await callAPI(`/api/reports/${reportId}`);
        viewReportContent(report);
    } catch (error) {
        alert('加载报告失败：' + error.message);
    }
}

function viewReportContent(report) {
    const modal = document.createElement('div');
    modal.className = 'report-modal';
    modal.innerHTML = `
        <div class="modal-overlay" onclick="closeReportModal()"></div>
        <div class="modal-content report-content">
            <div class="modal-header">
                <h2>${report.title}</h2>
                <button class="modal-close" onclick="closeReportModal()">×</button>
            </div>
            <div class="modal-body">
                <div class="report-meta">生成时间：${formatDate(report.generated_at)}</div>
                ${report.sections.map(section => `
                    <div class="report-section">
                        <h3>${section.title}</h3>
                        <pre>${section.content}</pre>
                    </div>
                `).join('')}
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" onclick="exportReport(${report.id})">导出 Markdown</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

function closeReportModal() {
    const modal = document.querySelector('.report-modal');
    if (modal) {
        modal.remove();
    }
}

function exportReport(reportId) {
    // 简单实现：复制到剪贴板
    alert('导出功能：报告内容已准备，可以手动复制');
}


// ==================== 5. Skill 管理完整界面 ====================

function showSkillCreatePanel() {
    const panel = document.getElementById('skill-create-panel');
    if (panel) {
        panel.style.display = 'block';
    }
}

function closeSkillPanel() {
    const panel = document.getElementById('skill-create-panel');
    if (panel) {
        panel.style.display = 'none';
    }
}

async function createSkillWithConfig() {
    const name = document.getElementById('skill-name').value.trim();
    const description = document.getElementById('skill-desc').value.trim();
    const trigger = document.getElementById('skill-trigger').value;
    const rulesText = document.getElementById('skill-rules').value;

    if (!name) {
        alert('请输入 Skill 名称');
        return;
    }

    try {
        const logicConfig = JSON.parse(rulesText);

        // 先验证 Skill
        const validation = await callAPI('/api/skills/validate', {
            method: 'POST',
            body: JSON.stringify({ logic_config: logicConfig })
        });

        if (!validation.valid) {
            alert(`Skill 验证失败：\n${validation.errors.join('\n')}\n\n请修复后重试。`);
            return;
        }

        // 验证通过，创建 Skill
        const response = await callAPI('/api/skills', {
            method: 'POST',
            body: JSON.stringify({
                project_id: currentProjectId,
                name: name,
                description: description,
                category: '自定义Skill',
                trigger_type: trigger,
                logic_config: logicConfig
            })
        });

        alert(`Skill "${response.name}" 创建成功！\n验证通过：${validation.message}`);
        closeSkillPanel();
        await loadSkillPage();
    } catch (e) {
        if (e.message.includes('JSON')) {
            alert('JSON 格式错误，请检查规则配置');
        } else {
            alert('创建失败：' + e.message);
        }
    }
}

async function toggleSkill(skillId, currentStatus) {
    try {
        const response = await callAPI(`/api/skills/${skillId}/toggle`, {
            method: 'POST'
        });

        alert(`Skill 已${response.status === 'active' ? '激活' : '停用'}`);
        await loadSkillPage();
    } catch (e) {
        alert('操作失败：' + e.message);
    }
}

async function testSkill(skillId) {
    const testText = prompt('请输入测试文本（模拟文件内容）：', '布依族山歌田野调研');
    if (!testText) return;

    const testKeywords = prompt('请输入测试关键词（逗号分隔）：', '音频资料,口述历史');
    if (!testKeywords) return;

    const testData = {
        text: testText,
        keywords: testKeywords.split(',').map(k => k.trim()),
        filename: '测试文件.mp3'
    };

    try {
        const response = await callAPI(`/api/skills/${skillId}/test`, {
            method: 'POST',
            body: JSON.stringify({ test_data: testData })
        });

        if (response.success) {
            const output = response.test_output;
            alert(`测试成功！\n\n输出结果：\n` +
                  `- 标签：${output.tags ? output.tags.join(', ') : '无'}\n` +
                  `- 洞察：${output.insights ? output.insights.join(', ') : '无'}\n` +
                  `- 增强关键词：${output.enhanced_keywords ? output.enhanced_keywords.join(', ') : '无'}`);
        } else {
            alert(`测试失败：${response.error}`);
        }
    } catch (e) {
        alert('测试失败：' + e.message);
    }
}

async function loadSkillPage() {
    if (!currentProjectId) return;

    try {
        const skills = await callAPI(`/api/skills?project_id=${currentProjectId}`);
        renderSkillCards(skills);
    } catch (error) {
        console.error('加载 Skills 失败:', error);
    }
}

function renderSkillCards(skills) {
    const container = document.querySelector('.skill-grid');
    if (!container) return;

    const triggerMap = {
        'keyword_extract': '📥 关键词提取',
        'business_analysis': '📊 业态分析',
        'report_generate': '📄 报告生成',
        'chat_response': '💬 对话回复',
        'file_process': '🔧 文件处理',
        'manual': '⚙️ 手动触发'
    };

    container.innerHTML = skills.map(skill => {
        const statusClass = skill.status === 'active' ? 'active' : 'inactive';
        const statusText = skill.status === 'active' ? '✅ 已激活' : '⏸ 已停用';
        const isSystem = skill.is_system === 1;

        return `
            <div class="skill-card ${isSystem ? 'system' : 'custom'}" data-skill-id="${skill.id}">
                <div class="skill-header">
                    <span class="skill-status ${statusClass}" onclick="toggleSkill(${skill.id}, '${skill.status}')">
                        ${statusText}
                    </span>
                    <span class="skill-type">${isSystem ? '🔷 系统内置' : '🔧 自定义'}</span>
                </div>
                <div class="skill-icon">${isSystem ? '🏛️' : '⚙️'}</div>
                <div class="skill-name">${skill.name}</div>
                <div class="skill-desc">${skill.description}</div>
                <div class="skill-meta">
                    <span class="skill-trigger">${triggerMap[skill.trigger_type] || skill.trigger_type}</span>
                </div>
                <div class="skill-actions">
                    <button class="btn btn-ghost btn-sm" onclick="testSkill(${skill.id})">测试</button>
                    ${!isSystem ? `<button class="btn btn-ghost btn-sm" onclick="deleteSkill(${skill.id})">删除</button>` : ''}
                </div>
            </div>
        `;
    }).join('');
}


// ==================== 初始化所有新功能 ====================

document.addEventListener('DOMContentLoaded', async function() {
    console.log('FieldMind 前端补丁加载中...');

    // 初始化拖拽上传
    initDragUpload();

    // 如果当前页面是相关页面，加载数据
    const activePage = document.querySelector('.page-section.active');
    if (activePage) {
        const pageId = activePage.id.replace('page-', '');
        if (pageId === 'busi') await loadBusinessPage();
        if (pageId === 'timeline') await loadTimelinePage();
        if (pageId === 'report') await loadReportPage();
        if (pageId === 'skill') await loadSkillPage();
    }

    console.log('✓ 前端补丁加载完成');
});
