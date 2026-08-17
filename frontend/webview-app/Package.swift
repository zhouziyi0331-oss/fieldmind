// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "FieldMindWebView",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(
            name: "FieldMindWebView",
            targets: ["FieldMindWebView"])
    ],
    targets: [
        .executableTarget(
            name: "FieldMindWebView",
            path: "Sources")
    ]
)
