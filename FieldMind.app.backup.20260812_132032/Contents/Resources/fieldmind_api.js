/**
 * FieldMind 前端 API 集成
 * 与 Flask 后端进行真实的数据交互
 */

// 使用统一配置
const API_BASE = window.FIELDMIND_CONFIG ? window.FIELDMIND_CONFIG.API_BASE_URL : 'http://localhost:8000';
let currentProjectId = null;
let allProjects = [];

// ==================== 工具函数 ====================

async function callAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || '请求失败');
    }

    return await response.json();
  } catch (error) {
    console.error('API 调用失败:', error);
    alert(`错误: ${error.message}`);
    throw error;
  }
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// ==================== 页面导航 ====================

function showPage(id, el) {
  // 隐藏所有页面
  document.querySelectorAll('.page-section').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  // 显示选中页面
  const page = document.getElementById('page-' + id);
  if (page) page.classList.add('active');
  if (el) el.classList.add('active');

  // 加载页面数据
  loadPageData(id);

  // 如果是 dashboard 页面，初始化图表
  if (id === 'dashboard') {
    setTimeout(initCharts, 100);
  }
}

async function loadPageData(pageId) {
  if (!currentProjectId && pageId !== 'overview') {
    return;
  }

  switch (pageId) {
    case 'overview':
      await loadOverviewPage();
      break;
    case 'import':
      await loadImportPage();
      break;
    case 'keyword':
      await loadKeywordPage();
      break;
    case 'business':
      await loadBusinessPage();
      break;
    case 'skill':
      await loadSkillPage();
      break;
  }
}

// ==================== 概览页面 ====================

async function loadOverviewPage() {
  try {
    // 加载统计数据
    const stats = await callAPI('/api/stats/overview');

    document.querySelector('.stat-card:nth-child(1) .stat-val').textContent = stats.projects || 0;
    document.querySelector('.stat-card:nth-child(2) .stat-val').textContent = stats.files || 0;
    document.querySelector('.stat-card:nth-child(3) .stat-val').textContent = stats.keywords || 0;
    document.querySelector('.stat-card:nth-child(4) .stat-val').textContent = stats.skills || 0;

    // 加载项目列表
    await loadProjects();
  } catch (error) {
    console.error('加载概览页面失败:', error);
  }
}

