# FieldMind 整合与实现计划

**日期**: 2026-08-02  
**目标**: 整合 Desktop App + Rebuild 后端，实现三大核心功能

---

## 一、当前状态检查 ✅

### 已安装的核心工具
- ✅ **Whisper** - 音视频转文字
- ✅ **FFmpeg** - 视频处理
- ✅ **OpenCV (cv2)** - 图像/视频处理
- ✅ **Redis** - 缓存和任务队列
- ✅ **Celery** - 异步任务
- ✅ **Neo4j** - 知识图谱
- ✅ **ChromaDB** - 向量数据库
- ✅ **LangChain** - AI 编排
- ✅ **Anthropic (Claude)** - AI 模型
- ✅ **OpenAI** - AI 模型

### 需要补充安装
- ❌ **Tesseract** - OCR 文字识别
- ❌ **PaddleOCR** - 中文 OCR（可选）
- ❌ **Scrapy** - 爬虫框架
- ❌ **Playwright** - 浏览器自动化
- ⚠️ **Qdrant/Milvus** - 可选（已有 ChromaDB）

---

## 二、整合方案架构

### 最终架构
```
┌─────────────────────────────────────────┐
│   Desktop FieldMindApp (SwiftUI)       │
│   - 原生 macOS 界面                     │
│   - 用户交互                            │
│   - 数据可视化                          │
└─────────────┬───────────────────────────┘
              │ HTTP API
              ↓
┌─────────────────────────────────────────┐
│   FieldMind-Rebuild Backend (FastAPI)  │
│   - 24个已有 API                        │
│   - 3个新增核心功能 API                 │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┼─────────┬────────────┐
    ↓         ↓         ↓            ↓
┌────────┐ ┌─────┐ ┌─────────┐ ┌──────────┐
│ Whisper│ │Neo4j│ │ChromaDB │ │ Claude   │
│ FFmpeg │ │     │ │         │ │ Opus 5   │
└────────┘ └─────┘ └─────────┘ └──────────┘
```

---

## 三、分步实施计划

### 阶段 0：环境准备（今天，30分钟）

#### 0.1 安装缺失的系统工具
```bash
# 安装 Tesseract OCR
brew install tesseract tesseract-lang

# 验证安装
tesseract --version
ffmpeg -version
whisper --help
```

#### 0.2 安装 Python 补充包
```bash
cd ~/FieldMind-Rebuild/fieldmind-backend

# OCR
pip install paddleocr

# 爬虫
pip install scrapy playwright
python -m playwright install

# 视频处理增强
pip install moviepy scenedetect

# 关键词检索增强
pip install rank-bm25

# 数据可视化
pip install plotly wordcloud pyecharts

# 报告生成
pip install python-docx weasyprint

# 网络搜索
pip install duckduckgo-search newspaper3k
```

#### 0.3 验证后端启动
```bash
cd ~/FieldMind-Rebuild/fieldmind-backend
python3 -m uvicorn app.main_simple:app --reload --port 8000

# 访问 http://localhost:8000/docs 查看 API 文档
```

---

### 阶段 1：项目整合（今天-明天，4小时）

#### 1.1 修改 Desktop App API 配置

**文件**: `~/Desktop/FieldMindApp/Sources/FieldMind/Services/APIService.swift`

```swift
class APIService {
    // 修改为指向 Rebuild 后端
    static let baseURL = "http://localhost:8000"
    
    // 测试连接
    static func testConnection() async throws -> Bool {
        let url = URL(string: "\(baseURL)/health")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return true
    }
}
```

#### 1.2 测试基础功能
- [ ] Desktop App 创建项目
- [ ] Desktop App 上传文档
- [ ] 查看后端日志确认处理
- [ ] Desktop App 查看知识图谱
- [ ] Desktop App 查看时间线

---

### 阶段 2：关键词智能检索系统（第1-2天，8-10小时）

#### 2.1 后端实现

**新建**: `~/FieldMind-Rebuild/fieldmind-backend/app/api/keyword_search.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.services.keyword_search_service import KeywordSearchService

router = APIRouter(prefix="/keyword-search")

@router.post("/projects/{project_id}/search")
async def search_by_keyword(
    project_id: int,
    keyword: str,
    include_videos: bool = True,
    include_audios: bool = True,
    include_documents: bool = True,
    db: Session = Depends(get_db)
):
    """
    关键词智能检索
    
    返回：
    - 所有提到该关键词的材料
    - 视频/音频的精确时间点
    - 关键词时间线
    - 相关关键词推荐
    """
    service = KeywordSearchService(db)
    results = await service.search_keyword(
        project_id=project_id,
        keyword=keyword,
        include_videos=include_videos,
        include_audios=include_audios,
        include_documents=include_documents
    )
    return results
```

