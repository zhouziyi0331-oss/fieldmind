import Foundation

/// 网络请求错误类型
enum NetworkError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int, message: String?)
    case decodingError(Error)
    case encodingError(Error)
    case networkUnavailable
    case timeout
    case unauthorized
    case serverError(String)
    case unknown(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "无效的URL"
        case .invalidResponse:
            return "服务器响应格式错误"
        case .httpError(let statusCode, let message):
            if let message = message {
                return "请求失败 (\(statusCode)): \(message)"
            }
            return "请求失败，状态码: \(statusCode)"
        case .decodingError(let error):
            return "数据解析失败: \(error.localizedDescription)"
        case .encodingError(let error):
            return "数据编码失败: \(error.localizedDescription)"
        case .networkUnavailable:
            return "网络连接不可用"
        case .timeout:
            return "请求超时"
        case .unauthorized:
            return "未授权，请重新登录"
        case .serverError(let message):
            return "服务器错误: \(message)"
        case .unknown(let error):
            return "未知错误: \(error.localizedDescription)"
        }
    }
}

/// HTTP 方法
enum HTTPMethod: String {
    case get = "GET"
    case post = "POST"
    case put = "PUT"
    case delete = "DELETE"
    case patch = "PATCH"
}
