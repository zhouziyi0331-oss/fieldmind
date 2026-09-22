//
//  RAGService.swift
//  FieldMind
//
//  P3 功能集成 - RAG 检索增强生成服务
//  Created by Claude on 2026-09-16.
//

import Foundation

/// RAG 服务 - 检索增强生成
class RAGService {
    static let shared = RAGService()

    private let baseURL: URL
    private let session: URLSession

    private init() {
        self.baseURL = URL(string: "http://localhost:8000/api/v1/rag")!
        self.session = URLSession.shared
    }

    // MARK: - Models

    struct IndexDocumentRequest: Codable {
        let docId: String
        let content: String
        let metadata: [String: String]
        let chunk: Bool
        let chunkMethod: String

        enum CodingKeys: String, CodingKey {
            case docId = "doc_id"
            case content, metadata, chunk
            case chunkMethod = "chunk_method"
        }
    }

    struct SearchRequest: Codable {
        let query: String
        let topK: Int
        let filterMetadata: [String: String]?

        enum CodingKeys: String, CodingKey {
            case query
            case topK = "top_k"
            case filterMetadata = "filter_metadata"
        }
    }

    struct SearchResult: Codable {
        let document: Document
        let score: Double
        let rank: Int

        struct Document: Codable {
            let docId: String
            let content: String
            let metadata: [String: String]

            enum CodingKeys: String, CodingKey {
                case docId = "doc_id"
                case content, metadata
            }
        }
    }

    struct GenerateRequest: Codable {
        let query: String
        let topK: Int
        let llmProvider: String
        let model: String

        enum CodingKeys: String, CodingKey {
            case query
            case topK = "top_k"
            case llmProvider = "llm_provider"
            case model
        }
    }

    struct GenerateResponse: Codable {
        let query: String
        let answer: String
        let sources: [Source]
        let contextUsed: Bool
        let numSources: Int

        enum CodingKeys: String, CodingKey {
            case query, answer, sources
            case contextUsed = "context_used"
            case numSources = "num_sources"
        }

        struct Source: Codable {
            let docId: String
            let score: Double
            let content: String

            enum CodingKeys: String, CodingKey {
                case docId = "doc_id"
                case score, content
            }
        }
    }

    // MARK: - API Methods

    /// 索引文档
    func indexDocument(docId: String,
                      content: String,
                      metadata: [String: String] = [:],
                      chunk: Bool = false,
                      chunkMethod: String = "tokens") async throws {
        let url = baseURL.appendingPathComponent("index")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = IndexDocumentRequest(
            docId: docId,
            content: content,
            metadata: metadata,
            chunk: chunk,
            chunkMethod: chunkMethod
        )
        request.httpBody = try JSONEncoder().encode(body)

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw RAGError.serverError
        }
    }

    /// 搜索相关文档
    func search(query: String,
                topK: Int = 5,
                filterMetadata: [String: String]? = nil) async throws -> [SearchResult] {
        let url = baseURL.appendingPathComponent("search")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = SearchRequest(query: query, topK: topK, filterMetadata: filterMetadata)
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw RAGError.serverError
        }

        let result = try JSONDecoder().decode([String: [SearchResult]].self, from: data)
        return result["results"] ?? []
    }

    /// 检索增强生成
    func generate(query: String,
                  topK: Int = 3,
                  llmProvider: String = "openai",
                  model: String = "gpt-3.5-turbo") async throws -> GenerateResponse {
        let url = baseURL.appendingPathComponent("generate")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = GenerateRequest(query: query, topK: topK, llmProvider: llmProvider, model: model)
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw RAGError.serverError
        }

        return try JSONDecoder().decode(GenerateResponse.self, from: data)
    }

    /// 删除文档
    func deleteDocument(docId: String) async throws {
        let url = baseURL.appendingPathComponent("documents/\(docId)")
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw RAGError.serverError
        }
    }

    /// 获取统计信息
    func getStatistics() async throws -> [String: Any] {
        let url = baseURL.appendingPathComponent("statistics")

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw RAGError.serverError
        }

        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }
}

// MARK: - Error Types

enum RAGError: Error {
    case invalidURL
    case serverError
    case decodingError
    case networkError

    var localizedDescription: String {
        switch self {
        case .invalidURL:
            return "无效的 URL"
        case .serverError:
            return "服务器错误"
        case .decodingError:
            return "数据解析错误"
        case .networkError:
            return "网络连接错误"
        }
    }
}