**新建**: `~/FieldMind-Rebuild/fieldmind-backend/app/services/keyword_search_service.py`

```python
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import ProjectDocument
from app.services.document_converter import DocumentConverter
import json

class KeywordSearchService:
    def __init__(self, db: Session):
        self.db = db
    
    async def search_keyword(
        self,
        project_id: int,
        keyword: str,
        include_videos: bool = True,
        include_audios: bool = True,
        include_documents: bool = True
    ) -> Dict[str, Any]:
        """
        核心功能：关键词智能检索
        """
        results = {
            "keyword": keyword,
            "total_mentions": 0,
            "documents": [],
            "video_timestamps": [],
            "audio_timestamps": [],
            "timeline": [],
            "related_keywords": []
        }
        
        # 1. 查询项目所有文档
        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()
        
        for doc in documents:
            # 2. 根据文件类型处理
            if doc.file_type.startswith('video/') and include_videos:
                timestamps = await self._search_in_video(doc, keyword)
                results["video_timestamps"].extend(timestamps)
            
            elif doc.file_type.startswith('audio/') and include_audios:
                timestamps = await self._search_in_audio(doc, keyword)
                results["audio_timestamps"].extend(timestamps)
            
            elif include_documents:
                matches = await self._search_in_document(doc, keyword)
                if matches:
                    results["documents"].append({
                        "doc_id": doc.id,
                        "filename": doc.filename,
                        "matches": matches
                    })
        
        # 3. 计算总提及次数
        results["total_mentions"] = (
            len(results["video_timestamps"]) +
            len(results["audio_timestamps"]) +
            sum(len(d["matches"]) for d in results["documents"])
        )
        
        # 4. 生成关键词时间线
        results["timeline"] = await self._generate_keyword_timeline(
            results["video_timestamps"],
            results["audio_timestamps"],
            results["documents"]
        )
        
        # 5. 推荐相关关键词
        results["related_keywords"] = await self._get_related_keywords(
            project_id, keyword
        )
        
        return results
    
    async def _search_in_video(self, doc: ProjectDocument, keyword: str) -> List[Dict]:
        """
        在视频中搜索关键词
        
        步骤：
        1. 读取视频转写文本（Whisper 生成的带时间戳文本）
        2. 搜索关键词出现位置
        3. 返回时间戳和上下文
        """
        timestamps = []
        
        # 假设转写文本存储在 doc.metadata 或单独的表中
        transcript_file = f"/path/to/transcripts/{doc.id}.json"
        
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
            
            # transcript_data 格式:
            # [
            #   {"start": 0.5, "end": 3.2, "text": "这是布依族的传统..."},
            #   {"start": 3.2, "end": 6.8, "text": "他们的山歌很有特色..."},
            # ]
            
            for segment in transcript_data:
                if keyword in segment["text"]:
                    timestamps.append({
                        "video_id": doc.id,
                        "filename": doc.filename,
                        "timestamp": self._format_timestamp(segment["start"]),
                        "timestamp_seconds": segment["start"],
                        "context": segment["text"],
                        "match_position": segment["text"].find(keyword)
                    })
        
        except FileNotFoundError:
            # 如果转写文件不存在，触发异步转写
            pass
        
        return timestamps
    
    async def _search_in_audio(self, doc: ProjectDocument, keyword: str) -> List[Dict]:
        """
        在音频中搜索关键词（逻辑同视频）
        """
        return await self._search_in_video(doc, keyword)
    
    async def _search_in_document(self, doc: ProjectDocument, keyword: str) -> List[Dict]:
        """
        在文档中搜索关键词
        """
        matches = []
        
        # 读取文档内容
        content = doc.content or ""
        
        # 查找所有匹配位置
        for match in re.finditer(keyword, content):
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end]
            
            matches.append({
                "position": match.start(),
                "context": context
            })
        
        return matches
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        将秒数转换为 HH:MM:SS 格式
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    async def _generate_keyword_timeline(
        self, 
        video_ts: List, 
        audio_ts: List, 
        docs: List
    ) -> List[Dict]:
        """
        生成关键词时间线
        """
        # TODO: 实现时间线生成逻辑
        return []
    
    async def _get_related_keywords(self, project_id: int, keyword: str) -> List[str]:
        """
        推荐相关关键词
        """
        # TODO: 使用共现分析或词向量找相关词
        return []
```

