import Foundation

/// API 配置
struct APIConfig {
    /// 后端服务根地址。允许通过 UserDefaults 或环境变量切换部署地址，
    /// 但默认只指向本机 FieldMind 后端。
    static var serverURL: String {
        let configured = UserDefaults.standard.string(forKey: "fieldmind_api_server_url")
            ?? ProcessInfo.processInfo.environment["FIELDMIND_API_URL"]
        let value = (configured?.trimmingCharacters(in: .whitespacesAndNewlines) ?? "")
            .trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        let fallbackPort = ProcessInfo.processInfo.environment["FIELDMIND_PORT"] ?? "8013"
        return normalizeLocalPort(value.isEmpty ? "http://127.0.0.1:\(fallbackPort)" : value)
    }

    /// 旧版本曾使用 8000/8011 端口。只修正本机地址，避免历史偏好把新版客户端带回旧服务；
    /// 远程部署地址和非本机端口保持原样。
    private static func normalizeLocalPort(_ value: String) -> String {
        guard var components = URLComponents(string: value),
              let host = components.host?.lowercased(),
              host == "127.0.0.1" || host == "localhost" || host == "::1",
              let port = components.port,
              port == 8000 || port == 8011 || port == 8012 else {
            return value
        }
        let fallbackPort = Int(ProcessInfo.processInfo.environment["FIELDMIND_PORT"] ?? "") ?? 8013
        components.port = fallbackPort
        return components.string ?? value
    }

    static var baseURL: String {
        "\(serverURL)/api"
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

        self.decoder = APIClient.makeDecoder(keyDecodingStrategy: .convertFromSnakeCase)

        self.encoder = JSONEncoder()
        self.encoder.keyEncodingStrategy = .convertToSnakeCase
        self.encoder.dateEncodingStrategy = .iso8601
    }

    /// 统一解析裸响应和 {success, data} 响应，所有 multipart 上传也使用这一套规则。
    static func decodePayload<T: Decodable>(_ data: Data, as type: T.Type = T.self) throws -> T {
        // 不使用 convertFromSnakeCase，因为我们手动提取JSON字符串后它不起作用
        // 所有的模型都应该在 CodingKeys 中明确定义 snake_case 映射
        let decoder = JSONDecoder()

        // 先尝试直接解码（适用于没有包装的响应）
        do {
            let result = try decoder.decode(T.self, from: data)
            return result
        } catch {
            // 如果直接解码失败，尝试提取data字段
            return try decodePayload(data, as: type, decoder: decoder)
        }
    }

