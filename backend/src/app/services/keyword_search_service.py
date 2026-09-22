"""
关键词智能检索服务
实现视频/音频时间点定位、文档搜索、关键词分析
"""

import re
import json
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from pathlib import Path
import jieba
from collections import Counter

from app.models.project import ProjectDocument, ProjectDocumentAsset
from app.config import settings


class KeywordSearchService:
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        # 修正：转写文本存储在 UPLOAD_DIR/transcripts/
        self.transcripts_dir = Path(settings.UPLOAD_DIR) / "transcripts"
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)

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

        返回：
        - 所有提到该关键词的材料
        - 视频/音频的精确时间点（HH:MM:SS）
        - 文档的匹配位置和上下文
        - 关键词时间线
        - 相关关键词推荐
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

        if not documents:
            return results

        # 2. 根据文件类型处理
        for doc in documents:
            try:
                file_type = (doc.file_type or "").lower()

                if file_type in {"video", "mp4", "mov", "avi", "mkv", "webm"} and include_videos:
                    timestamps = await self._search_in_video(doc, keyword)
                    results["video_timestamps"].extend(timestamps)

                elif file_type in {"audio", "mp3", "wav", "m4a", "ogg", "flac", "aac"} and include_audios:
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
            except Exception as e:
                print(f"搜索文档 {doc.id} 时出错: {e}")
                continue

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
            project_id, keyword, documents
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

        # 转写文件路径：修正为 doc_{id}.json（统一命名）
        transcript_file = self.transcripts_dir / f"doc_{doc.id}.json"

        asset = self.db.query(ProjectDocumentAsset).filter(
            ProjectDocumentAsset.document_id == doc.id,
            ProjectDocumentAsset.asset_type == "transcript",
        ).first()

        if asset and asset.content:
            try:
                transcript_data = json.loads(asset.content)
            except (TypeError, json.JSONDecodeError):
                transcript_data = []
        elif not transcript_file.exists():
            # 如果转写文件不存在，尝试从 extra_data 读取
            if doc.extra_data and isinstance(doc.extra_data, dict):
                transcript_data = doc.extra_data.get("transcript", [])
            else:
                # 没有转写数据，返回空
                return timestamps
        else:
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_data = json.load(f)
            except Exception as e:
                print(f"读取转写文件失败: {e}")
                return timestamps

        # 搜索关键词
        # transcript_data 格式:
        # [
        #   {"start": 0.5, "end": 3.2, "text": "这是布依族的传统..."},
        #   {"start": 3.2, "end": 6.8, "text": "他们的山歌很有特色..."},
        # ]

        for segment in transcript_data:
            if keyword in segment.get("text", ""):
                timestamps.append({
                    "video_id": doc.id,
                    "filename": doc.filename,
                    "timestamp": self._format_timestamp(segment["start"]),
                    "timestamp_seconds": segment["start"],
                    "context": segment["text"],
                    "match_position": segment["text"].find(keyword)
                })

        return timestamps

    async def _search_in_audio(self, doc: ProjectDocument, keyword: str) -> List[Dict]:
        """
        在音频中搜索关键词（逻辑同视频）
        """
        timestamps = []

        # 转写文件路径：修正为 doc_{id}.json（统一命名）
        transcript_file = self.transcripts_dir / f"doc_{doc.id}.json"

        asset = self.db.query(ProjectDocumentAsset).filter(
            ProjectDocumentAsset.document_id == doc.id,
            ProjectDocumentAsset.asset_type == "transcript",
        ).first()

        if asset and asset.content:
            try:
                transcript_data = json.loads(asset.content)
            except (TypeError, json.JSONDecodeError):
                transcript_data = []
        elif not transcript_file.exists():
            if doc.extra_data and isinstance(doc.extra_data, dict):
                transcript_data = doc.extra_data.get("transcript", [])
            else:
                return timestamps
        else:
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_data = json.load(f)
            except Exception as e:
                print(f"读取转写文件失败: {e}")
                return timestamps

        # 搜索关键词
        for segment in transcript_data:
            if keyword in segment.get("text", ""):
                timestamps.append({
                    "audio_id": doc.id,
                    "filename": doc.filename,
                    "timestamp": self._format_timestamp(segment["start"]),
                    "timestamp_seconds": segment["start"],
                    "context": segment["text"],
                    "match_position": segment["text"].find(keyword)
                })

        return timestamps

    async def _search_in_document(self, doc: ProjectDocument, keyword: str) -> List[Dict]:
        """
        在文档中搜索关键词
        """
        matches = []

        # 读取文档内容
        content = doc.text_content or ""

        if not content:
            return matches

        # 查找所有匹配位置
        for match in re.finditer(re.escape(keyword), content):
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end]

            # 计算在第几段
            paragraph_num = content[:match.start()].count('\n') + 1

            matches.append({
                "position": match.start(),
                "paragraph": paragraph_num,
                "context": context.strip()
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
        video_ts: List[Dict],
        audio_ts: List[Dict],
        docs: List[Dict]
    ) -> List[Dict]:
        """
        生成关键词时间线

        将所有提及按时间顺序排列
        """
        timeline = []

        # 从视频时间戳生成时间线项
        for ts in video_ts:
            timeline.append({
                "type": "video",
                "source": ts["filename"],
                "time": ts["timestamp"],
                "context": ts["context"]
            })

        # 从音频时间戳生成时间线项
        for ts in audio_ts:
            timeline.append({
                "type": "audio",
                "source": ts["filename"],
                "time": ts["timestamp"],
                "context": ts["context"]
            })

        # 从文档生成时间线项（文档没有时间，按段落顺序）
        for doc in docs:
            for match in doc["matches"]:
                timeline.append({
                    "type": "document",
                    "source": doc["filename"],
                    "paragraph": match["paragraph"],
                    "context": match["context"]
                })

        return timeline

    async def _get_related_keywords(
        self,
        project_id: int,
        keyword: str,
        documents: List[ProjectDocument]
    ) -> List[str]:
        """
        推荐相关关键词

        方法：
        1. 找到所有包含目标关键词的文本片段
        2. 提取这些片段中的其他高频词
        3. 排除常见停用词
        """
        related = []

        # 停用词列表（简化版）
        stopwords = set([
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都',
            '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会',
            '着', '没有', '看', '好', '自己', '这'
        ])

        # 收集包含关键词的所有文本
        related_texts = []
        for doc in documents:
            content = doc.text_content or ""
            if keyword in content:
                # 提取包含关键词的句子
                sentences = re.split(r'[。！？\n]', content)
                for sentence in sentences:
                    if keyword in sentence:
                        related_texts.append(sentence)

        if not related_texts:
            return related

        # 合并所有相关文本
        combined_text = ' '.join(related_texts)

        # 使用 jieba 分词
        words = jieba.cut(combined_text)

        # 统计词频
        word_freq = Counter()
        for word in words:
            word = word.strip()
            # 过滤：不是关键词本身、不是停用词、长度 >= 2
            if (word != keyword and
                word not in stopwords and
                len(word) >= 2 and
                not word.isdigit()):
                word_freq[word] += 1

        # 返回 Top 10 相关词
        related = [word for word, count in word_freq.most_common(10)]

        return related

    async def get_top_keywords(self, project_id: int, limit: int = 50) -> List[Dict]:
        """
        获取项目的 Top N 关键词
        """
        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        if not documents:
            return []

        # 停用词
        stopwords = set([
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都',
            '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会',
            '着', '没有', '看', '好', '自己', '这', '里', '个', '们', '为'
        ])

        # 合并所有文档内容
        all_text = ""
        for doc in documents:
            if doc.text_content:
                all_text += doc.text_content + " "

        # 分词
        words = jieba.cut(all_text)

        # 统计词频
        word_freq = Counter()
        for word in words:
            word = word.strip()
            if (word not in stopwords and
                len(word) >= 2 and
                not word.isdigit()):
                word_freq[word] += 1

        # 返回 Top N
        top_keywords = [
            {"keyword": word, "count": count}
            for word, count in word_freq.most_common(limit)
        ]

        return top_keywords

    async def get_keyword_timeline(self, project_id: int, keyword: str) -> List[Dict]:
        """
        获取关键词的时间线
        """
        # 先搜索关键词
        results = await self.search_keyword(
            project_id=project_id,
            keyword=keyword,
            include_videos=True,
            include_audios=True,
            include_documents=True
        )

        return results.get("timeline", [])
