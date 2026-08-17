import Foundation

/// API 配置
struct APIConfig {
    static var baseURL: String {
        // 暂时强制使用本地开发环境
        return "http://localhost:8000/api"
    }

    static let timeout: TimeInterval = 30
    static let defaultHeaders: [String: String] = [
        "Content-Type": "application/json",
        "Accept": "application/json"
    ]
}

/// API 客户端
class APIClient {
    static let shared = APIClient()

    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    private init() {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = APIConfig.timeout
        configuration.timeoutIntervalForResource = APIConfig.timeout * 2
        self.session = URLSession(configuration: configuration)

        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder.dateDecodingStrategy = .iso8601

        self.encoder = JSONEncoder()
        self.encoder.keyEncodingStrategy = .convertToSnakeCase
        self.encoder.dateEncodingStrategy = .iso8601
    }

    /// 发起 API 请求
    /// - Parameters:
    ///   - endpoint: API 端点
    ///   - method: HTTP 方法
    ///   - body: 请求体（可选）
    ///   - queryItems: URL 查询参数（可选）
    ///   - headers: 额外的请求头（可选）
    /// - Returns: 解码后的响应数据
    func request<T: Decodable>(
        _ endpoint: APIEndpoint,
        method: HTTPMethod = .get,
        body: Encodable? = nil,
        queryItems: [URLQueryItem]? = nil,
        headers: [String: String]? = nil
    ) async throws -> T {
        // 构建 URL
        guard var urlComponents = URLComponents(string: APIConfig.baseURL + endpoint.path) else {
            DebugLogger.shared.log("❌ 无效URL: \(endpoint.path)", type: .error)
            throw NetworkError.invalidURL
        }

        // 合并 endpoint 自带的 queryItems 和额外传入的 queryItems
        var allQueryItems = endpoint.queryItems
        if let additionalQueryItems = queryItems {
            allQueryItems.append(contentsOf: additionalQueryItems)
        }
        if !allQueryItems.isEmpty {
            urlComponents.queryItems = allQueryItems
            DebugLogger.shared.log("🔍 QueryItems: \(allQueryItems.map { "\($0.name)=\($0.value ?? "nil")" }.joined(separator: "&"))", type: .info)
        }

        guard let url = urlComponents.url else {
            DebugLogger.shared.log("❌ URL构建失败", type: .error)
            throw NetworkError.invalidURL
        }

        // 构建请求
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue

        // 设置请求头
        for (key, value) in APIConfig.defaultHeaders {
            request.setValue(value, forHTTPHeaderField: key)
        }

        if let headers = headers {
            for (key, value) in headers {
                request.setValue(value, forHTTPHeaderField: key)
            }
        }

        // 设置请求体
        if let body = body {
            do {
                request.httpBody = try encoder.encode(AnyEncodable(body))
            } catch {
                DebugLogger.shared.log("❌ 编码请求体失败: \(error.localizedDescription)", type: .error)
                throw NetworkError.encodingError(error)
            }
        }

        // 记录请求
        let bodyPreview = body != nil ? " [有请求体]" : ""
        DebugLogger.shared.log("🌐 \(method.rawValue) \(url.absoluteString)\(bodyPreview)", type: .api)

        // 发起请求
        let (data, response) = try await session.data(for: request)

        // 检查响应
        guard let httpResponse = response as? HTTPURLResponse else {
            DebugLogger.shared.log("❌ 无效响应", type: .error)
            throw NetworkError.invalidResponse
        }

        // 处理 HTTP 状态码
        switch httpResponse.statusCode {
        case 200...299:
            // 成功响应
            let dataSize = data.count
            let sizeText = dataSize > 1024 ? "\(dataSize/1024)KB" : "\(dataSize)B"
            DebugLogger.shared.log("✅ \(httpResponse.statusCode) - \(sizeText)", type: .success)
            break
        case 401:
            DebugLogger.shared.log("❌ 401 未授权", type: .error, details: String(data: data, encoding: .utf8))
            throw NetworkError.unauthorized
        case 400...499:
            // 客户端错误
            let errorMessage = try? decoder.decode(ErrorResponse.self, from: data)
            let details = String(data: data, encoding: .utf8)
            DebugLogger.shared.log("❌ \(httpResponse.statusCode) 客户端错误: \(errorMessage?.detail ?? "未知")", type: .error, details: details)
            throw NetworkError.httpError(statusCode: httpResponse.statusCode, message: errorMessage?.detail)
        case 500...599:
            // 服务器错误
            let errorMessage = try? decoder.decode(ErrorResponse.self, from: data)
            let details = String(data: data, encoding: .utf8)
            DebugLogger.shared.log("❌ \(httpResponse.statusCode) 服务器错误: \(errorMessage?.detail ?? "未知")", type: .error, details: details)
            throw NetworkError.serverError(errorMessage?.detail ?? "服务器内部错误")
        default:
            DebugLogger.shared.log("❌ \(httpResponse.statusCode) 未知错误", type: .error)
            throw NetworkError.httpError(statusCode: httpResponse.statusCode, message: nil)
        }

        // 解码响应数据
        do {
            let result = try decoder.decode(T.self, from: data)
            return result
        } catch {
            let preview = String(data: data.prefix(200), encoding: .utf8) ?? "无法解析"
            DebugLogger.shared.log("❌ 解码失败: \(error.localizedDescription)", type: .error, details: preview)
            throw NetworkError.decodingError(error)
        }
    }

    /// 无返回值的请求（例如 DELETE 操作）
    func requestWithoutResponse(
        _ endpoint: APIEndpoint,
        method: HTTPMethod,
        body: Encodable? = nil,
        queryItems: [URLQueryItem]? = nil,
        headers: [String: String]? = nil
    ) async throws {
        let _: EmptyResponse = try await request(
            endpoint,
            method: method,
            body: body,
            queryItems: queryItems,
            headers: headers
        )
    }
}

// MARK: - 辅助类型

/// 错误响应模型
struct ErrorResponse: Decodable {
    let detail: String?
    let message: String?
}

/// 空响应（用于没有返回值的请求）
// MARK: - Empty Response Helper
struct EmptyResponse: Codable {}

/// 类型擦除的 Encodable 包装器
private struct AnyEncodable: Encodable {
    private let encodeClosure: (Encoder) throws -> Void

    init(_ encodable: Encodable) {
        self.encodeClosure = encodable.encode
    }

    func encode(to encoder: Encoder) throws {
        try encodeClosure(encoder)
    }
}