    private static func makeDecoder(keyDecodingStrategy: JSONDecoder.KeyDecodingStrategy) -> JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = keyDecodingStrategy
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let value = try container.decode(String.self)
            let iso = ISO8601DateFormatter()
            iso.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = iso.date(from: value) { return date }
            iso.formatOptions = [.withInternetDateTime]
            if let date = iso.date(from: value) { return date }
            let formats = [
                "yyyy-MM-dd'T'HH:mm:ss.SSSSSS",
                "yyyy-MM-dd'T'HH:mm:ss.SSS",
                "yyyy-MM-dd'T'HH:mm:ss"
            ]
            for format in formats {
                let local = DateFormatter()
                local.locale = Locale(identifier: "en_US_POSIX")
                local.timeZone = TimeZone(secondsFromGMT: 0)
                local.dateFormat = format
                if let date = local.date(from: value) { return date }
            }
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "无法解析日期: \(value)")
        }
        return decoder
    }

    private static func decodePayload<T: Decodable>(_ data: Data, as type: T.Type, decoder: JSONDecoder) throws -> T {
        do {
            // 尝试直接解码（适用于无包装的响应）
            let result = try decoder.decode(T.self, from: data)
            print("✅ [APIClient] 直接解码成功")
            return result
        } catch {
            print("⚠️ [APIClient] 直接解码失败，尝试提取data字段")

            // 尝试作为包装响应处理
            guard let jsonString = String(data: data, encoding: .utf8) else {
                throw error
            }

            // 检查是否是包装响应
            guard (jsonString.contains("\"success\":true") || jsonString.contains("\"success\": true")),
                  let dataStart = jsonString.range(of: "\"data\":")?.upperBound else {
                throw error
            }

            // 从 "data": 后面开始提取
            let remaining = jsonString[dataStart...]
            var index = remaining.startIndex

            // 跳过空格
            while index < remaining.endIndex && remaining[index].isWhitespace {
                index = remaining.index(after: index)
            }

            guard index < remaining.endIndex else { throw error }

            // 确定是对象还是数组
            let firstChar = remaining[index]
            guard firstChar == "{" || firstChar == "[" else { throw error }

            let openChar = firstChar
            let closeChar: Character = (firstChar == "{") ? "}" : "]"

            // 提取完整的JSON
            var depth = 0
            var inString = false
            var escaped = false
            var endIndex = index

            for char in remaining[index...] {
                if escaped {
                    escaped = false
                } else if char == "\\" {
                    escaped = true
                } else if char == "\"" {
                    inString.toggle()
                } else if !inString {
                    if char == openChar {
                        depth += 1
                    } else if char == closeChar {
                        depth -= 1
                        if depth == 0 {
                            endIndex = remaining.index(after: endIndex)
                            break
                        }
                    }
                }
                endIndex = remaining.index(after: endIndex)
            }

            let dataJSONString = String(remaining[index..<endIndex])
            guard let dataJSON = dataJSONString.data(using: .utf8) else { throw error }

            let result = try decoder.decode(T.self, from: dataJSON)
            print("✅ [APIClient] 从data字段解码成功")
            return result
        }
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
        let fullPath = APIConfig.baseURL + endpoint.path
        print("🔍 [APIClient] 构建URL: baseURL=\(APIConfig.baseURL), path=\(endpoint.path)")
        print("🔍 [APIClient] 完整URL: \(fullPath)")

        guard var urlComponents = URLComponents(string: fullPath) else {
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

        // 解码响应数据。新旧后端同时存在裸数据和 {success,data} 包装，
        // 先尝试接口声明的完整响应，再只取 data 字段兼容包装接口。
        do {
            if data.isEmpty, T.self == EmptyResponse.self {
                return EmptyResponse() as! T
            }
            let result: T = try APIClient.decodePayload(data, as: T.self)
            DebugLogger.shared.log("✅ 解码成功: \(String(describing: T.self))", type: .info)
            return result
        } catch let decodingError as DecodingError {
            var errorMsg = "解码失败: "
            switch decodingError {
            case .keyNotFound(let key, let context):
                errorMsg += "缺失键 '\(key.stringValue)' 路径: \(context.codingPath.map { $0.stringValue }.joined(separator: "."))"
            case .typeMismatch(let type, let context):
                errorMsg += "类型不匹配 \(type) 路径: \(context.codingPath.map { $0.stringValue }.joined(separator: "."))"
            case .valueNotFound(let type, let context):
                errorMsg += "值未找到 \(type) 路径: \(context.codingPath.map { $0.stringValue }.joined(separator: "."))"
            case .dataCorrupted(let context):
                errorMsg += "数据损坏: \(context.debugDescription)"
            @unknown default:
                errorMsg += "\(decodingError)"
            }

            let fullJSON = String(data: data, encoding: .utf8) ?? "无法解析"
            DebugLogger.shared.log("❌ \(errorMsg)", type: .error, details: fullJSON)
            throw NetworkError.decodingError(decodingError)
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
    let error: NestedError?

    struct NestedError: Decodable {
        let message: String?
        let details: String?
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        detail = try container.decodeIfPresent(String.self, forKey: .detail)
        message = try container.decodeIfPresent(String.self, forKey: .message)
        error = try container.decodeIfPresent(NestedError.self, forKey: .error)
    }

    private enum CodingKeys: String, CodingKey {
        case detail, message, error
    }

    var resolvedMessage: String? {
        detail ?? message ?? error?.message ?? error?.details
    }
}

/// 后端统一响应包装。部分旧接口仍返回裸数据，调用方按接口契约选择是否使用它。
struct APIEnvelope<T: Decodable>: Decodable {
    let success: Bool
    let data: T
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
