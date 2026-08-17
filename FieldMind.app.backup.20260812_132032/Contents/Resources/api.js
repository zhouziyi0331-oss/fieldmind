/**
 * FieldMind API 调用层
 * 封装所有与后端的通信
 */

// API 基础配置 - 使用统一配置
const API_CONFIG = {
  get baseURL() {
    return window.FIELDMIND_CONFIG ? window.FIELDMIND_CONFIG.API_BASE_URL : 'http://localhost:8000';
  },
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
};

// 当前项目ID（全局状态）
let currentProjectId = 1;

/**
 * 通用API调用函数
 */
async function apiCall(endpoint, options = {}) {
  const url = `${API_CONFIG.baseURL}${endpoint}`;
  const config = {
    ...options,
    headers: {
      ...API_CONFIG.headers,
      ...options.headers
    }
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API调用失败:', endpoint, error);
    showToast(`请求失败: ${error.message}`, 'error');
    throw error;
  }
}

// ==================== 项目管理 ====================

/**
 * 获取所有项目
 */
async function getProjects() {
  return await apiCall('/api/projects', { method: 'GET' });
}

/**
 * 创建新项目
 */
async function createProject(projectData) {
  return await apiCall('/api/projects', {
    method: 'POST',
    body: JSON.stringify(projectData)
  });
}

/**
 * 删除项目
 */
async function deleteProject(projectId) {
  return await apiCall(`/api/projects/${projectId}`, {
    method: 'DELETE'
  });
}

/**
 * 设置当前项目
 */
function setCurrentProject(projectId) {
  currentProjectId = projectId;
  localStorage.setItem('currentProjectId', projectId);
}

/**
 * 获取当前项目ID
 */
function getCurrentProjectId() {
  if (!currentProjectId) {
    currentProjectId = parseInt(localStorage.getItem('currentProjectId') || '1');
  }
  return currentProjectId;
}

// ==================== 文件管理 ====================

/**
 * 获取文件列表
 */
async function getFiles(projectId = null) {
  const pid = projectId || getCurrentProjectId();
  return await apiCall(`/api/files?project_id=${pid}`, { method: 'GET' });
}

/**
 * 上传文件（逐个上传）
 */
async function uploadFiles(files, projectId = null, onProgress = null) {
  const pid = projectId || getCurrentProjectId();
  const results = [];

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const formData = new FormData();

    // 添加项目ID和单个文件
    formData.append('project_id', pid);
    formData.append('file', file);

    const url = `${API_CONFIG.baseURL}/api/files/upload`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData
        // 注意：不要设置 Content-Type，让浏览器自动设置
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || '上传失败');
      }

      const result = await response.json();
      results.push(result);

      // 通知进度
      if (onProgress) {
        onProgress(i + 1, files.length);
      }
    } catch (error) {
      console.error(`文件 ${file.name} 上传失败:`, error);
      results.push({ error: error.message, filename: file.name });
    }
  }

  return {
    success: results.filter(r => !r.error).length,
    failed: results.filter(r => r.error).length,
    total: files.length,
    results
  };
}

/**
 * 删除文件
 */
async function deleteFile(fileId) {
  return await apiCall(`/api/files/${fileId}`, {
    method: 'DELETE'
  });
}

// ==================== 关键词引擎 ====================

/**
 * 获取关键词列表
 */
async function getKeywords(projectId = null) {
  const pid = projectId || getCurrentProjectId();
  return await apiCall(`/api/keywords?project_id=${pid}`, { method: 'GET' });
}

/**
 * 提取关键词
 */
async function extractKeywords(fileId) {
  return await apiCall('/api/keywords/extract', {
    method: 'POST',
    body: JSON.stringify({ file_id: fileId })
  });
}

// ==================== AI对话 ====================

/**
 * 发送对话消息
 */
async function sendChatMessage(message, projectId = null) {
  const pid = projectId || getCurrentProjectId();
  return await apiCall('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      message: message,
      project_id: pid
    })
  });
}

/**
 * 获取对话历史
 */
async function getChatHistory(projectId = null) {
  const pid = projectId || getCurrentProjectId();
  return await apiCall(`/api/chat?project_id=${pid}`, { method: 'GET' });
}

// ==================== Skill 生态 ====================

/**
 * 获取所有Skill
 */
async function getSkills() {
  return await apiCall('/api/skills', { method: 'GET' });
}

/**
 * 创建新Skill
 */
async function createSkill(skillData) {
  return await apiCall('/api/skills', {
    method: 'POST',
    body: JSON.stringify(skillData)
  });
}

/**
 * 执行Skill
 */
