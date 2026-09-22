import SwiftUI

// MARK: - Animation Configuration
struct AnimationConfig {
    // 动画时长
    struct Duration {
        static let instant: Double = 0.1
        static let fast: Double = 0.2
        static let normal: Double = 0.3
        static let slow: Double = 0.5
        static let verySlow: Double = 0.8
    }

    // 动画曲线
    struct Curve {
        static let easeIn = Animation.easeIn(duration: Duration.normal)
        static let easeOut = Animation.easeOut(duration: Duration.normal)
        static let easeInOut = Animation.easeInOut(duration: Duration.normal)
        static let spring = Animation.spring(response: 0.3, dampingFraction: 0.7)
        static let springBouncy = Animation.spring(response: 0.4, dampingFraction: 0.6)
        static let linear = Animation.linear(duration: Duration.normal)
    }

    // 页面过渡
    struct Transition {
        static let fade = AnyTransition.opacity
        static let slide = AnyTransition.slide
        static let scale = AnyTransition.scale
        static let move = AnyTransition.move(edge: .trailing)
        static let combined = AnyTransition.opacity.combined(with: .scale)
    }

    // 悬停效果
    struct Hover {
        static let scaleAmount: CGFloat = 1.02
        static let shadowRadius: CGFloat = 8
        static let duration: Double = Duration.fast
    }

    // 加载动画
    struct Loading {
        static let rotationDuration: Double = 1.0
        static let pulseDuration: Double = 0.8
        static let dotDelay: Double = 0.2
    }
}

// MARK: - Animation Extensions
extension View {
    // 悬停缩放动画
    func hoverScale(isHovered: Bool, scale: CGFloat = AnimationConfig.Hover.scaleAmount) -> some View {
        self.scaleEffect(isHovered ? scale : 1.0)
            .animation(.easeOut(duration: AnimationConfig.Hover.duration), value: isHovered)
    }

    // 悬停阴影动画
    func hoverShadow(isHovered: Bool, radius: CGFloat = AnimationConfig.Hover.shadowRadius) -> some View {
        self.shadow(
            color: Color.black.opacity(isHovered ? 0.1 : 0),
            radius: isHovered ? radius : 0,
            x: 0,
            y: isHovered ? 4 : 0
        )
        .animation(.easeOut(duration: AnimationConfig.Hover.duration), value: isHovered)
    }

    // 列表项出现动画
    func listItemAppear(index: Int, delay: Double = 0.05) -> some View {
        self.opacity(1)
            .transition(.opacity.combined(with: .move(edge: .top)))
            .animation(
                .easeOut(duration: AnimationConfig.Duration.normal)
                    .delay(Double(index) * delay),
                value: index
            )
    }

    // 淡入动画
    func fadeIn(duration: Double = AnimationConfig.Duration.normal) -> some View {
        self.transition(.opacity)
            .animation(.easeIn(duration: duration), value: true)
    }

    // 滑动进入动画
    func slideIn(edge: Edge = .trailing, duration: Double = AnimationConfig.Duration.normal) -> some View {
        self.transition(.move(edge: edge))
            .animation(.easeOut(duration: duration), value: true)
    }
}
