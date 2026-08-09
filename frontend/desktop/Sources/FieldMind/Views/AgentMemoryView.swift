import SwiftUI

struct AgentMemoryView: View {
    @State private var selectedTab = 0
    @State private var agentRoles: [AgentRole] = []
    @State private var selectedRole: AgentRole?
    @State private var showNewRoleSheet = false

    let tabs = ["角色配置", "项目记忆", "用户偏好"]

    var body: some View {
        VStack(spacing: 0) {
            // 顶部标签栏
            HStack(spacing: 4) {
                ForEach(Array(tabs.enumerated()), id: \.offset) { index, tab in
                    Button {
                        selectedTab = index
                    } label: {
                        Text(tab)
                            .font(.system(size: 13, weight: selectedTab == index ? .semibold : .medium))
                            .foregroundColor(
                                selectedTab == index ?
                                Color.fieldMindPrimary : Color.fieldMindText.opacity(0.6)
                            )
                            .padding(.horizontal, 20)
                            .padding(.vertical, 10)
                            .background(
                                selectedTab == index ?
                                Color.fieldMindPrimary.opacity(0.08) : Color.clear
                            )
                            .cornerRadius(6)
                    }
                    .buttonStyle(PlainButtonStyle())
                }

                Spacer()
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 12)
            .background(Color.white)
            .overlay(
                Rectangle()
                    .fill(Color.gray.opacity(0.1))
                    .frame(height: 1),
                alignment: .bottom
            )

            // 内容区域
            Group {
                switch selectedTab {
                case 0:
                    roleConfigurationView
                case 1:
                    projectMemoryView
                case 2:
                    userPreferencesView
                default:
                    EmptyView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .background(Color.fieldMindBackground)
        .sheet(isPresented: $showNewRoleSheet) {
            NewAgentRoleSheet(onSave: { role in
                createRole(role: role)
            })
        }
        .onAppear {
            loadAgentRoles()
        }
    }

    // MARK: - 角色配置视图
    private var roleConfigurationView: some View {
        HStack(spacing: 0) {
            // 左侧：角色列表
            VStack(spacing: 0) {
                HStack {
                    Text("Agent 角色")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(Color.fieldMindText)

                    Spacer()

                    Button {
                        showNewRoleSheet = true
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .font(.system(size: 16))
                            .foregroundColor(Color.fieldMindPrimary)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(Color.white)

                ScrollView(showsIndicators: false) {
                    VStack(spacing: 8) {
                        ForEach(agentRoles) { role in
                            roleListItem(role: role)
                        }
                    }
                    .padding(12)
                }
            }
            .frame(width: 260)
            .background(Color.white)
            .overlay(
                Rectangle()
                    .fill(Color.gray.opacity(0.1))
                    .frame(width: 1),
                alignment: .trailing
            )

            // 右侧：角色详情
            if let role = selectedRole {
                roleDetailView(role: role)
            } else {
                VStack(spacing: 16) {
                    Image(systemName: "brain")
                        .font(.system(size: 48))
                        .foregroundColor(Color.fieldMindText.opacity(0.2))
                    Text("选择角色查看详情")
                        .font(.system(size: 13))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.fieldMindBackground)
            }
        }
    }

    private func roleListItem(role: AgentRole) -> some View {
        Button {
            selectedRole = role
        } label: {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    Image(systemName: role.icon)
                        .font(.system(size: 14))
                        .foregroundColor(Color.fieldMindPrimary)

                    Text(role.name)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(Color.fieldMindText)

                    Spacer()

                    if role.isDefault {
                        Image(systemName: "star.fill")
                            .font(.system(size: 9))
                            .foregroundColor(Color.fieldMindSuccess)
                    }
                }

                Text(role.expertise)
                    .font(.system(size: 10))
                    .foregroundColor(Color.fieldMindText.opacity(0.6))
                    .lineLimit(2)
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                selectedRole?.id == role.id ?
                Color.fieldMindPrimary.opacity(0.08) : Color.fieldMindBackground
            )
            .cornerRadius(7)
        }
        .buttonStyle(PlainButtonStyle())
    }

    private func roleDetailView(role: AgentRole) -> some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 24) {
                // 角色信息卡片
                VStack(alignment: .leading, spacing: 16) {
                    HStack(spacing: 12) {
                        Image(systemName: role.icon)
                            .font(.system(size: 24))
                            .foregroundColor(Color.fieldMindPrimary)
                            .frame(width: 40, height: 40)
                            .background(Color.fieldMindPrimary.opacity(0.1))
                            .cornerRadius(8)

                        VStack(alignment: .leading, spacing: 4) {
                            Text(role.name)
                                .font(.system(size: 16, weight: .bold))
                                .foregroundColor(Color.fieldMindText)

                            if role.isDefault {
                                HStack(spacing: 6) {
                                    Image(systemName: "star.fill")
                                        .font(.system(size: 9))
                                    Text("默认角色")
                                        .font(.system(size: 10))
                                }
                                .foregroundColor(Color.fieldMindSuccess)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.fieldMindSuccess.opacity(0.1))
                                .cornerRadius(4)
                            }
                        }

                        Spacer()

                        Menu {
                            Button("设为默认") {
                                // 设为默认
                            }
                            Button("编辑角色") {
                                // 编辑
                            }
                            Divider()
                            Button("删除角色") {
                                deleteRole(role: role)
                            }
                        } label: {
                            Image(systemName: "ellipsis")
                                .font(.system(size: 14))
                                .foregroundColor(Color.fieldMindText.opacity(0.6))
                                .frame(width: 32, height: 32)
                                .background(Color.fieldMindBackground)
                                .cornerRadius(6)
                        }
                        .menuStyle(BorderlessButtonMenuStyle())
                    }
                }
                .padding(20)
                .background(Color.white)
                .cornerRadius(10)

                // 专业领域
                VStack(alignment: .leading, spacing: 12) {
                    Text("专业领域")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(Color.fieldMindText)

                    Text(role.expertise)
                        .font(.system(size: 12))
                        .foregroundColor(Color.fieldMindText.opacity(0.8))
                        .lineSpacing(4)
                        .padding(16)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.white)
                        .cornerRadius(8)
                }

                // 基础人设
                VStack(alignment: .leading, spacing: 12) {
                    Text("基础人设")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(Color.fieldMindText)

                    Text(role.personality)
                        .font(.system(size: 12))
                        .foregroundColor(Color.fieldMindText.opacity(0.8))
                        .lineSpacing(4)
                        .padding(16)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.white)
                        .cornerRadius(8)
                }

