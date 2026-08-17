/**
 * FieldMind 前端统一配置
 * 根据环境自动切换 API 端点
 */

// 环境检测
const ENV = (function() {
    const hostname = window.location.hostname;

    // 判断是否为本地开发环境
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '') {
        return 'development';
    }

    return 'production';
})();

// 环境配置
const CONFIG = {
    development: {
        API_BASE_URL: 'http://localhost:8000',
        WS_BASE_URL: 'ws://localhost:8000',
        MINERU_URL: 'http://localhost:8765',
        OLLAMA_URL: 'http://localhost:11434',
    },
    production: {
        API_BASE_URL: 'https://api.fieldmind.com',
        WS_BASE_URL: 'wss://api.fieldmind.com',
        MINERU_URL: 'https://mineru.fieldmind.com',
        OLLAMA_URL: 'https://ollama.fieldmind.com',
    }
};

// 当前配置
const CURRENT_CONFIG = CONFIG[ENV];

// 导出到全局
window.FIELDMIND_CONFIG = {
    ENV: ENV,
    API_BASE_URL: CURRENT_CONFIG.API_BASE_URL,
    WS_BASE_URL: CURRENT_CONFIG.WS_BASE_URL,
    MINERU_URL: CURRENT_CONFIG.MINERU_URL,
    OLLAMA_URL: CURRENT_CONFIG.OLLAMA_URL,

    // 便捷方法：生成完整 API URL
    apiUrl: function(path) {
        // 确保 path 以 / 开头
        if (!path.startsWith('/')) {
            path = '/' + path;
        }
        return this.API_BASE_URL + path;
    },

    // WebSocket URL
    wsUrl: function(path) {
        if (!path.startsWith('/')) {
            path = '/' + path;
        }
        return this.WS_BASE_URL + path;
    }
};

// 日志输出
console.log('[CONFIG] FieldMind 配置已加载');
console.log('[CONFIG] 环境:', ENV);
console.log('[CONFIG] API Base:', CURRENT_CONFIG.API_BASE_URL);
console.log('[CONFIG] WebSocket:', CURRENT_CONFIG.WS_BASE_URL);
