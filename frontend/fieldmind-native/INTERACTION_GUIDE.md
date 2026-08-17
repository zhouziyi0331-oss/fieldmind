# 交互组件使用指南

本文档说明如何在FieldMind应用中使用新增的交互组件系统。

## 概述

交互组件系统包括以下模块：
1. **AnimationConfig** - 动画配置和扩展
2. **Toast** - 消息提示
3. **Modal** - 模态框（对话框、表单、抽屉）
4. **Tooltip** - 工具提示和加载状态
5. **Transitions** - 页面过渡和动画组件

## 1. Toast 消息提示

### 基本使用

```swift
// 成功提示
ToastManager.shared.success("操作成功")

// 错误提示
ToastManager.shared.error("操作失败，请重试")

// 警告提示
ToastManager.shared.warning("请注意检查输入内容")

// 信息提示
ToastManager.shared.info("这是一条提示信息")
```

### 自定义持续时间

```swift
ToastManager.shared.success("操作成功", duration: 5.0)
```

### 手动关闭

```swift
ToastManager.shared.dismiss()
```

## 2. Modal 模态框

### Alert 确认对话框

```swift
ModalManager.shared.showAlert(AlertConfig(
    title: "确认操作",
    message: "确定要执行此操作吗？此操作无法撤销。",
    primaryButtonText: "确定",
    secondaryButtonText: "取消",
    primaryAction: {
        // 执行确认操作
    },
    isDestructive: false
))
```

### 删除确认对话框

```swift
ModalManager.shared.showAlert(AlertConfig(
    title: "确认删除",
    message: "确定要删除「项目名称」吗？此操作无法撤销。",
    primaryButtonText: "删除",
    secondaryButtonText: "取消",
    primaryAction: {
        // 执行删除操作
    },
    isDestructive: true
))
```

### Form 表单模态框

```swift
ModalManager.shared.showForm(title: "编辑信息") {
    VStack(alignment: .leading, spacing: 16) {
        // 表单内容
        VStack(alignment: .leading, spacing: 8) {
            Text("名称")
                .font(.system(size: 13))
                .foregroundColor(Color.fmText2)
            
            TextField("请输入名称", text: $name)
                .textFieldStyle(.plain)
                .padding(10)
                .background(Color.fmBg)
                .cornerRadius(6)
        }
        
        // 按钮
        HStack {
            Spacer()
            Button("取消") {
                ModalManager.shared.dismiss()
            }
            Button("保存") {
                // 保存逻辑
                ModalManager.shared.dismiss()
            }
        }
    }
}
```

### Drawer 侧边抽屉

```swift
ModalManager.shared.showDrawer(title: "详细信息", width: 480) {
    VStack(alignment: .leading, spacing: 20) {
        // 抽屉内容
        Text("详细信息内容")
    }
}
```

### Fullscreen 全屏模态框

```swift
ModalManager.shared.showFullscreen(title: "全屏内容") {
    // 全屏内容
    VStack {
        Text("全屏内容")
    }
}
```

## 3. Loading 加载状态

### 显示加载

```swift
LoadingManager.shared.show(message: "加载中")
```

### 隐藏加载

```swift
LoadingManager.shared.hide()
```

### 异步操作示例

```swift
LoadingManager.shared.show(message: "正在处理")

// 执行异步操作
Task {
    await performAsyncOperation()
    
    await MainActor.run {
        LoadingManager.shared.hide()
        ToastManager.shared.success("处理完成")
    }
}
```

### 加载组件

```swift
// 加载旋转器
LoadingSpinner(size: 40)

// 加载点动画
LoadingDots(dotCount: 3, dotSize: 8, spacing: 6)

// 骨架屏
SkeletonView(width: 200, height: 16)

// 骨架卡片
SkeletonCard()
```

## 4. Tooltip 工具提示

```swift
Button("操作") {
    // 按钮操作
}
.tooltip("这是一个提示", position: .top)
```

支持的位置：
- `.top` - 上方
- `.bottom` - 下方
- `.left` - 左侧
- `.right` - 右侧

## 5. 动画扩展

### 悬停效果

```swift
// 悬停缩放
someView
    .hoverScale(isHovered: isHovered, scale: 1.02)

// 悬停阴影
someView
    .hoverShadow(isHovered: isHovered, radius: 8)
```

### 过渡动画

```swift
// 淡入
someView
    .fadeIn(duration: 0.3)

// 滑动进入
someView
    .slideIn(edge: .trailing, duration: 0.3)

// 列表项动画
ForEach(items.indices, id: \.self) { index in
    ItemView(items[index])
        .staggeredAnimation(index: index)
}
```

