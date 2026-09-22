//
//  ChatViewModel_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:01 CST 2026
//

import Foundation
import SwiftUI

// ========================================
// 主实现（来自主项目）
// ========================================


@MainActor
class ChatViewModel: ObservableObject {
    @Published var sessions: [ChatSessionResponse] = []
    @Published var currentSession: ChatSessionResponse?
    @Published var messages: [ChatMessageResponse] = []
    @Published var isLoadingSessions = false
    @Published var isLoadingMessages = false
    @Published var isSendingMessage = false
    @Published var errorMessage: String?

    private let service = ChatService()
    private var currentProjectId: Int?

    /// 加载项目的所有对话会话
    func loadSessions(projectId: Int) async {
        guard currentProjectId != projectId || sessions.isEmpty else {
            return
        }

        isLoadingSessions = true
        errorMessage = nil
        currentProjectId = projectId

        do {
            let response = try await service.listProjectSessions(projectId: projectId, limit: 50)
            self.sessions = response.sessions

            // 自动选择第一个会话
            if currentSession == nil, let firstSession = sessions.first {
                await loadMessages(sessionId: firstSession.id)
            }
        } catch {
            self.errorMessage = error.localizedDescription
        }

        isLoadingSessions = false
    }

    /// 加载会话的所有消息
    func loadMessages(sessionId: Int) async {
        isLoadingMessages = true
        errorMessage = nil

        do {
            // 更新当前会话
            if let session = sessions.first(where: { $0.id == sessionId }) {
                self.currentSession = session
            } else {
                let session = try await service.getSession(sessionId: sessionId)
                self.currentSession = session
            }

            // 加载消息
            let response = try await service.getSessionMessages(sessionId: sessionId, limit: 100)
            self.messages = response.messages
        } catch {
            self.errorMessage = error.localizedDescription
        }

        isLoadingMessages = false
    }

    /// 创建新对话会话
    func createNewSession(projectId: Int, name: String, documentIds: [Int]? = nil) async {
        isLoadingSessions = true
        errorMessage = nil

        do {
            let newSession = try await service.createSession(
                projectId: projectId,
                name: name,
                documentIds: documentIds
            )

            // 添加到列表并选中
            self.sessions.insert(newSession, at: 0)
            self.currentSession = newSession
            self.messages = []
        } catch {
            self.errorMessage = error.localizedDescription
        }

        isLoadingSessions = false
    }

    /// 发送消息
    func sendMessage(content: String) async {
        guard let sessionId = currentSession?.id else {
            return
        }

        isSendingMessage = true
        errorMessage = nil

        // 立即添加用户消息到UI
        let userMessage = ChatMessageResponse(
            id: -1, // 临时ID
            sessionId: sessionId,
            role: "user",
            content: content,
            thinkingProcess: nil,
            sources: nil,
            extraData: nil,
            createdAt: ISO8601DateFormatter().string(from: Date())
        )
        messages.append(userMessage)

        do {
            // 发送消息并获取AI响应
            _ = try await service.sendMessage(sessionId: sessionId, content: content)

            // 移除临时用户消息，重新加载所有消息以获得准确的ID
            await loadMessages(sessionId: sessionId)

            // 更新会话列表中的最后消息时间
            if sessions.firstIndex(where: { $0.id == sessionId }) != nil {
                await loadSessions(projectId: currentProjectId ?? 1)
            }
        } catch {
            // 发送失败，移除临时消息
            messages.removeAll { $0.id == -1 }
            self.errorMessage = error.localizedDescription
        }

        isSendingMessage = false
    }

