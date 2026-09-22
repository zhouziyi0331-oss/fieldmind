import SwiftUI

// MARK: - Page Transition Type
enum PageTransitionType {
    case fade
    case slide
    case scale
    case push
}

// MARK: - Page Transition Manager
@MainActor


class PageTransitionManager: ObservableObject {
    static let shared = PageTransitionManager()

    @Published var transitionType: PageTransitionType = .fade
    @Published var isTransitioning: Bool = false

    private init() {}

    func transition(to page: String, type: PageTransitionType = .fade, completion: (() -> Void)? = nil) {
        transitionType = type
        isTransitioning = true

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { [weak self] in
            self?.isTransitioning = false
            completion?()
        }
    }
}

// MARK: - Page Transition Modifier
struct PageTransitionModifier: ViewModifier {
    let type: PageTransitionType
    @Binding var isPresented: Bool

    func body(content: Content) -> some View {
        content
            .transition(transitionForType)
            .animation(.easeInOut(duration: 0.3), value: isPresented)
    }

    private var transitionForType: AnyTransition {
        switch type {
        case .fade:
            return .opacity
        case .slide:
            return .move(edge: .trailing).combined(with: .opacity)
        case .scale:
            return .scale(scale: 0.95).combined(with: .opacity)
        case .push:
            return .asymmetric(
                insertion: .move(edge: .trailing),
                removal: .move(edge: .leading)
            )
        }
    }
}

extension View {
    func pageTransition(type: PageTransitionType, isPresented: Binding<Bool>) -> some View {
        self.modifier(PageTransitionModifier(type: type, isPresented: isPresented))
    }
}

// MARK: - Animated Content Switcher
struct AnimatedContentSwitcher<Content: View>: View {
    let currentKey: String
    let content: Content
    let animation: Animation

    init(
        currentKey: String,
        animation: Animation = .easeInOut(duration: 0.3),
        @ViewBuilder content: () -> Content
    ) {
        self.currentKey = currentKey
        self.animation = animation
        self.content = content()
    }

    var body: some View {
        content
            .id(currentKey)
            .transition(.opacity)
            .animation(animation, value: currentKey)
    }
}

// MARK: - Slide Transition View
struct SlideTransitionView<Content: View>: View {
    let isPresented: Bool
    let edge: Edge
    let content: Content

    init(isPresented: Bool, edge: Edge = .trailing, @ViewBuilder content: () -> Content) {
        self.isPresented = isPresented
        self.edge = edge
        self.content = content()
    }

    var body: some View {
        if isPresented {
            content
                .transition(.move(edge: edge).combined(with: .opacity))
        }
    }
}

// MARK: - Fade Transition View
struct FadeTransitionView<Content: View>: View {
    let isPresented: Bool
    let duration: Double
    let content: Content

    init(isPresented: Bool, duration: Double = 0.3, @ViewBuilder content: () -> Content) {
        self.isPresented = isPresented
        self.duration = duration
        self.content = content()
    }

    var body: some View {
        content
            .opacity(isPresented ? 1 : 0)
            .animation(.easeInOut(duration: duration), value: isPresented)
    }
}

// MARK: - Scale Transition View
struct ScaleTransitionView<Content: View>: View {
    let isPresented: Bool
    let scale: CGFloat
    let content: Content

    init(isPresented: Bool, scale: CGFloat = 0.9, @ViewBuilder content: () -> Content) {
        self.isPresented = isPresented
        self.scale = scale
        self.content = content()
    }

    var body: some View {
        content
            .scaleEffect(isPresented ? 1 : scale)
            .opacity(isPresented ? 1 : 0)
            .animation(.spring(response: 0.3, dampingFraction: 0.7), value: isPresented)
    }
}

// MARK: - Staggered List Animation
struct StaggeredListModifier: ViewModifier {
    let index: Int
    let baseDelay: Double
    let duration: Double

    init(index: Int, baseDelay: Double = 0.05, duration: Double = 0.3) {
        self.index = index
        self.baseDelay = baseDelay
        self.duration = duration
    }

    func body(content: Content) -> some View {
        content
            .opacity(1)
            .transition(.asymmetric(
                insertion: .move(edge: .top).combined(with: .opacity),
                removal: .opacity
            ))
            .animation(
                .easeOut(duration: duration).delay(Double(index) * baseDelay),
                value: index
            )
    }
}

extension View {
    func staggeredAnimation(index: Int, baseDelay: Double = 0.05, duration: Double = 0.3) -> some View {
        self.modifier(StaggeredListModifier(index: index, baseDelay: baseDelay, duration: duration))
    }
}

// MARK: - Smooth Expand/Collapse
struct ExpandableSection<Header: View, Content: View>: View {
    @State private var isExpanded: Bool
    let header: Header
    let content: Content
    let animation: Animation

    init(
        isExpanded: Bool = false,
        animation: Animation = .spring(response: 0.3, dampingFraction: 0.7),
        @ViewBuilder header: () -> Header,
        @ViewBuilder content: () -> Content
    ) {
        self._isExpanded = State(initialValue: isExpanded)
        self.animation = animation
        self.header = header()
        self.content = content()
    }

    var body: some View {
        VStack(spacing: 0) {
            Button(action: {
                withAnimation(animation) {
                    isExpanded.toggle()
                }
            }) {
                HStack {
                    header

                    Spacer()

                    Image(systemName: "chevron.right")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                        .rotationEffect(.degrees(isExpanded ? 90 : 0))
                        .animation(animation, value: isExpanded)
                }
            }
            .buttonStyle(.plain)

            if isExpanded {
                content
                    .transition(.asymmetric(
                        insertion: .move(edge: .top).combined(with: .opacity),
                        removal: .opacity
                    ))
            }
        }
    }
}

// MARK: - Animated Number Counter
struct AnimatedCounter: View {
    let value: Int
    let duration: Double

    @State private var displayValue: Int = 0

    init(value: Int, duration: Double = 0.5) {
        self.value = value
        self.duration = duration
    }

    var body: some View {
        Text("\(displayValue)")
            .contentTransition(.numericText())
            .animation(.easeOut(duration: duration), value: displayValue)
            .onAppear {
                animateCount()
            }
            .onChange(of: value) { _, newValue in
                animateCount()
            }
    }

    private func animateCount() {
        let steps = 20
        let increment = max(1, value / steps)
        let stepDuration = duration / Double(steps)

        for i in 0...steps {
            DispatchQueue.main.asyncAfter(deadline: .now() + stepDuration * Double(i)) {
                if i == steps {
                    displayValue = value
                } else {
                    displayValue = min(value, increment * i)
                }
            }
        }
    }
}

// MARK: - Animated Progress Bar
struct AnimatedProgressBar: View {
    let progress: Double
    let height: CGFloat
    let color: Color
    let backgroundColor: Color

    @State private var animatedProgress: Double = 0

    init(
        progress: Double,
        height: CGFloat = 8,
        color: Color = Color(hex: "1890FF"),
        backgroundColor: Color = Color.fmBg
    ) {
        self.progress = progress
        self.height = height
        self.color = color
        self.backgroundColor = backgroundColor
    }

    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .leading) {
                Rectangle()
                    .fill(backgroundColor)

                Rectangle()
                    .fill(color)
                    .frame(width: geometry.size.width * animatedProgress)
                    .animation(.spring(response: 0.5, dampingFraction: 0.7), value: animatedProgress)
            }
        }
        .frame(height: height)
        .cornerRadius(height / 2)
        .onAppear {
            animatedProgress = progress
        }
        .onChange(of: progress) { _, newValue in
            animatedProgress = newValue
        }
    }
}
