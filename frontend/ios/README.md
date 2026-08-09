# FieldMind iOS/macOS App

田野调查知识管理系统 - Swift原生应用

## 技术栈

- **语言**: Swift 6
- **UI框架**: SwiftUI
- **架构**: MVVM + Combine
- **数据持久化**: CoreData
- **网络**: Alamofire
- **本地AI**: CoreML

## 项目结构

```
FieldMind/
├── FieldMind.xcodeproj
├── FieldMind/
│   ├── App/
│   │   ├── FieldMindApp.swift          # 应用入口
│   │   └── ContentView.swift           # 主视图
│   │
│   ├── Models/                         # 数据模型
│   │   ├── Document.swift
│   │   ├── AudioRecording.swift
│   │   ├── Entity.swift
│   │   └── User.swift
│   │
│   ├── Views/                          # 视图
│   │   ├── Home/
│   │   │   ├── HomeView.swift
│   │   │   └── DocumentListView.swift
│   │   ├── Recording/
│   │   │   ├── AudioRecorderView.swift
│   │   │   └── VideoRecorderView.swift
│   │   ├── Search/
│   │   │   └── SearchView.swift
│   │   ├── KnowledgeGraph/
│   │   │   └── GraphView.swift
│   │   └── Settings/
│   │       └── SettingsView.swift
│   │
│   ├── ViewModels/                     # 视图模型
│   │   ├── DocumentViewModel.swift
│   │   ├── AudioViewModel.swift
│   │   └── SearchViewModel.swift
│   │
│   ├── Services/                       # 服务层
│   │   ├── APIService.swift           # 后端API通信
│   │   ├── AudioService.swift         # 音频录制
│   │   ├── DatabaseService.swift      # CoreData管理
│   │   └── SyncService.swift          # 数据同步
│   │
│   ├── CoreData/
│   │   ├── FieldMind.xcdatamodeld    # CoreData模型
│   │   └── PersistenceController.swift
│   │
│   ├── Utilities/                     # 工具类
│   │   ├── Extensions/
│   │   │   ├── String+Extension.swift
│   │   │   └── Date+Extension.swift
│   │   └── Constants.swift
│   │
│   └── Resources/                     # 资源文件
│       ├── Assets.xcassets
│       ├── Localizable.strings
│       └── Info.plist
│
└── FieldMindTests/                    # 测试
    ├── ViewModelTests/
    └── ServiceTests/
```

## 功能模块

### 1. 数据采集
- 📝 **文本输入**: Markdown编辑器
- 🎤 **音频录制**: 高质量音频录制，自动分段
- 📹 **视频录制**: 视频拍摄和压缩
- 📷 **照片采集**: 相机和相册
- 📄 **文档导入**: PDF、Word等

### 2. 本地存储
- **CoreData**: 结构化数据存储
- **文件系统**: 音视频文件管理
- **缓存**: 离线优先策略

### 3. 网络同步
- **上传队列**: 后台上传音视频
- **增量同步**: 智能同步策略
- **冲突解决**: 本地优先原则

### 4. 搜索功能
- **本地搜索**: CoreData查询
- **远程搜索**: 语义搜索API
- **混合搜索**: 本地+远程结合

### 5. 知识图谱
- **图可视化**: 交互式知识图谱
- **实体浏览**: 人物、地点、事件
- **关系探索**: 关联发现

## 核心代码示例

### AudioRecorderService
```swift
import AVFoundation
import Combine

class AudioRecorderService: NSObject, ObservableObject {
    @Published var isRecording = false
    @Published var recordingTime: TimeInterval = 0
    
    private var audioRecorder: AVAudioRecorder?
    private var timer: Timer?
    
    func startRecording() {
        let audioSession = AVAudioSession.sharedInstance()
        try? audioSession.setCategory(.record, mode: .default)
        try? audioSession.setActive(true)
        
        let url = getDocumentsDirectory()
            .appendingPathComponent("recording_\(Date().timeIntervalSince1970).m4a")
        
        let settings = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 44100,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]
        
        audioRecorder = try? AVAudioRecorder(url: url, settings: settings)
        audioRecorder?.record()
        
        isRecording = true
        startTimer()
    }
    
    func stopRecording() -> URL? {
        audioRecorder?.stop()
        isRecording = false
        stopTimer()
        
        return audioRecorder?.url
    }
}
```