async function loadProjects() {
  try {
    allProjects = await callAPI('/api/projects');

    const projectList = document.querySelector('.sb-projects');
    if (!projectList) return;

    projectList.innerHTML = '';

    if (allProjects.length === 0) {
      projectList.innerHTML = '<div style="padding:12px;color:var(--sb-text3);font-size:11px;text-align:center;">暂无项目<br>点击上方按钮创建</div>';
      return;
    }

    allProjects.forEach(project => {
      const item = document.createElement('div');
      item.className = 'sb-project-item';
      if (project.id === currentProjectId) {
        item.classList.add('active');
      }
      item.innerHTML = `
        <div class="sb-project-name">${escapeHtml(project.name)}</div>
        <div class="sb-project-meta">${formatDate(project.created_at)}</div>
      `;
      item.onclick = () => selectProject(project.id);
      projectList.appendChild(item);
    });

    // 如果没有选中项目，自动选中第一个
    if (!currentProjectId && allProjects.length > 0) {
      selectProject(allProjects[0].id);
    }
  } catch (error) {
    console.error('加载项目列表失败:', error);
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function selectProject(projectId) {
  currentProjectId = projectId;

  // 更新侧边栏选中状态
  document.querySelectorAll('.sb-project-item').forEach(item => {
    item.classList.remove('active');
  });

  const selectedItem = Array.from(document.querySelectorAll('.sb-project-item')).find(
    item => item.textContent.includes(allProjects.find(p => p.id === projectId)?.name || '')
  );
  if (selectedItem) {
    selectedItem.classList.add('active');
  }

  // 重新加载当前页面的数据
  const activePage = document.querySelector('.page-section.active');
  if (activePage) {
    const pageId = activePage.id.replace('page-', '');
    loadPageData(pageId);
  }
}

async function createNewProject() {
  const name = prompt('请输入项目名称:');
  if (!name || !name.trim()) return;

  const description = prompt('请输入项目描述（可选）:') || '';

  try {
    const project = await callAPI('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ name: name.trim(), description: description.trim() })
    });

    alert(`项目 "${project.name}" 创建成功！`);
    await loadProjects();
    selectProject(project.id);
  } catch (error) {
    console.error('创建项目失败:', error);
  }
}

// ==================== 导入页面 ====================

async function loadImportPage() {
  if (!currentProjectId) {
    document.querySelector('#page-import .section').innerHTML = '<p style="padding:20px;color:var(--text3);">请先选择或创建一个项目</p>';
    return;
  }

  try {
    const files = await callAPI(`/api/files?project_id=${currentProjectId}`);

    const fileListContainer = document.querySelector('#page-import .file-list');
    if (!fileListContainer) return;

    if (files.length === 0) {
      fileListContainer.innerHTML = '<div style="padding:20px;color:var(--text3);text-align:center;">暂无文件<br>点击上方按钮上传</div>';
      return;
    }

    fileListContainer.innerHTML = files.map(file => `
      <div class="file-item">
        <div class="file-icon">${getFileIcon(file.filetype)}</div>
        <div class="file-info">
          <div class="file-name">${escapeHtml(file.filename)}</div>
          <div class="file-meta">${formatFileSize(file.filesize)} · ${formatDate(file.uploaded_at)}</div>
        </div>
      </div>
    `).join('');
  } catch (error) {
    console.error('加载文件列表失败:', error);
  }
}

function getFileIcon(filetype) {
  const icons = {
    'mp3': '🎵',
    'wav': '🎵',
    'mp4': '🎬',
    'mov': '🎬',
    'jpg': '🖼️',
    'png': '🖼️',
    'pdf': '📄',
    'docx': '📝',
    'txt': '📝',
  };
  return icons[filetype] || '📎';
}

async function uploadFile() {
  if (!currentProjectId) {
    alert('请先选择一个项目');
    return;
  }

  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;

  input.onchange = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('project_id', currentProjectId);

        const response = await fetch(`${API_BASE}/api/files/upload`, {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error('上传失败');
        }

        const result = await response.json();
        console.log('上传成功:', result);
      } catch (error) {
        console.error('上传文件失败:', file.name, error);
        alert(`上传 ${file.name} 失败: ${error.message}`);
      }
    }

    alert(`成功上传 ${files.length} 个文件！`);
    await loadImportPage();
    await loadKeywordPage(); // 刷新关键词
  };

  input.click();
}

// ==================== 关键词页面 ====================

async function loadKeywordPage() {
  if (!currentProjectId) {
    document.querySelector('#page-keyword .section').innerHTML = '<p style="padding:20px;color:var(--text3);">请先选择或创建一个项目</p>';
    return;
  }

  try {
    const keywords = await callAPI(`/api/keywords?project_id=${currentProjectId}`);

    const keywordContainer = document.querySelector('#page-keyword .keyword-grid');
    if (!keywordContainer) return;

    if (keywords.length === 0) {
      keywordContainer.innerHTML = '<div style="padding:20px;color:var(--text3);text-align:center;">暂无关键词<br>上传文件后自动提取</div>';
      return;
    }

    keywordContainer.innerHTML = keywords.map(kw => `
      <div class="kw-panel">
        <div class="kw-hd">
          <div class="kw-label">${escapeHtml(kw.keyword)}</div>
          <div class="kw-freq">${kw.frequency}</div>
        </div>
        <div class="kw-bar">
          <div class="kw-bar-fill" style="width:${Math.min(100, kw.frequency * 10)}%"></div>
        </div>
      </div>
    `).join('');
  } catch (error) {
    console.error('加载关键词失败:', error);
  }
}

// ==================== 业态页面 ====================

async function loadBusinessPage() {
  // 业态分析数据（暂时使用静态数据，可以后续扩展API）
  console.log('业态分析页面已加载');
}

// ==================== Skill 页面 ====================

async function loadSkillPage() {
  try {
    const skills = await callAPI(`/api/skills${currentProjectId ? `?project_id=${currentProjectId}` : ''}`);

    // 这里可以动态渲染 skills，当前使用静态HTML
    console.log('加载的 Skills:', skills);
  } catch (error) {
    console.error('加载 Skills 失败:', error);
  }
}

