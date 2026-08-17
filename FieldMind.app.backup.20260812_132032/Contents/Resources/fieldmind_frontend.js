/**
 * FieldMind Frontend API Integration
 * 前端API集成 - 保持原有UI完全不变，只修改数据来源
 */

// ============ 配置 - 使用统一配置 ============
const API_BASE_URL = window.FIELDMIND_CONFIG ? window.FIELDMIND_CONFIG.API_BASE_URL + '/api' : 'http://localhost:8000/api';
const WS_URL = window.FIELDMIND_CONFIG ? window.FIELDMIND_CONFIG.WS_BASE_URL + '/ws' : 'ws://localhost:8000/ws';

let currentProject = 'default_project';
let websocket = null;

// ============ WebSocket连接 ============
function connectWebSocket() {
    websocket = new WebSocket(WS_URL);

    websocket.onopen = () => {
        console.log('✅ WebSocket已连接');
        showNotification('实时连接已建立', 'success');
    };

    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    websocket.onerror = (error) => {
        console.error('WebSocket错误:', error);
    };

    websocket.onclose = () => {
        console.log('WebSocket已断开，5秒后重连...');
        setTimeout(connectWebSocket, 5000);
    };

    // 心跳保持
    setInterval(() => {
        if (websocket.readyState === WebSocket.OPEN) {
            websocket.send('ping');
        }
    }, 30000);
}

function handleWebSocketMessage(data) {
    console.log('收到WebSocket消息:', data);

    switch (data.type) {
        case 'file_upload_started':
            showNotification(`文件 ${data.filename} 开始上传`, 'info');
            break;

        case 'file_processing':
            updateFileStatus(data.filename, 'processing', `步骤 ${data.step}: ${data.message}`);
            break;

        case 'file_processing_completed':
            updateFileStatus(data.filename, 'done', '处理完成');
            showNotification(`文件 ${data.filename} 处理完成`, 'success');
            loadFileList(); // 刷新文件列表
            break;

        case 'file_processing_error':
            updateFileStatus(data.filename, 'error', data.error);
            showNotification(`文件处理失败: ${data.error}`, 'error');
            break;

        case 'project_created':
            showNotification(`项目 ${data.project} 创建成功`, 'success');
            loadProjects(); // 刷新项目列表
            break;
    }
}

// ============ API请求封装 ============
async function apiRequest(endpoint, options = {}) {
    try {
        const url = `${API_BASE_URL}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '请求失败');
        }

        return await response.json();
    } catch (error) {
        console.error('API请求失败:', error);
        showNotification(`请求失败: ${error.message}`, 'error');
        throw error;
    }
}

// ============ 项目管理 ============
async function loadProjects() {
    try {
        const result = await apiRequest('/projects');

        if (result.success) {
            renderProjectList(result.projects);
            updateProjectStats(result.projects);
        }
    } catch (error) {
        console.error('加载项目失败:', error);
    }
}

function renderProjectList(projects) {
    const container = document.querySelector('.sb-project');
    if (!container) return;

    // 保留标题，只更新项目列表
    const projectsHTML = projects.map(proj => `
        <div class="sb-project-item ${proj.name === currentProject ? 'cur' : ''}"
             onclick="switchProject('${proj.name}')">
            <span class="sb-project-dot"></span>
            <span>${proj.name}</span>
        </div>
    `).join('');

    // 只更新项目列表部分
    const existingItems = container.querySelectorAll('.sb-project-item');
    existingItems.forEach(item => item.remove());
    container.insertAdjacentHTML('beforeend', projectsHTML);
}

async function createProject() {
    const name = prompt('请输入项目名称:');
    if (!name) return;

    const description = prompt('请输入项目描述（可选）:') || '';

    try {
        const result = await apiRequest('/projects', {
            method: 'POST',
            body: JSON.stringify({ name, description }),
        });

        if (result.success) {
            showNotification(result.message, 'success');
            await loadProjects();
        }
    } catch (error) {
        console.error('创建项目失败:', error);
    }
}

function switchProject(projectName) {
    currentProject = projectName;
    loadProjectData(projectName);
    loadFileList();
    loadProjects(); // 更新UI高亮
}

async function loadProjectData(projectName) {
    try {
        const result = await apiRequest(`/projects/${projectName}`);

        if (result.success) {
            updateProjectInfo(result.project);
        }
    } catch (error) {
        console.error('加载项目数据失败:', error);
    }
}

// ============ 文件管理 ============
async function loadFileList() {
    try {
        const result = await apiRequest(`/projects/${currentProject}/files`);

        if (result.success) {
            renderFileList(result.files);
        }
    } catch (error) {
        console.error('加载文件列表失败:', error);
    }
}

function renderFileList(files) {
    const container = document.querySelector('.file-list');
    if (!container) return;

    if (files.length === 0) {
        container.innerHTML = '<div style="text-align:center;color:var(--text3);padding:20px;">暂无文件</div>';
        return;
    }

    const filesHTML = files.map(file => {
        const iconClass = file.type;
        const statusClass = file.status;
        const statusText = {
            'done': '已完成',
            'processing': '处理中',
            'pending': '待处理',
            'error': '失败'
        }[file.status] || '未知';

        return `
        <div class="file-item" data-filename="${file.name}">
            <div class="file-icon ${iconClass}">
                ${getFileIcon(file.type)}
            </div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-meta">${file.size_mb} MB · ${formatDate(file.created_at)}</div>
            </div>
            <div class="file-status ${statusClass}">${statusText}</div>
            <button class="btn btn-ghost btn-sm" onclick="deleteFile('${file.name}')" style="margin-left:8px;">
                删除
            </button>
        </div>
        `;
    }).join('');

    container.innerHTML = filesHTML;
}

function getFileIcon(type) {
    const icons = {
        'audio': '<svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13M9 13c-1.657 0-3 1.343-3 3s1.343 3 3 3 3-1.343 3-3-1.343-3-3-3zm12-8c-1.657 0-3 1.343-3 3s1.343 3 3 3 3-1.343 3-3-1.343-3-3-3z"/></svg>',
        'video': '<svg viewBox="0 0 24 24"><path d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>',
        'doc': '<svg viewBox="0 0 24 24"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>',
        'sheet': '<svg viewBox="0 0 24 24"><path d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>',
    };
    return icons[type] || icons['doc'];
}

function updateFileStatus(filename, status, message) {
    const fileItem = document.querySelector(`.file-item[data-filename="${filename}"]`);
    if (!fileItem) return;

    const statusEl = fileItem.querySelector('.file-status');
    if (statusEl) {
        statusEl.className = `file-status ${status}`;
        const statusText = {
            'done': '已完成',
            'processing': '处理中',
            'pending': '待处理',
            'error': '失败'
        }[status] || message;
        statusEl.textContent = statusText;
    }
}

async function handleFileUpload(files) {
    if (!files || files.length === 0) return;

    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            showNotification(`正在上传 ${file.name}...`, 'info');

            const response = await fetch(`${API_BASE_URL}/projects/${currentProject}/files`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (result.success) {
                showNotification(result.message, 'success');
                // WebSocket会自动更新文件列表
            } else {
                showNotification(`上传失败: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('文件上传失败:', error);
            showNotification(`上传失败: ${error.message}`, 'error');
        }
    }
}