#### 2.2 前端实现

**新建**: `~/Desktop/FieldMindApp/Sources/FieldMind/Views/KeywordSearchView.swift`

```swift
import SwiftUI

struct KeywordSearchView: View {
    @State private var keyword: String = ""
    @State private var searchResults: KeywordSearchResults?
    @State private var isSearching = false
    
    var body: some View {
        VStack(spacing: 20) {
            // 搜索框
            HStack {
                Image(systemName: "magnifyingglass")
                TextField("输入关键词搜索（如：布依族、民俗）", text: $keyword)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                
                Button("搜索") {
                    Task {
                        await performSearch()
                    }
                }
                .disabled(keyword.isEmpty || isSearching)
            }
            .padding()
            
            if isSearching {
                ProgressView("搜索中...")
            } else if let results = searchResults {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        // 统计信息
                        HStack {
                            Text("找到 \(results.totalMentions) 处提及")
                                .font(.headline)
                            Spacer()
                        }
                        .padding()
                        .background(Color.blue.opacity(0.1))
                        .cornerRadius(8)
                        
                        // 视频时间点
                        if !results.videoTimestamps.isEmpty {
                            VideoTimestampsSection(timestamps: results.videoTimestamps)
                        }
                        
                        // 音频时间点
                        if !results.audioTimestamps.isEmpty {
                            AudioTimestampsSection(timestamps: results.audioTimestamps)
                        }
                        
                        // 文档匹配
                        if !results.documents.isEmpty {
                            DocumentMatchesSection(documents: results.documents)
                        }
                        
                        // 相关关键词
                        if !results.relatedKeywords.isEmpty {
                            RelatedKeywordsSection(keywords: results.relatedKeywords) { keyword in
                                self.keyword = keyword
                                Task {
                                    await performSearch()
                                }
                            }
                        }
                    }
                    .padding()
                }
            }
        }
    }
    
    func performSearch() async {
        isSearching = true
        defer { isSearching = false }
        
        do {
            let results = try await APIService.shared.searchKeyword(
                projectId: AppState.shared.currentProjectId,
                keyword: keyword
            )
            searchResults = results
        } catch {
            print("搜索失败: \(error)")
        }
    }
}

struct VideoTimestampsSection: View {
    let timestamps: [VideoTimestamp]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("视频中的提及")
                .font(.headline)
            
            ForEach(timestamps, id: \.videoId) { ts in
                HStack {
                    Image(systemName: "play.circle.fill")
                        .foregroundColor(.blue)
                    
                    VStack(alignment: .leading) {
                        Text(ts.filename)
                            .font(.subheadline)
                        Text("时间点: \(ts.timestamp)")
                            .font(.caption)
                            .foregroundColor(.gray)
                        Text(ts.context)
                            .font(.caption)
                            .lineLimit(2)
                    }
                    
                    Spacer()
                    
                    Button("播放") {
                        // TODO: 跳转到视频播放，定位到时间点
                    }
                }
                .padding()
                .background(Color.gray.opacity(0.05))
                .cornerRadius(8)
            }
        }
    }
}

// TODO: 实现其他 Section 组件
```

---

### 阶段 3：在地文创分析引擎（第3-4天，10-12小时）

#### 3.1 后端实现

**新建**: `~/FieldMind-Rebuild/fieldmind-backend/app/api/creative_analysis.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.creative_analysis_service import CreativeAnalysisService

router = APIRouter(prefix="/creative-analysis")

@router.post("/projects/{project_id}/analyze")
async def analyze_creative_possibilities(
    project_id: int,
    keywords: List[str],
    mode: str = "creative",  # creative / business / academic
    db: Session = Depends(get_db)
):
    """
    在地文创分析引擎
    
    NOT 刻板的文创建议（❌）:
    - "制作山歌CD"
    - "开发文创产品"
    - "举办山歌表演"
    
    BUT 深度创意思考（✅）:
    - "山歌对唱互动体验"
    - "山歌剧本杀"
    - "山歌疗愈空间"
    - "山歌 × 电音融合"
    """
    service = CreativeAnalysisService(db)
    results = await service.analyze_creative_possibilities(
        project_id=project_id,
        keywords=keywords,
        mode=mode
    )
    return results
```