async function executeSkill(skillId, input) {
  return await apiCall('/api/skills/llm', {
    method: 'POST',
    body: JSON.stringify({
      skill_id: skillId,
      input: input
    })
  });
}

/**
 * 删除Skill
 */
async function deleteSkill(skillId) {
  return await apiCall(`/api/skills/${skillId}`, {
    method: 'DELETE'
  });
}

/**
 * 启用/禁用Skill
 */
async function toggleSkill(skillId, enabled) {
  return await apiCall(`/api/skills/${skillId}/enable`, {
    method: 'POST',
    body: JSON.stringify({ enabled: enabled })
  });
}

// ==================== 统计数据 ====================

/**
 * 获取概览统计
 */
async function getOverviewStats(projectId = null) {
  const pid = projectId || getCurrentProjectId();
  return await apiCall(`/api/stats/overview?project_id=${pid}`, { method: 'GET' });
}

// ==================== 三层报告（需要补充后端API）====================

/**
 * 生成报告
 */
async function generateReport(reportType, projectId = null) {
  const pid = projectId || getCurrentProjectId();
  return await apiCall('/api/reports/generate', {
    method: 'POST',
    body: JSON.stringify({
      project_id: pid,
      report_type: reportType  // 'r1', 'r2', 'r3'
    })
  });
}

/**
 * 获取报告
 */
async function getReport(reportType, projectId = null) {
  const pid = projectId || getCurrentProjectId();
  return await apiCall(`/api/reports/${pid}/${reportType}`, { method: 'GET' });
}

/**
 * 导出报告
 */
async function exportReport(reportType, format, projectId = null) {
  const pid = projectId || getCurrentProjectId();
  return await apiCall('/api/reports/export', {
    method: 'POST',
    body: JSON.stringify({
      project_id: pid,
      report_type: reportType,
      format: format  // 'pdf', 'markdown', 'docx'
    })
  });
}

// ==================== 知识脉络（需要补充后端API）====================

/**
 * 获取知识脉络
 */
async function getThreads(projectId = null) {
  const pid = projectId || getCurrentProjectId();
  return await apiCall(`/api/threads/${pid}`, { method: 'GET' });
}

/**
 * 生成知识脉络
 */
async function generateThreads(projectId = null) {
  const pid = projectId || getCurrentProjectId();
  return await apiCall('/api/threads/generate', {
    method: 'POST',
    body: JSON.stringify({ project_id: pid })
  });
}

// ==================== 编年史（需要补充后端API）====================

/**
 * 获取时间线
 */
async function getTimeline(projectId = null) {
  const pid = projectId || getCurrentProjectId();
  return await apiCall(`/api/timeline/${pid}`, { method: 'GET' });
}

/**
 * 获取事件详情
 */
async function getEventDetail(eventId) {
  return await apiCall(`/api/timeline/event/${eventId}`, { method: 'GET' });
}

// ==================== Agent记忆（需要补充后端API）====================

/**
 * 获取Agent记忆列表
 */
async function getAgentMemories() {
  return await apiCall('/api/agent/memory', { method: 'GET' });
}

/**
 * 添加Agent记忆
 */
async function addAgentMemory(memoryData) {
  return await apiCall('/api/agent/memory', {
    method: 'POST',
    body: JSON.stringify(memoryData)
  });
}

/**
 * 删除Agent记忆
 */
async function deleteAgentMemory(memoryId) {
  return await apiCall(`/api/agent/memory/${memoryId}`, {
    method: 'DELETE'
  });
}

// ==================== 工作流（需要补充后端API）====================

/**
 * 获取工作流列表
 */
async function getWorkflows() {
  return await apiCall('/api/workflows', { method: 'GET' });
}

/**
 * 执行工作流
 */
async function executeWorkflow(workflowId, params) {
  return await apiCall('/api/workflows/execute', {
    method: 'POST',
    body: JSON.stringify({
      workflow_id: workflowId,
      params: params
    })
  });
}

/**
 * 保存工作流
 */
async function saveWorkflow(workflowData) {
  return await apiCall('/api/workflows', {
    method: 'POST',
    body: JSON.stringify(workflowData)
  });
}

// ==================== 工具函数 ====================

/**
 * 显示Toast提示
 */
function showToast(message, type = 'info') {
  // 复用index.html中的showToast函数
  if (typeof window.showToast === 'function') {
    window.showToast(message, type);
  } else {
    console.log(`[${type.toUpperCase()}] ${message}`);
  }
}

/**
 * 显示加载中
 */
function showLoading(message = '加载中...') {
  // 可以实现一个全局的加载遮罩
  console.log('Loading:', message);
}

/**
 * 隐藏加载中
 */
function hideLoading() {
  console.log('Loading complete');
}
