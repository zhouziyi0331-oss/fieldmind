#!/bin/bash
# FieldMind iOS/macOS 项目初始化脚本

echo "📱 初始化 FieldMind iOS/macOS 项目..."
echo ""

# 检查 Xcode
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ 未找到 Xcode，请先安装 Xcode"
    exit 1
fi

echo "✅ Xcode 版本: $(xcodebuild -version | head -n 1)"
echo ""

# 创建项目目录结构
cd fieldmind-ios

echo "📁 创建项目目录结构..."
mkdir -p FieldMind/FieldMind/Models
mkdir -p FieldMind/FieldMind/ViewModels
mkdir -p FieldMind/FieldMind/Views
mkdir -p FieldMind/FieldMind/Services
mkdir -p FieldMind/FieldMind/Utilities
mkdir -p FieldMind/FieldMind/Resources
mkdir -p FieldMind/FieldMind/Core

# 创建 Package.swift (Swift Package Manager)
echo ""
echo "📦 创建 Package.swift..."
cat > Package.swift << 'SWIFT'
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "FieldMind",
    platforms: [
        .iOS(.v16),
        .macOS(.v13)
    ],
    products: [
        .library(
            name: "FieldMind",
            targets: ["FieldMind"]
        )
    ],
    dependencies: [
        // Network
        .package(url: "https://github.com/Alamofire/Alamofire.git", from: "5.9.0"),
        // Keychain
        .package(url: "https://github.com/kishikawakatsumi/KeychainAccess.git", from: "4.2.2"),
        // SwiftUI Navigation
        .package(url: "https://github.com/pointfreeco/swift-composable-architecture.git", from: "1.7.0")
    ],
    targets: [
        .target(
            name: "FieldMind",
            dependencies: [
                "Alamofire",
                "KeychainAccess",
                .product(name: "ComposableArchitecture", package: "swift-composable-architecture")
            ]
        ),
        .testTarget(
            name: "FieldMindTests",
            dependencies: ["FieldMind"]
        )
    ]
)
SWIFT

# 创建核心服务 - APIService
echo "🔧 创建核心服务..."
cat > FieldMind/FieldMind/Services/APIService.swift << 'SWIFT'
import Foundation
import Alamofire
import Combine

class APIService {
    static let shared = APIService()
    
    private let baseURL: String
    private let session: Session
    
    private init() {
        // 从配置读取或使用默认值
        self.baseURL = UserDefaults.standard.string(forKey: "api_base_url") 
            ?? "http://localhost:8000/api/v1"
        
        // 配置会话
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 30
        configuration.timeoutIntervalForResource = 300
        
        self.session = Session(configuration: configuration)
    }
    
    func setBaseURL(_ url: String) {
        UserDefaults.standard.set(url, forKey: "api_base_url")
    }
    
    // MARK: - Audio APIs
    
    func uploadAudio(fileURL: URL, metadata: [String: Any]) -> AnyPublisher<AudioFile, Error> {
        let endpoint = "\(baseURL)/audio/upload"
        
        return Future { promise in
            AF.upload(multipartFormData: { formData in
                formData.append(fileURL, withName: "file")
                
                if let jsonData = try? JSONSerialization.data(withJSONObject: metadata) {
                    formData.append(jsonData, withName: "metadata", mimeType: "application/json")
                }
            }, to: endpoint)
            .validate()
            .responseDecodable(of: AudioFile.self) { response in
                switch response.result {
                case .success(let audioFile):
                    promise(.success(audioFile))
                case .failure(let error):
                    promise(.failure(error))
                }
            }
        }
        .eraseToAnyPublisher()
    }
    
    func transcribeAudio(fileId: String, language: String = "zh") -> AnyPublisher<TranscriptionResult, Error> {
        let endpoint = "\(baseURL)/audio/transcribe/\(fileId)"
        let parameters: [String: String] = ["language": language]
        
        return Future { promise in
            self.session.request(endpoint, method: .post, parameters: parameters, encoding: JSONEncoding.default)
                .validate()
                .responseDecodable(of: TranscriptionResult.self) { response in
                    switch response.result {
                    case .success(let result):
                        promise(.success(result))
                    case .failure(let error):
                        promise(.failure(error))
                    }
                }
        }
        .eraseToAnyPublisher()
    }
    
    // MARK: - RAG APIs
    