async function deleteFile(filename) {
    if (!confirm(`确定要删除文件 "${filename}" 吗？`)) return;

    try {
        const result = await apiRequest(`/projects/${currentProject}/files/${filename}`, {
            method: 'DELETE',
        });

        if (result.success) {
            showNotification(result.message, 'success');
            await loadFileList();
        }
    } catch (error) {
        console.error('删除文件失败:', error);
    }
}

// ============ 知识库查询 ============
async function askQuestion() {
    const input = document.querySelector('#query-input');
    if (!input) return;

    const question = input.value.trim();
    if (!question) {
        showNotification('请输入问题', 'warning');
        return;
    }

    // 显示加载状态
    const answerBox = document.querySelector('#answer-box');
    if (answerBox) {
        answerBox.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text3);">思考中...</div>';
    }

    try {
        const result = await apiRequest(`/projects/${currentProject}/query`, {
            method: 'POST',
            body: JSON.stringify({
                question: question,
                use_lightrag: true,
                use_ragflow: true,
                use_graphrag: true,
            }),
        });

        if (result.success) {
            renderAnswer(result);
        }
    } catch (error) {
        console.error('查询失败:', error);
        if (answerBox) {
            answerBox.innerHTML = '<div style="color:var(--red);padding:20px;">查询失败，请重试</div>';
        }
    }
}

function renderAnswer(result) {
    const answerBox = document.querySelector('#answer-box');
    if (!answerBox) return;

    const enginesUsed = Object.entries(result.engines_used)
        .filter(([_, used]) => used)
        .map(([engine, _]) => `<span class="ev-pill">${engine}</span>`)
        .join(' ');

    const sourcesHTML = result.sources.length > 0
        ? result.sources.map(src => `<div class="src-item">
            <div class="src-type ${src.type}">${src.type}</div>
            <div>
                <div class="src-name">${src.name}</div>
                <div class="src-loc">${src.location}</div>
            </div>
          </div>`).join('')
        : '<div style="color:var(--text3);">无来源</div>';

    answerBox.innerHTML = `
        <div class="ai-box">
            <div class="ai-box-hd">
                <span class="ai-badge">AI回答</span>
                <span class="ai-box-title">${result.question}</span>
            </div>
            <div class="ai-body">${result.answer}</div>
            <div class="ai-evidence">
                <div class="ai-ev-label">使用引擎:</div>
                ${enginesUsed}
            </div>
        </div>
        <div style="margin-top:16px;">
            <div style="font-size:11px;font-weight:700;color:var(--text2);margin-bottom:8px;">来源</div>
            ${sourcesHTML}
        </div>
    `;
}