## 6. 页面过渡

### 内容切换器

```swift
AnimatedContentSwitcher(currentKey: selectedTab) {
    switch selectedTab {
    case "tab1":
        Tab1View()
    case "tab2":
        Tab2View()
    default:
        DefaultView()
    }
}
```

### 可展开区域

```swift
ExpandableSection(isExpanded: false) {
    Text("标题")
} content: {
    Text("内容")
}
```

### 动画进度条

```swift
AnimatedProgressBar(
    progress: 0.65,
    height: 8,
    color: Color(hex: "1890FF"),
    backgroundColor: Color.fmBg
)
```

### 动画计数器

```swift
AnimatedCounter(value: 1234, duration: 0.5)
```

## 7. 增强组件

### 增强按钮

```swift
EnhancedButton(
    title: "保存",
    icon: "checkmark.circle.fill",
    isPrimary: true,
    isDestructive: false
) {
    // 按钮操作
}
```

### 增强卡片

```swift
EnhancedCard {
    VStack {
        Text("卡片内容")
    }
    .padding(16)
}
```

### 增强文本框

```swift
EnhancedTextField(
    placeholder: "请输入内容",
    text: $text,
    isRequired: true,
    errorMessage: errorMessage
)
```

## 8. 动画配置

### 预设时长

```swift
AnimationConfig.Duration.instant   // 0.1s
AnimationConfig.Duration.fast      // 0.2s
AnimationConfig.Duration.normal    // 0.3s
AnimationConfig.Duration.slow      // 0.5s
AnimationConfig.Duration.verySlow  // 0.8s
```

### 预设曲线

```swift
AnimationConfig.Curve.easeIn
AnimationConfig.Curve.easeOut
AnimationConfig.Curve.easeInOut
AnimationConfig.Curve.spring
AnimationConfig.Curve.springBouncy
AnimationConfig.Curve.linear
```

### 预设过渡

```swift
AnimationConfig.Transition.fade
AnimationConfig.Transition.slide
AnimationConfig.Transition.scale
AnimationConfig.Transition.move
AnimationConfig.Transition.combined
```

## 9. 实际应用示例

### 删除操作流程

```swift
Button("删除") {
    ModalManager.shared.showAlert(AlertConfig(
        title: "确认删除",
        message: "确定要删除「\(item.name)」吗？此操作无法撤销。",
        primaryButtonText: "删除",
        secondaryButtonText: "取消",
        primaryAction: {
            LoadingManager.shared.show(message: "删除中")
            
            Task {
                do {
                    try await deleteItem(item)
                    await MainActor.run {
                        LoadingManager.shared.hide()
                        ToastManager.shared.success("删除成功")
                    }
                } catch {
                    await MainActor.run {
                        LoadingManager.shared.hide()
                        ToastManager.shared.error("删除失败：\(error.localizedDescription)")
                    }
                }
            }
        },
        isDestructive: true
    ))
}
```

### 表单提交流程

```swift
Button("保存") {
    guard validateForm() else {
        ToastManager.shared.warning("请检查输入内容")
        return
    }
    
    LoadingManager.shared.show(message: "保存中")
    
    Task {
        do {
            try await saveData()
            await MainActor.run {
                LoadingManager.shared.hide()
                ToastManager.shared.success("保存成功")
                ModalManager.shared.dismiss()
            }
        } catch {
            await MainActor.run {
                LoadingManager.shared.hide()
                ToastManager.shared.error("保存失败")
            }
        }
    }
}
```

## 10. 注意事项

1. **MainActor** - 所有UI更新必须在MainActor上执行
2. **内存管理** - Manager使用单例模式，无需手动管理生命周期
3. **动画性能** - 避免在列表中对每个项目使用复杂动画
4. **Toast显示** - Toast会自动消失，默认3秒
5. **Modal层级** - Modal的zIndex为1001，Toast为1000，Loading为1003
6. **无硬编码** - 所有颜色、尺寸、时长都使用配置常量
7. **无Emoji** - 所有图标使用SF Symbols
8. **一致性** - 使用设计令牌（Color.fmText, Color.fmBg等）保持视觉一致性

## 11. 后续集成

在后续的API集成阶段，这些组件将用于：
- 显示API请求状态
- 处理错误提示
- 确认危险操作
- 显示加载状态
- 提供用户反馈

所有30个页面都可以使用这些组件来增强用户体验。