### APIService
```swift
import Alamofire
import Combine

class APIService {
    static let shared = APIService()
    private let baseURL = "http://localhost:8000/api/v1"
    
    func uploadAudio(fileURL: URL) -> AnyPublisher<AudioUploadResponse, Error> {
        let url = "\(baseURL)/audio/upload"
        
        return Future { promise in
            AF.upload(multipartFormData: { multipartFormData in
                multipartFormData.append(fileURL, withName: "file")
            }, to: url)
            .responseDecodable(of: AudioUploadResponse.self) { response in
                switch response.result {
                case .success(let data):
                    promise(.success(data))
                case .failure(let error):
                    promise(.failure(error))
                }
            }
        }
        .eraseToAnyPublisher()
    }
    
    func transcribeAudio(fileId: String) -> AnyPublisher<TranscriptionResponse, Error> {
        let url = "\(baseURL)/audio/transcribe/\(fileId)"
        
        return Future { promise in
            AF.request(url, method: .post)
                .responseDecodable(of: TranscriptionResponse.self) { response in
                    switch response.result {
                    case .success(let data):
                        promise(.success(data))
                    case .failure(let error):
                        promise(.failure(error))
                    }
                }
        }
        .eraseToAnyPublisher()
    }
}
```

## 开发环境

### 要求
- macOS 14.0+
- Xcode 16.0+
- iOS 17.0+ / macOS 14.0+
- Swift 6.0+

### 依赖管理
使用 **Swift Package Manager** (SPM)

```swift
dependencies: [
    .package(url: "https://github.com/Alamofire/Alamofire.git", from: "5.9.0"),
    .package(url: "https://github.com/kishikawakatsumi/KeychainAccess.git", from: "4.2.2"),
]
```

## 构建和运行

### 1. 打开项目
```bash
cd fieldmind-ios
open FieldMind.xcodeproj
```

### 2. 配置后端地址
编辑 `Constants.swift`:
```swift
enum APIConfig {
    static let baseURL = "http://localhost:8000/api/v1"
}
```

### 3. 运行应用
- 选择模拟器或真机
- 点击 Run (⌘R)

## CoreData模型

### Document Entity
```
- id: UUID
- title: String
- content: String
- type: String (text/audio/video/pdf)
- createdAt: Date
- updatedAt: Date
- isSynced: Bool
```

### AudioRecording Entity
```
- id: UUID
- localURL: String
- duration: Double
- transcription: String?
- createdAt: Date
- isSynced: Bool
```

## 架构模式

### MVVM + Combine
```
View → ViewModel → Service → API/CoreData
  ↓        ↓          ↓
  Combine Publishers
```

### 数据流
1. **View** 触发用户操作
2. **ViewModel** 处理业务逻辑
3. **Service** 执行API调用或数据操作
4. **Combine** 响应式更新UI

## 测试

### 单元测试
```bash
# 运行测试
xcodebuild test -scheme FieldMind -destination 'platform=iOS Simulator,name=iPhone 15'
```

### UI测试
```bash
xcodebuild test -scheme FieldMind -destination 'platform=iOS Simulator,name=iPhone 15' -only-testing:FieldMindUITests
```

## 发布

### 1. 版本号
在 `Info.plist` 中更新版本号

### 2. 构建
```bash
xcodebuild archive -scheme FieldMind -archivePath ./build/FieldMind.xcarchive
```

### 3. 导出IPA
```bash
xcodebuild -exportArchive -archivePath ./build/FieldMind.xcarchive -exportPath ./build -exportOptionsPlist ExportOptions.plist
```

---

**开发者**: FieldMind Team  
**最后更新**: 2026-07-29