    func queryRAG(question: String, topK: Int = 5) -> AnyPublisher<RAGResponse, Error> {
        let endpoint = "\(baseURL)/rag/query"
        let parameters: [String: Any] = [
            "question": question,
            "top_k": topK,
            "return_sources": true
        ]
        
        return Future { promise in
            self.session.request(endpoint, method: .post, parameters: parameters, encoding: JSONEncoding.default)
                .validate()
                .responseDecodable(of: RAGResponse.self) { response in
                    switch response.result {
                    case .success(let result):
                        promise(.success(result))
                    case .failure(let error):
                        promise(.failure(error))
                    }
                }
        }
        .eraseToAnyPublisher()
    }
    
    // MARK: - Knowledge Graph APIs
    
    func createEntity(type: String, properties: [String: Any]) -> AnyPublisher<KGEntity, Error> {
        let endpoint = "\(baseURL)/kg/entities"
        let parameters: [String: Any] = [
            "entity_type": type,
            "properties": properties
        ]
        
        return Future { promise in
            self.session.request(endpoint, method: .post, parameters: parameters, encoding: JSONEncoding.default)
                .validate()
                .responseDecodable(of: KGEntity.self) { response in
                    switch response.result {
                    case .success(let entity):
                        promise(.success(entity))
                    case .failure(let error):
                        promise(.failure(error))
                    }
                }
        }
        .eraseToAnyPublisher()
    }
    
    func getEntityNeighbors(entityId: String, depth: Int = 1) -> AnyPublisher<[KGEntity], Error> {
        let endpoint = "\(baseURL)/kg/entities/\(entityId)/neighbors"
        let parameters: [String: Int] = ["depth": depth]
        
        return Future { promise in
            self.session.request(endpoint, method: .get, parameters: parameters)
                .validate()
                .responseDecodable(of: [KGEntity].self) { response in
                    switch response.result {
                    case .success(let entities):
                        promise(.success(entities))
                    case .failure(let error):
                        promise(.failure(error))
                    }
                }
        }
        .eraseToAnyPublisher()
    }
}
SWIFT

# 创建数据模型
cat > FieldMind/FieldMind/Models/Models.swift << 'SWIFT'
import Foundation

// MARK: - Audio Models

struct AudioFile: Codable, Identifiable {
    let id: String
    let filename: String
    let filepath: String
    let filesize: Int
    let duration: Double?
    let format: String
    let sampleRate: Int?
    let channels: Int?
    let uploadedAt: Date
    let metadata: [String: String]?
    
    enum CodingKeys: String, CodingKey {
        case id, filename, filepath, filesize, duration, format, metadata
        case sampleRate = "sample_rate"
        case channels
        case uploadedAt = "uploaded_at"
    }
}

struct TranscriptionResult: Codable {
    let fileId: String
    let text: String
    let language: String
    let segments: [TranscriptionSegment]
    let processingTime: Double
    
    enum CodingKeys: String, CodingKey {
        case fileId = "file_id"
        case text, language, segments
        case processingTime = "processing_time"
    }
}

struct TranscriptionSegment: Codable, Identifiable {
    let id: Int
    let text: String
    let start: Double
    let end: Double
}

// MARK: - RAG Models

struct RAGResponse: Codable {
    let answer: String
    let sources: [RAGSource]?
    let processingTime: Double?
    
    enum CodingKeys: String, CodingKey {
        case answer, sources
        case processingTime = "processing_time"
    }
}

struct RAGSource: Codable, Identifiable {
    let id: String
    let content: String
    let score: Double
    let metadata: [String: String]?
}

// MARK: - Knowledge Graph Models

struct KGEntity: Codable, Identifiable {
    let id: String
    let type: String
    let properties: [String: String]
    
    enum CodingKeys: String, CodingKey {
        case id
        case type = "entity_type"
        case properties
    }
}

struct KGRelationship: Codable {
    let id: String
    let fromId: String
    let toId: String
    let type: String
    let properties: [String: String]?
    
    enum CodingKeys: String, CodingKey {
        case id
        case fromId = "from_id"
        case toId = "to_id"
        case type = "rel_type"
        case properties
    }
}
SWIFT

echo "✅ 项目结构创建完成"
echo ""
echo "📋 项目目录:"
echo "  fieldmind-ios/Package.swift"
echo "  fieldmind-ios/FieldMind/FieldMind/Services/APIService.swift"
echo "  fieldmind-ios/FieldMind/FieldMind/Models/Models.swift"
echo ""
echo "🚀 下一步:"
echo "  1. 在 Xcode 中创建新的 App 项目"
echo "  2. 将生成的文件添加到项目"
echo "  3. 在项目设置中添加 Swift Package 依赖"
echo "  4. 开始开发 UI 和 ViewModels"
echo ""
echo "💡 使用 Swift Package Manager:"
echo "  cd fieldmind-ios"
echo "  swift package resolve"
echo "  open Package.swift  # 在 Xcode 中打开"
