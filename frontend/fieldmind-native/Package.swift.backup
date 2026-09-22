// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "FieldMindNative",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(
            name: "FieldMindNative",
            targets: ["FieldMindNative"]
        )
    ],
    targets: [
        .executableTarget(
            name: "FieldMindNative",
            dependencies: [],
            path: "Sources",
            resources: [
                .process("Resources")
            ]
        )
    ]
)