**新建**: `~/FieldMind-Rebuild/fieldmind-backend/app/services/creative_analysis_service.py`

```python
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from anthropic import Anthropic
import os

class CreativeAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    async def analyze_creative_possibilities(
        self,
        project_id: int,
        keywords: List[str],
        mode: str = "creative"
    ) -> Dict[str, Any]:
        """
        使用 Claude Opus 5 深度思考文创可能性
        
        核心：避免刻板建议，真正结合在地特色
        """
        
        # 1. 从数据库提取项目相关信息
        project_context = await self._get_project_context(project_id)
        
        # 2. 构建深度思考 Prompt
        prompt = self._build_creative_prompt(keywords, project_context, mode)
        
        # 3. 调用 Claude Opus 5
        response = self.anthropic.messages.create(
            model="claude-opus-5",
            max_tokens=16000,
            thinking={
                "type": "enabled",
                "budget_tokens": 10000  # 深度思考预算
            },
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # 4. 解析和结构化结果
        analysis = self._parse_creative_response(response)
        
        return analysis
    
    def _build_creative_prompt(
        self, 
        keywords: List[str], 
        context: str, 
        mode: str
    ) -> str:
        """
        构建创意分析 Prompt
        """
        keywords_str = "、".join(keywords)
        
        prompt = f"""
你是一位深谙乡村文化的创意策划专家。现在需要你基于调研数据，为"{keywords_str}"提供**真正有创意、接地气的文创建议**。

## 调研背景
{context}

## 核心要求

### ❌ 避免这些刻板建议：
- 制作XX纪念品、文创产品
- 举办XX表演、展览
- 开发XX旅游路线
- 建设XX文化馆

### ✅ 你应该这样思考：

1. **深度理解在地特色**
   - {keywords_str} 的独特性是什么？
   - 与其他地方的同类事物有何不同？
   - 背后的文化逻辑和生活方式是什么？

2. **寻找创新结合点**
   - 能否与当代年轻人的生活方式结合？
   - 能否与新技术（AR/VR/AI）结合？
   - 能否与其他文化形式跨界？
   - 能否创造新的体验方式？

3. **确保真实可行**
   - 是否尊重当地文化？
   - 是否有实际落地可能？
   - 当地人是否愿意参与？
   - 游客是否真的感兴趣？

## 输出格式

请以 JSON 格式返回分析结果：

```json
{{
  "cultural_elements": [
    {{
      "element": "布依族山歌",
      "uniqueness": "对歌形式独特，即兴创作能力强",
      "cultural_meaning": "社交、情感表达、传承的重要方式"
    }}
  ],
  "creative_possibilities": [
    {{
      "idea": "山歌对唱互动体验",
      "description": "游客学习基本对歌技巧，与当地人现场对唱，AI实时翻译和指导，录制专属山歌作品带走",
      "innovation_point": "从被动观赏到主动参与，从表演到真实社交",
      "feasibility_score": 85,
      "required_resources": ["3-5位当地歌手", "录音设备", "AI翻译系统"],
      "target_audience": "18-35岁年轻人，喜欢社交体验",
      "market_potential": "中高",
      "unique_value": "真正的文化交流，非刻板表演",
      "risks": ["歌手时间安排", "对歌难度控制"],
      "implementation_difficulty": "中等"
    }},
    {{
      "idea": "山歌剧本杀",
      "description": "将山歌融入剧本杀游戏，玩家通过对歌推进剧情、解谜、社交",
      "innovation_point": "游戏化 × 传统文化，Z世代接受度高",
      "feasibility_score": 75,
      "required_resources": ["剧本创作", "山歌素材库", "游戏场景"],
      "target_audience": "剧本杀爱好者、年轻人",
      "market_potential": "高",
      "unique_value": "全新的文化体验形式",
      "risks": ["剧本质量", "山歌与剧情融合难度"],
      "implementation_difficulty": "较高"
    }}
  ],
  "anti_patterns": [
    "❌ 制作山歌CD/音像制品 - 过时且无互动",
    "❌ 山歌广场表演 - 游客只是旁观者",
    "❌ 山歌文创周边 - 缺乏文化深度"
  ]
}}
```

请开始你的深度思考和创意分析。
"""
        return prompt
    
    async def _get_project_context(self, project_id: int) -> str:
        """
        提取项目相关信息作为背景
        """
        # TODO: 从数据库查询项目文档、知识图谱、关键词等
        return "项目背景信息..."
    
    def _parse_creative_response(self, response) -> Dict[str, Any]:
        """
        解析 Claude 的响应
        """
        # TODO: 解析 JSON 响应
        return {}
```