// ============ 系统监控 ============
async function loadSystemStatus() {
    try {
        const [statusResult, metricsResult, enginesResult] = await Promise.all([
            apiRequest('/system/status'),
            apiRequest('/system/metrics'),
            apiRequest('/system/engines'),
        ]);

        if (statusResult.success) {
            updateSystemStatus(statusResult);
        }

        if (metricsResult.success) {
            updateMetrics(metricsResult.metrics);
        }

        if (enginesResult.success) {
            updateEnginesStatus(enginesResult.engines);
        }
    } catch (error) {
        console.error('加载系统状态失败:', error);
    }
}

function updateSystemStatus(status) {
    // 更新概览页面的系统状态
    const statusEl = document.querySelector('#system-status');
    if (statusEl) {
        statusEl.textContent = status.status === 'running' ? '运行中' : '离线';
    }

    const versionEl = document.querySelector('#system-version');
    if (versionEl) {
        versionEl.textContent = `v${status.version}`;
    }
}

function updateMetrics(metrics) {
    // 更新统计数据
    const updates = {
        '#metric-projects': metrics.total_projects,
        '#metric-files': metrics.total_files,
        '#metric-storage': `${metrics.total_storage_mb} MB`,
        '#metric-modules': metrics.modules_loaded,
    };

    Object.entries(updates).forEach(([selector, value]) => {
        const el = document.querySelector(selector);
        if (el) el.textContent = value;
    });
}

function updateEnginesStatus(engines) {
    const container = document.querySelector('#engines-list');
    if (!container) return;

    const enginesHTML = engines.map(engine => `
        <div class="model-layer">
            <div class="model-layer-hd">
                <div class="ml-icon ${engine.status === 'active' ? 'must' : 'opt'}">
                    <svg viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                </div>
                <div class="ml-info">
                    <div class="ml-name">${engine.name}</div>
                    <div class="ml-desc">${engine.description}</div>
                </div>
                <div class="ml-badge ${engine.status === 'active' ? 'must' : 'opt'}">
                    ${engine.status === 'active' ? '运行中' : '离线'}
                </div>
            </div>
        </div>
    `).join('');

    container.innerHTML = enginesHTML;
}

// ============ 工具函数 ============
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    notification.style.cssText = `
        position: fixed;
        top: 70px;
        right: 24px;
        background: var(--surface);
        border: 1px solid var(--border2);
        border-radius: 7px;
        padding: 12px 20px;
        box-shadow: var(--shadow-lg);
        z-index: 9999;
        font-size: 12px;
        font-weight: 600;
        animation: slideIn 0.3s ease;
    `;

    if (type === 'success') {
        notification.style.borderLeft = '3px solid var(--a2)';
        notification.style.color = 'var(--a2)';
    } else if (type === 'error') {
        notification.style.borderLeft = '3px solid var(--red)';
        notification.style.color = 'var(--red)';
    } else if (type === 'warning') {
        notification.style.borderLeft = '3px solid var(--a3)';
        notification.style.color = 'var(--a3)';
    } else {
        notification.style.borderLeft = '3px solid var(--a1)';
        notification.style.color = 'var(--a1)';
    }

    document.body.appendChild(notification);

    // 3秒后自动移除
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;

    return date.toLocaleDateString('zh-CN');
}

function updateProjectStats(projects) {
    // 更新项目统计信息
    const totalProjects = projects.length;
    const totalFiles = projects.reduce((sum, p) => sum + p.file_count, 0);

    const statsEl = document.querySelector('#projects-stats');
    if (statsEl) {
        statsEl.innerHTML = `${totalProjects} 个项目 · ${totalFiles} 个文件`;
    }
}

function updateProjectInfo(project) {
    // 更新顶部项目信息
    const titleEl = document.querySelector('.topbar-title');
    if (titleEl) {
        titleEl.textContent = project.name;
    }

    const pathEl = document.querySelector('.topbar-path');
    if (pathEl) {
        pathEl.textContent = `/${project.name}`;
    }
}

// ============ 页面加载初始化 ============
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 FieldMind Frontend Initializing...');

    // 连接WebSocket
    connectWebSocket();

    // 加载初始数据
    loadProjects();
    loadFileList();
    loadSystemStatus();

    // 绑定文件上传
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');

    if (uploadZone) {
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('drag-over');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            handleFileUpload(e.dataTransfer.files);
        });

        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            handleFileUpload(e.target.files);
        });
    }

    // 绑定查询按钮
    const queryBtn = document.querySelector('#query-btn');
    if (queryBtn) {
        queryBtn.addEventListener('click', askQuestion);
    }

    const queryInput = document.querySelector('#query-input');
    if (queryInput) {
        queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                askQuestion();
            }
        });
    }

    // 定期刷新系统状态（每30秒）
    setInterval(loadSystemStatus, 30000);

    console.log('✅ FieldMind Frontend Ready!');
});

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOut {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(400px);
        opacity: 0;
    }
}

.upload-zone.drag-over {
    border-color: var(--a1) !important;
    background: var(--a1-dim) !important;
}
`;
document.head.appendChild(style);