                // 思维方式
                VStack(alignment: .leading, spacing: 12) {
                    Text("思维方式")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(Color.fieldMindText)

                    VStack(alignment: .leading, spacing: 8) {
                        ForEach(role.thinkingPatterns, id: \.self) { pattern in
                            HStack(alignment: .top, spacing: 8) {
                                Circle()
                                    .fill(Color.fieldMindPrimary)
                                    .frame(width: 6, height: 6)
                                    .padding(.top, 5)

                                Text(pattern)
                                    .font(.system(size: 12))
                                    .foregroundColor(Color.fieldMindText.opacity(0.8))
                            }
                        }
                    }
                    .padding(16)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.white)
                    .cornerRadius(8)
                }
            }
            .padding(24)
        }
        .background(Color.fieldMindBackground)
    }

    // MARK: - 项目记忆视图
    private var projectMemoryView: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 20) {
                Text("项目独立记忆")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(Color.fieldMindText)

                Text("每个项目拥有独立的 Agent 记忆空间，互不干扰")
                    .font(.system(size: 11))
                    .foregroundColor(Color.fieldMindText.opacity(0.6))

                // 项目记忆列表
                VStack(spacing: 12) {
                    projectMemoryCard(
                        projectName: "贵州布依族村落",
                        memoryCount: 156,
                        lastUpdated: "2小时前",
                        keyPoints: ["重点关注文化传承", "优先分析年轻人态度", "注意地方政策变化"]
                    )

                    projectMemoryCard(
                        projectName: "云南傣族社区",
                        memoryCount: 89,
                        lastUpdated: "1天前",
                        keyPoints: ["重点关注民族节庆", "分析旅游产业影响", "收集老人口述历史"]
                    )
                }
            }
            .padding(24)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color.fieldMindBackground)
    }

    private func projectMemoryCard(projectName: String, memoryCount: Int, lastUpdated: String, keyPoints: [String]) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading, spacing: 6) {
                    Text(projectName)
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(Color.fieldMindText)

                    HStack(spacing: 16) {
                        Label("\(memoryCount) 条记忆", systemImage: "brain")
                            .font(.system(size: 10))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))

                        Label("更新于 \(lastUpdated)", systemImage: "clock")
                            .font(.system(size: 10))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }
                }

                Spacer()

                Button {
                    // 查看详情
                } label: {
                    Text("查看")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fieldMindPrimary)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color.fieldMindPrimary.opacity(0.1))
                        .cornerRadius(5)
                }
                .buttonStyle(PlainButtonStyle())
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("记忆要点")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(Color.fieldMindText.opacity(0.7))

                ForEach(keyPoints, id: \.self) { point in
                    HStack(alignment: .top, spacing: 8) {
                        Circle()
                            .fill(Color.fieldMindAuxiliary)
                            .frame(width: 5, height: 5)
                            .padding(.top, 5)

                        Text(point)
                            .font(.system(size: 11))
                            .foregroundColor(Color.fieldMindText.opacity(0.7))
                    }
                }
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .cornerRadius(10)
    }

    // MARK: - 用户偏好视图
    private var userPreferencesView: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 20) {
                Text("用户交互偏好")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(Color.fieldMindText)

                Text("Agent 会自动学习并记住你的工作习惯和偏好")
                    .font(.system(size: 11))
                    .foregroundColor(Color.fieldMindText.opacity(0.6))

                // 偏好列表
                VStack(spacing: 12) {
                    preferenceCard(
                        title: "交互风格",
                        content: "偏好简洁直接的回答，不喜欢过多的解释性内容"
                    )

                    preferenceCard(
                        title: "工作时段",
                        content: "主要在上午 9:00-12:00 和下午 14:00-18:00 工作"
                    )

                    preferenceCard(
                        title: "常用功能",
                        content: "经常使用知识图谱、报告生成和智能对话功能"
                    )

                    preferenceCard(
                        title: "输出偏好",
                        content: "喜欢结构化的输出，偏好使用列表和标题"
                    )
                }

                // 清除记忆按钮
                Button {
                    // 清除用户偏好
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "trash")
                            .font(.system(size: 11))
                        Text("清除用户偏好记忆")
                            .font(.system(size: 12))
                    }
                    .foregroundColor(Color.fieldMindDanger)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(Color.fieldMindDanger.opacity(0.08))
                    .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(24)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color.fieldMindBackground)
    }

    private func preferenceCard(title: String, content: String) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(Color.fieldMindText)

            Text(content)
                .font(.system(size: 11))
                .foregroundColor(Color.fieldMindText.opacity(0.7))
                .lineSpacing(3)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .cornerRadius(8)
    }

    // MARK: - 数据操作
    private func loadAgentRoles() {
        // TODO: 调用后端API /api/v1/agent/roles
        agentRoles = [
            AgentRole(
                id: "1",
                name: "人类学家",
                icon: "person.text.rectangle",
                expertise: "专注于文化人类学、田野调查方法论、民族志写作",
                personality: "严谨、客观、善于观察细节，重视文化相对论和本土视角",
                thinkingPatterns: [
                    "从参与观察的角度理解文化现象",
                    "关注日常生活中的意义系统",
                    "重视局内人（emic）和局外人（etic）视角的结合",
                    "注意文化变迁和现代性的影响"
                ],
                isDefault: true
            ),
            AgentRole(
                id: "2",
                name: "历史学者",
                icon: "book.closed",
                expertise: "专注于地方史、口述历史、历史文献分析",
                personality: "注重史料考证、时间脉络梳理、历史事件的因果关系",
                thinkingPatterns: [
                    "从历史演变的角度理解当下",
                    "重视原始文献和口述材料的价值",
                    "关注历史事件的长时段影响",
                    "注意历史记忆与集体认同的关系"
                ],
                isDefault: false
            ),
            AgentRole(
                id: "3",
                name: "商业分析师",
                icon: "chart.bar",
                expertise: "专注于市场分析、商业模式设计、产业研究",
                personality: "注重可行性、市场潜力、投资回报和风险评估",
                thinkingPatterns: [
                    "从商业价值的角度评估机会",
                    "关注市场需求和竞争格局",
                    "重视资源整合和商业模式创新",
                    "注意政策环境和产业趋势"
                ],
                isDefault: false
            )
        ]
        selectedRole = agentRoles.first
    }

    private func createRole(role: AgentRole) {
        // TODO: 调用后端API POST /api/v1/agent/roles
        agentRoles.append(role)
        showNewRoleSheet = false
    }

    private func deleteRole(role: AgentRole) {
        // TODO: 调用后端API DELETE /api/v1/agent/roles/{id}
        agentRoles.removeAll { $0.id == role.id }
        selectedRole = agentRoles.first
    }
}