---

### 阶段 4：业态分析系统（第5-6天，10-12小时）

#### 4.1 后端实现

**新建**: `~/FieldMind-Rebuild/fieldmind-backend/app/api/business_analysis.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.business_analysis_service import BusinessAnalysisService

router = APIRouter(prefix="/business-analysis")

@router.post("/projects/{project_id}/analyze")
async def analyze_business_formats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    业态分析系统
    
    输出：
    1. 现有业态梳理
    2. 可能的新业态
    3. 可行性评分（有理有据）
    4. 所需资源和条件
    """
    service = BusinessAnalysisService(db)
    results = await service.analyze_business_formats(project_id)
    return results
```

**核心逻辑**: 与文创分析类似，使用 Claude Opus 5 深度分析调研数据，给出基于证据的业态建议。

---

### 阶段 5：Desktop App 新增页面（第7天，6-8小时）

#### 5.1 更新 MainAppView 侧边栏

```swift
// 添加新的导航项
NavigationLink(destination: KeywordSearchView()) {
    Label("关键词检索", systemImage: "magnifyingglass")
}

NavigationLink(destination: CreativeAnalysisView()) {
    Label("文创分析", systemImage: "lightbulb")
}

NavigationLink(destination: BusinessAnalysisView()) {
    Label("业态分析", systemImage: "chart.bar")
}
```

---

## 四、需要补充的插件评估

### 你提到的 9 个工具

| 工具 | 状态 | 建议 |
|------|------|------|
| **Whisper** | ✅ 已安装 | 保留，核心功能 |
| **FFmpeg** | ✅ 已安装 | 保留，视频处理必需 |
| **PaddleOCR** | ❌ 未装 | **建议安装**，中文OCR更好 |
| **Tesseract** | ❌ 未装 | **建议安装**，通用OCR |
| **Qdrant** | ❌ 未装 | 可选，已有 ChromaDB |
| **Milvus** | ❌ 未装 | 可选，已有 ChromaDB |
| **Neo4j** | ✅ 已有库 | 保留，知识图谱核心 |
| **Scrapy** | ❌ 未装 | **建议安装**，联网功能需要 |
| **Playwright** | ❌ 未装 | **建议安装**，动态网页爬取 |

### 建议的插件方案

**保留现有 33 个工具**，额外安装：
```bash
# OCR
brew install tesseract tesseract-lang
pip install paddleocr

# 爬虫
pip install scrapy playwright newspaper3k duckduckgo-search
python -m playwright install

# 视频处理增强
pip install moviepy scenedetect

# 数据分析和可视化
pip install plotly wordcloud pyecharts rank-bm25

# 报告生成
pip install python-docx weasyprint
```

**不需要安装**：
- Qdrant/Milvus（已有 ChromaDB，功能足够）

---

## 五、时间和里程碑

| 阶段 | 时间 | 输出 |
|------|------|------|
| 阶段0：环境准备 | 0.5天 | ✅ 工具安装完成 |
| 阶段1：项目整合 | 0.5天 | ✅ Desktop App 连接后端 |
| 阶段2：关键词检索 | 2天 | ✅ 视频时间点定位功能 |
| 阶段3：文创分析 | 2天 | ✅ AI 创意建议引擎 |
| 阶段4：业态分析 | 2天 | ✅ 业态可行性分析 |
| 阶段5：前端页面 | 1天 | ✅ 三个新页面 |
| **总计** | **8天** | **完整功能系统** |

---

## 六、下一步行动

### 立即开始（今天）

```bash
# 1. 安装工具
brew install tesseract tesseract-lang

# 2. 安装 Python 包
cd ~/FieldMind-Rebuild/fieldmind-backend
pip install paddleocr scrapy playwright moviepy scenedetect rank-bm25 plotly wordcloud python-docx weasyprint duckduckgo-search newspaper3k
python -m playwright install

# 3. 启动后端
python3 -m uvicorn app.main_simple:app --reload --port 8000

# 4. 测试 Desktop App 连接
# 打开 Xcode，运行 Desktop FieldMindApp
```

---

**准备好了吗？我们现在就开始整合！** 🚀