async function createNewSkill() {
  if (!currentProjectId) {
    alert('请先选择一个项目');
    return;
  }

  const name = prompt('请输入 Skill 名称:');
  if (!name || !name.trim()) return;

  const description = prompt('请输入 Skill 描述:') || '';
  const category = prompt('请输入类别（必须内置/核心机制/可选Skill）:', '可选Skill');

  try {
    const skill = await callAPI('/api/skills', {
      method: 'POST',
      body: JSON.stringify({
        project_id: currentProjectId,
        name: name.trim(),
        description: description.trim(),
        category: category.trim()
      })
    });

    alert(`Skill "${skill.name}" 创建成功！`);
    await loadSkillPage();
  } catch (error) {
    console.error('创建 Skill 失败:', error);
  }
}

// ==================== 仪表盘图表 ====================

let chartInstances = {};

function initCharts() {
  // 销毁旧图表
  Object.values(chartInstances).forEach(chart => chart.destroy());
  chartInstances = {};

  // 时序折线图
  const ctx1 = document.getElementById('chart1')?.getContext('2d');
  if (ctx1) {
    chartInstances.chart1 = new Chart(ctx1, {
      type: 'line',
      data: {
        labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
        datasets: [{
          label: '资料导入量',
          data: [12, 19, 15, 25, 22, 30],
          borderColor: '#178AB7',
          backgroundColor: 'rgba(23,138,183,0.1)',
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }
    });
  }

  // 柱状图
  const ctx2 = document.getElementById('chart2')?.getContext('2d');
  if (ctx2) {
    chartInstances.chart2 = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: ['访谈', '图像', '音频', '视频', '文档'],
        datasets: [{
          label: '文件类型分布',
          data: [45, 32, 28, 15, 60],
          backgroundColor: ['#178AB7', '#9FAC24', '#D9BC92', '#45481D', '#6FA7B6']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }
    });
  }

  // 环形图
  const ctx3 = document.getElementById('chart3')?.getContext('2d');
  if (ctx3) {
    chartInstances.chart3 = new Chart(ctx3, {
      type: 'doughnut',
      data: {
        labels: ['已验证', '待验证', '冲突'],
        datasets: [{
          data: [65, 28, 7],
          backgroundColor: ['#178AB7', '#9FAC24', '#D9BC92']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    });
  }
}

// ==================== 时钟 ====================

function updateClock() {
  const now = new Date();
  const timeStr = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const dateStr = now.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });

  const clockEl = document.querySelector('.hd-clock');
  if (clockEl) {
    clockEl.innerHTML = `<div style="font-size:14px;font-weight:600;">${timeStr}</div><div style="font-size:10px;opacity:.7;margin-top:2px;">${dateStr}</div>`;
  }
}

// ==================== 数据闪烁（模拟实时更新）====================

function flicker() {
  const cards = document.querySelectorAll('.stat-card .stat-val');
  cards.forEach(card => {
    if (Math.random() > 0.7) {
      card.style.transform = 'scale(1.05)';
      setTimeout(() => {
        card.style.transform = 'scale(1)';
      }, 200);
    }
  });
}

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', async () => {
  console.log('FieldMind 前端初始化...');

  // 检查后端连接
  try {
    const health = await callAPI('/api/health');
    console.log('后端连接成功:', health);
  } catch (error) {
    console.error('无法连接到后端服务');
    alert('无法连接到后端服务，请检查后端是否已启动');
  }

  // 绑定新建项目按钮
  const newProjectBtn = document.querySelector('.sb-hd button');
  if (newProjectBtn) {
    newProjectBtn.onclick = createNewProject;
  }

  // 绑定上传按钮
  const uploadBtns = document.querySelectorAll('#page-import button');
  uploadBtns.forEach(btn => {
    if (btn.textContent.includes('上传') || btn.textContent.includes('导入')) {
      btn.onclick = uploadFile;
    }
  });

  // 绑定创建 Skill 按钮
  const skillBtns = document.querySelectorAll('#page-skill button');
  skillBtns.forEach(btn => {
    if (btn.textContent.includes('创建')) {
      btn.onclick = createNewSkill;
    }
  });

  // 加载初始数据
  await loadOverviewPage();

  // 显示第一个页面
  showPage('overview', document.querySelector('.nav-item'));

  // 启动时钟
  updateClock();
  setInterval(updateClock, 1000);

  // 启动数据闪烁
  setInterval(flicker, 3000);

  console.log('✓ FieldMind 前端初始化完成');
});