    /// 删除会话
    func deleteSession(sessionId: Int) async {
        errorMessage = nil

        do {
            try await service.deleteSession(sessionId: sessionId)

            // 从列表中移除
            sessions.removeAll { $0.id == sessionId }

            // 如果删除的是当前会话，清空消息并选择第一个
            if currentSession?.id == sessionId {
                messages = []
                currentSession = nil

                if let firstSession = sessions.first {
                    await loadMessages(sessionId: firstSession.id)
                }
            }
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    /// 进化技能框架
    func evolveSkill() async {
        guard let sessionId = currentSession?.id else {
            return
        }

        errorMessage = nil

        do {
            let response = try await service.evolveSkill(sessionId: sessionId)
            // 可以显示成功提示
            print("技能框架进化成功: \(response.message)")
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

@MainActor
class ChatViewModel: ObservableObject {
    @Published var sessions: [ChatSessionResponse] = []
    @Published var currentSession: ChatSessionResponse?
    @Published var messages: [ChatMessageResponse] = []
    @Published var isLoadingSessions = false
    @Published var isLoadingMessages = false
    @Published var isSendingMessage = false
    @Published var errorMessage: String?

    private let service = ChatService()
    private var currentProjectId: Int?

    /// 加载项目的所有对话会话
    func loadSessions(projectId: Int) async {
        guard currentProjectId != projectId || sessions.isEmpty else {
            return
        }

        isLoadingSessions = true
        errorMessage = nil
        currentProjectId = projectId

        do {
            let response = try await service.listProjectSessions(projectId: projectId, limit: 50)
            self.sessions = response.sessions

            // 自动选择第一个会话
            if currentSession == nil, let firstSession = sessions.first {
                await loadMessages(sessionId: firstSession.id)
            }
        } catch {
            self.errorMessage = error.localizedDescription
        }

        isLoadingSessions = false
    }

    /// 加载会话的所有消息
    func loadMessages(sessionId: Int) async {
        isLoadingMessages = true
        errorMessage = nil

        do {
            // 更新当前会话
            if let session = sessions.first(where: { $0.id == sessionId }) {
                self.currentSession = session
            } else {
                let session = try await service.getSession(sessionId: sessionId)
                self.currentSession = session
            }

            // 加载消息
            let response = try await service.getSessionMessages(sessionId: sessionId, limit: 100)
            self.messages = response.messages
        } catch {
            self.errorMessage = error.localizedDescription
        }

        isLoadingMessages = false
    }

    /// 创建新对话会话
    func createNewSession(projectId: Int, name: String, documentIds: [Int]? = nil) async {
        isLoadingSessions = true
        errorMessage = nil

        do {
            let newSession = try await service.createSession(
                projectId: projectId,
                name: name,
                documentIds: documentIds
            )

            // 添加到列表并选中
            self.sessions.insert(newSession, at: 0)
            self.currentSession = newSession
            self.messages = []
        } catch {
            self.errorMessage = error.localizedDescription
        }

        isLoadingSessions = false
    }

    /// 发送消息
    func sendMessage(content: String) async {
        guard let sessionId = currentSession?.id else {
            return
        }

        isSendingMessage = true
        errorMessage = nil

        // 立即添加用户消息到UI
        let userMessage = ChatMessageResponse(
            id: -1, // 临时ID
            sessionId: sessionId,
            role: "user",
            content: content,
            thinkingProcess: nil,
            sources: nil,
            extraData: nil,
            createdAt: ISO8601DateFormatter().string(from: Date())
        )
        messages.append(userMessage)

        do {
            // 发送消息并获取AI响应
            _ = try await service.sendMessage(sessionId: sessionId, content: content)

            // 移除临时用户消息，重新加载所有消息以获得准确的ID
            await loadMessages(sessionId: sessionId)

            // 更新会话列表中的最后消息时间
            if sessions.firstIndex(where: { $0.id == sessionId }) != nil {
                await loadSessions(projectId: currentProjectId ?? 1)
            }
        } catch {
            // 发送失败，移除临时消息
            messages.removeAll { $0.id == -1 }
            self.errorMessage = error.localizedDescription
        }

        isSendingMessage = false
    }

    /// 删除会话
    func deleteSession(sessionId: Int) async {
        errorMessage = nil

        do {
            try await service.deleteSession(sessionId: sessionId)

            // 从列表中移除
            sessions.removeAll { $0.id == sessionId }

            // 如果删除的是当前会话，清空消息并选择第一个
            if currentSession?.id == sessionId {
                messages = []
                currentSession = nil

                if let firstSession = sessions.first {
                    await loadMessages(sessionId: firstSession.id)
                }
            }
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    /// 进化技能框架
    func evolveSkill() async {
        guard let sessionId = currentSession?.id else {
            return
        }

        errorMessage = nil

        do {
            let response = try await service.evolveSkill(sessionId: sessionId)
            // 可以显示成功提示
            print("技能框架进化成功: \(response.message)")
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }
}
*/

