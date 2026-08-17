import SwiftUI

// MARK: - Tooltip Position
enum TooltipPosition {
    case top
    case bottom
    case left
    case right
}

// MARK: - Tooltip View
struct TooltipView: View {
    let text: String
    let position: TooltipPosition

    var body: some View {
        Text(text)
            .font(.system(size: 12))
            .foregroundColor(.white)
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(Color.black.opacity(0.85))
            .cornerRadius(6)
    }
}

// MARK: - Tooltip Modifier
struct TooltipModifier: ViewModifier {
    let text: String
    let position: TooltipPosition
    @State private var isHovered: Bool = false

    func body(content: Content) -> some View {
        content
            .overlay(alignment: alignment) {
                if isHovered {
                    TooltipView(text: text, position: position)
                        .offset(x: offsetX, y: offsetY)
                        .transition(.opacity.combined(with: .scale(scale: 0.9)))
                        .zIndex(1002)
                }
            }
            .onHover { hovering in
                withAnimation(.easeInOut(duration: 0.15)) {
                    isHovered = hovering
                }
            }
    }

    private var alignment: Alignment {
        switch position {
        case .top: return .top
        case .bottom: return .bottom
        case .left: return .leading
        case .right: return .trailing
        }
    }

    private var offsetX: CGFloat {
        switch position {
        case .left: return -10
        case .right: return 10
        default: return 0
        }
    }

    private var offsetY: CGFloat {
        switch position {
        case .top: return -10
        case .bottom: return 10
        default: return 0
        }
    }
}

extension View {
    func tooltip(_ text: String, position: TooltipPosition = .top) -> some View {
        self.modifier(TooltipModifier(text: text, position: position))
    }
}

// MARK: - Loading Spinner
struct LoadingSpinner: View {
    @State private var isAnimating: Bool = false
    let size: CGFloat

    init(size: CGFloat = 20) {
        self.size = size
    }

    var body: some View {
        Circle()
            .trim(from: 0, to: 0.7)
            .stroke(Color(hex: "1890FF"), lineWidth: 2)
            .frame(width: size, height: size)
            .rotationEffect(Angle(degrees: isAnimating ? 360 : 0))
            .onAppear {
                withAnimation(.linear(duration: 1.0).repeatForever(autoreverses: false)) {
                    isAnimating = true
                }
            }
    }
}

// MARK: - Loading Dots
struct LoadingDots: View {
    @State private var animatingDot: Int = 0
    let dotCount: Int
    let dotSize: CGFloat
    let spacing: CGFloat

    init(dotCount: Int = 3, dotSize: CGFloat = 8, spacing: CGFloat = 6) {
        self.dotCount = dotCount
        self.dotSize = dotSize
        self.spacing = spacing
    }

    var body: some View {
        HStack(spacing: spacing) {
            ForEach(0..<dotCount, id: \.self) { index in
                Circle()
                    .fill(Color(hex: "1890FF"))
                    .frame(width: dotSize, height: dotSize)
                    .scaleEffect(animatingDot == index ? 1.2 : 0.8)
                    .opacity(animatingDot == index ? 1.0 : 0.4)
            }
        }
        .onAppear {
            startAnimation()
        }
    }

    private func startAnimation() {
        Timer.scheduledTimer(withTimeInterval: 0.3, repeats: true) { _ in
            withAnimation(.easeInOut(duration: 0.3)) {
                animatingDot = (animatingDot + 1) % dotCount
            }
        }
    }
}

// MARK: - Loading Overlay
struct LoadingOverlay: View {
    let message: String?

    init(message: String? = nil) {
        self.message = message
    }

    var body: some View {
        ZStack {
            Color.black.opacity(0.3)
                .ignoresSafeArea()

            VStack(spacing: 16) {
                LoadingSpinner(size: 40)

                if let message = message {
                    Text(message)
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText)
                }
            }
            .padding(24)
            .background(Color.white)
            .cornerRadius(12)
            .shadow(color: Color.black.opacity(0.1), radius: 20, x: 0, y: 10)
        }
        .transition(.opacity)
    }
}

// MARK: - Loading Manager
@MainActor
class LoadingManager: ObservableObject {
    static let shared = LoadingManager()

    @Published var isLoading: Bool = false
    @Published var message: String?

    private init() {}

    func show(message: String? = nil) {
        self.message = message
        withAnimation(.easeInOut(duration: 0.2)) {
            isLoading = true
        }
    }

    func hide() {
        withAnimation(.easeOut(duration: 0.2)) {
            isLoading = false
            message = nil
        }
    }
}

// MARK: - Loading Container
struct LoadingContainer: ViewModifier {
    @ObservedObject var manager: LoadingManager

    func body(content: Content) -> some View {
        ZStack {
            content

            if manager.isLoading {
                LoadingOverlay(message: manager.message)
                    .zIndex(1003)
            }
        }
    }
}

extension View {
    @MainActor
    func loading(manager: LoadingManager = LoadingManager.shared) -> some View {
        self.modifier(LoadingContainer(manager: manager))
    }
}

// MARK: - Skeleton Loading
struct SkeletonView: View {
    @State private var animationPhase: CGFloat = 0
    let width: CGFloat?
    let height: CGFloat

    init(width: CGFloat? = nil, height: CGFloat = 16) {
        self.width = width
        self.height = height
    }

    var body: some View {
        GeometryReader { geometry in
            let gradientWidth = geometry.size.width * 0.3

            Rectangle()
                .fill(Color.fmBg)
                .overlay(
                    LinearGradient(
                        gradient: Gradient(colors: [
                            Color.clear,
                            Color.white.opacity(0.5),
                            Color.clear
                        ]),
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                    .frame(width: gradientWidth)
                    .offset(x: animationPhase * (geometry.size.width + gradientWidth) - gradientWidth)
                )
                .clipShape(RoundedRectangle(cornerRadius: 4))
        }
        .frame(width: width, height: height)
        .onAppear {
            withAnimation(.linear(duration: 1.5).repeatForever(autoreverses: false)) {
                animationPhase = 1
            }
        }
    }
}

// MARK: - Skeleton Card
struct SkeletonCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 12) {
                SkeletonView(width: 48, height: 48)
                VStack(alignment: .leading, spacing: 6) {
                    SkeletonView(width: 120, height: 16)
                    SkeletonView(width: 80, height: 14)
                }
            }

            SkeletonView(height: 14)
            SkeletonView(width: 200, height: 14)
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }
}
