// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "FieldMind",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(
            name: "FieldMind",
            targets: ["FieldMind"])
    ],
    dependencies: [
        // 移除 Alamofire，使用原生 URLSession
    ],
    targets: [
        .executableTarget(
            name: "FieldMind",
            dependencies: [],
            path: "Sources/FieldMind",
            swiftSettings: [
                .unsafeFlags(["-parse-as-library"])
            ])
    ]
)
