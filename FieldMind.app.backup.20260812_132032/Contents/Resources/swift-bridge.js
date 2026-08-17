// Swift Bridge - JavaScript to Swift Native Communication
console.log('🔧 Swift Bridge Loading...');

// 创建全局API对象
window.FieldMindAPI = {
    // 通用API调用函数
    call: async function(endpoint, params = {}) {
        return new Promise((resolve, reject) => {
            const requestId = Date.now() + Math.random();

            // 创建回调处理
            window['_callback_' + requestId] = function(response) {
                delete window['_callback_' + requestId];
                if (response.error) {
                    reject(new Error(response.error));
                } else {
                    resolve(response);
                }
            };

            // 发送消息到Swift
            try {
                window.webkit.messageHandlers.api.postMessage({
                    requestId: requestId,
                    endpoint: endpoint,
                    params: params
                });
            } catch (error) {
                delete window['_callback_' + requestId];
                reject(error);
            }
        });
    },

    // 项目管理
    projects: {
        getAll: () => window.FieldMindAPI.call('/api/projects'),
        get: (id) => window.FieldMindAPI.call(`/api/projects/${id}`),
        create: (name, description) => window.FieldMindAPI.call('/api/projects', { method: 'POST', name, description }),
        update: (id, name, description) => window.FieldMindAPI.call(`/api/projects/${id}`, { method: 'PUT', name, description }),
        delete: (id) => window.FieldMindAPI.call(`/api/projects/${id}`, { method: 'DELETE' })
    },

    // 文件管理
    files: {
        getByProject: (projectId) => window.FieldMindAPI.call('/api/files', { project_id: projectId }),
        upload: (projectId, filename, content) => window.FieldMindAPI.call('/api/files/upload', {
            project_id: projectId,
            filename: filename,
            content: content
        }),
        delete: (id) => window.FieldMindAPI.call(`/api/files/${id}`, { method: 'DELETE' })
    },

    // 关键词
    keywords: {
        getAll: () => window.FieldMindAPI.call('/api/keywords'),
        getByProject: (projectId) => window.FieldMindAPI.call('/api/keywords', { project_id: projectId })
    },

    // 搜索
    search: {
        query: (searchQuery, projectId) => window.FieldMindAPI.call('/api/search', {
            query: searchQuery,
            project_id: projectId
        })
    },

    // 统计
    stats: {
        keywords: (projectId) => window.FieldMindAPI.call('/api/stats/keywords', { project_id: projectId }),
        documents: (projectId) => window.FieldMindAPI.call('/api/stats/documents', { project_id: projectId })
    },

    // 知识图谱
    graph: {
        get: (projectId) => window.FieldMindAPI.call('/api/graph', { project_id: projectId }),
        getNodes: (projectId) => window.FieldMindAPI.call('/api/graph/nodes', { project_id: projectId }),
        getEdges: (projectId) => window.FieldMindAPI.call('/api/graph/edges', { project_id: projectId })
    },

    // 对话管理
    conversations: {
        getHistory: (projectId, limit) => window.FieldMindAPI.call('/api/conversations', {
            project_id: projectId,
            limit: limit || 50
        }),
        sendMessage: (projectId, message) => window.FieldMindAPI.call('/api/conversations/messages', {
            project_id: projectId,
            message: message
        })
    },

    // 业态分析
    business: {
        analyze: (projectId, data) => window.FieldMindAPI.call('/api/business/analyze', {
            project_id: projectId,
            data: data
        }),
        getReport: (projectId) => window.FieldMindAPI.call('/api/business/report', { project_id: projectId })
    },

    // 时间线
    timeline: {
        generate: (projectId) => window.FieldMindAPI.call('/api/timeline/generate', { project_id: projectId }),
        getEvents: (projectId) => window.FieldMindAPI.call('/api/timeline/events', { project_id: projectId })
    },

    // Agent智能体
    agent: {
        chat: (projectId, message) => window.FieldMindAPI.call('/api/agent/chat', {
            project_id: projectId,
            message: message
        }),
        getStatus: () => window.FieldMindAPI.call('/api/agent/status')
    },

    // 思维模型
    thinkingModel: {
        analyze: (model, content, projectId) => window.FieldMindAPI.call('/api/thinking-model/analyze', {
            model: model,
            content: content,
            project_id: projectId
        }),
        getModels: () => window.FieldMindAPI.call('/api/thinking-model/models')
    },

    // SOP验证
    sop: {
        getTemplates: () => window.FieldMindAPI.call('/api/sop/templates'),
        validate: (templateId, completedSteps) => window.FieldMindAPI.call('/api/sop/validate', {
            template_id: templateId,
            completed_steps: completedSteps
        })
    },

    // 媒体文件
    media: {
        get: (fileId) => window.FieldMindAPI.call(`/api/media/${fileId}`)
    },

    // 叙事生成
    narrative: {
        generate: (projectId, style, length) => window.FieldMindAPI.call('/api/narrative/generate', {
            project_id: projectId,
            style: style || 'academic',
            length: length || 'medium'
        }),
        getTemplates: () => window.FieldMindAPI.call('/api/narrative/templates')
    },

    // 资料导入
    ingest: {
        process: (projectId, filepath) => window.FieldMindAPI.call('/api/ingest', {
            project_id: projectId,
            filepath: filepath
        }),
        getStatus: () => window.FieldMindAPI.call('/api/ingest/status')
    }
};

// 监听来自Swift的响应
window.addEventListener('message', function(event) {
    if (event.data && event.data.requestId && window['_callback_' + event.data.requestId]) {
        window['_callback_' + event.data.requestId](event.data);
    }
});

console.log('✅ Swift Bridge Ready');
console.log('📡 可用API模块:', Object.keys(window.FieldMindAPI).filter(k => k !== 'call'));

console.log('✅ Swift Bridge Ready');
console.log('📡 API接口已初始化:', Object.keys(window.FieldMindAPI));