// MARK: - 数据模型
struct AgentRole: Identifiable {
    let id: String
    let name: String
    let icon: String
    let expertise: String
    let personality: String
    let thinkingPatterns: [String]
    let isDefault: Bool
}

// MARK: - 新建角色表单
struct NewAgentRoleSheet: View {
    let onSave: (AgentRole) -> Void
    @Environment(\.dismiss) var dismiss

    @State private var name = ""
    @State private var expertise = ""
    @State private var personality = ""
    @State private var selectedIcon = "person.text.rectangle"

    let availableIcons = [
        "person.text.rectangle", "book.closed", "chart.bar",
        "lightbulb", "brain", "graduationcap"
    ]

    var body: some View {
        VStack(spacing: 0) {
            // 标题栏
            HStack {
                Text("新建 Agent 角色")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(Color.fieldMindText)

                Spacer()

                Button("取消") {
                    dismiss()
                }
                .font(.system(size: 12))
                .foregroundColor(Color.fieldMindText.opacity(0.6))
            }
            .padding(20)
            .background(Color.white)

            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 20) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("角色名称")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(Color.fieldMindText)

                        TextField("例如：人类学家", text: $name)
                            .textFieldStyle(CustomTextFieldStyle())
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        Text("专业领域")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(Color.fieldMindText)

                        TextField("描述这个角色的专业领域", text: $expertise)
                            .textFieldStyle(CustomTextFieldStyle())
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        Text("基础人设")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(Color.fieldMindText)

                        TextField("描述这个角色的性格特点", text: $personality)
                            .textFieldStyle(CustomTextFieldStyle())
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        Text("选择图标")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(Color.fieldMindText)

                        HStack(spacing: 12) {
                            ForEach(availableIcons, id: \.self) { icon in
                                Button {
                                    selectedIcon = icon
                                } label: {
                                    Image(systemName: icon)
                                        .font(.system(size: 20))
                                        .foregroundColor(
                                            selectedIcon == icon ?
                                            .white : Color.fieldMindPrimary
                                        )
                                        .frame(width: 44, height: 44)
                                        .background(
                                            selectedIcon == icon ?
                                            Color.fieldMindPrimary : Color.fieldMindPrimary.opacity(0.1)
                                        )
                                        .cornerRadius(8)
                                }
                                .buttonStyle(PlainButtonStyle())
                            }
                        }
                    }

                    Button {
                        let role = AgentRole(
                            id: UUID().uuidString,
                            name: name,
                            icon: selectedIcon,
                            expertise: expertise,
                            personality: personality,
                            thinkingPatterns: [],
                            isDefault: false
                        )
                        onSave(role)
                        dismiss()
                    } label: {
                        Text("创建角色")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(
                                name.isEmpty ? Color.gray.opacity(0.3) : Color.fieldMindPrimary
                            )
                            .cornerRadius(7)
                    }
                    .buttonStyle(PlainButtonStyle())
                    .disabled(name.isEmpty)
                }
                .padding(20)
            }
        }
        .frame(width: 500, height: 500)
        .background(Color.fieldMindBackground)
    }
}
