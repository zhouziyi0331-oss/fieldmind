"""
对话增强记忆服务 - Context-Aware Conversation
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from app.services.vectorization_service_complete import VectorizationService
from app.services.conversation_history_manager import ConversationHistoryManager
from app.models.analysis import AnalysisResult
from app.models.project import ProjectDocument

logger = logging.getLogger(__name__)

# 全局对话历史管理器
conversation_history = ConversationHistoryManager(max_history=20)


class ConversationMemoryService:
    """对话记忆服务 - 让对话带着项目上下文"""

    def __init__(self, db: Session, use_workflow_engine: bool = True):
        self.db = db
        self.vectorizer = VectorizationService()
        self.history_manager = conversation_history
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def prepare_context(
        self,
        project_id: int,
        query: str,
        include_documents: bool = True,
        include_analyses: bool = True,
        include_chunks: bool = True
    ) -> Dict[str, Any]:
        """
        准备对话上下文

        为AI对话准备完整的项目背景，包括：
        - 项目文档列表
        - 历史分析结果
        - 相关的chunks（语义检索）

        Args:
            project_id: 项目ID
            query: 用户查询
            include_documents: 是否包含文档列表
            include_analyses: 是否包含历史分析
            include_chunks: 是否包含相关chunks

        Returns:
            完整的上下文信息
        """
        context = {
            'project_id': project_id,
            'query': query,
            'timestamp': datetime.utcnow().isoformat()
        }

        # 1. 项目文档列表
        if include_documents:
            context['documents'] = self._get_project_documents(project_id)

        # 2. 历史分析结果
        if include_analyses:
            context['analyses'] = self._get_recent_analyses(project_id, limit=5)

        # 3. 相关chunks（语义检索）
        if include_chunks:
            context['relevant_chunks'] = self._search_relevant_chunks(
                project_id,
                query,
                top_k=10
            )

        # 4. 项目统计信息
        context['statistics'] = self._get_project_statistics(project_id)

        return context

    def _get_project_documents(self, project_id: int) -> List[Dict[str, Any]]:
        """获取项目文档列表"""
        docs = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'completed'
        ).limit(20).all()

        return [
            {
                'id': doc.id,
                'filename': doc.filename,
                'file_type': doc.file_type,
                'created_at': doc.created_at.isoformat() if doc.created_at else None
            }
            for doc in docs
        ]

    def _get_recent_analyses(
        self,
        project_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """获取最近的分析结果"""
        analyses = self.db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id
        ).order_by(
            AnalysisResult.created_at.desc()
        ).limit(limit).all()

        return [
            {
                'id': analysis.id,
                'type': analysis.analysis_type,
                'title': analysis.title,
                'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
                'summary': self._summarize_analysis(analysis)
            }
            for analysis in analyses
        ]

    def _summarize_analysis(self, analysis: AnalysisResult) -> str:
        """生成分析结果摘要"""
        result = analysis.result

        if analysis.analysis_type == 'keyword_search':
            doc_count = len(result.get('documents', []))
            return f"关键词检索，找到{doc_count}个匹配"

        elif analysis.analysis_type == 'creative':
            idea_count = len(result.get('creative_possibilities', []))
            return f"文创分析，生成{idea_count}个创意建议"

        elif analysis.analysis_type == 'business':
            format_count = len(result.get('suggested_formats', []))
            return f"业态分析，推荐{format_count}个业态"

        return "分析完成"

    def _search_relevant_chunks(
        self,
        project_id: int,
        query: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索相关的chunks"""
        try:
            # 降低阈值以适应TF-IDF
            results = self.vectorizer.semantic_search(
                query=query,
                project_id=project_id,
                db=self.db,
                top_k=top_k,
                threshold=0.01  # 降低阈值
            )

            # 如果语义搜索没结果，尝试关键词搜索
            if not results:
                logger.info(f"语义搜索无结果，尝试关键词搜索")
                from app.services.vectorization_service_complete import DocumentChunk
                import re

                # 提取查询中的关键词（简单分词）
                # 移除标点符号，按字分割，提取2-4字的词
                text_only = re.sub(r'[，。？！、]', '', query)

                # 提取可能的关键词（2-4字的连续字符）
                keywords = []
                for i in range(len(text_only)):
                    for length in [4, 3, 2]:  # 优先提取长词
                        if i + length <= len(text_only):
                            word = text_only[i:i+length]
                            if word and word not in keywords:
                                keywords.append(word)
                                if len(keywords) >= 5:
                                    break
                    if len(keywords) >= 5:
                        break

                logger.info(f"提取的关键词: {keywords[:5]}")

                found_chunks = set()  # 避免重复
                for keyword in keywords[:5]:
                    chunks = self.db.query(DocumentChunk).filter(
                        DocumentChunk.project_id == project_id,
                        DocumentChunk.text.like(f'%{keyword}%')
                    ).limit(3).all()

                    for chunk in chunks:
                        if chunk.chunk_id not in found_chunks:
                            found_chunks.add(chunk.chunk_id)
                            results.append({
                                'chunk_id': chunk.chunk_id,
                                'text': chunk.text,
                                'similarity': 0.5,
                                'document_id': chunk.document_id,
                                'chunk_index': chunk.chunk_index
                            })

                logger.info(f"关键词搜索找到 {len(results)} 个结果")

            return [
                {
                    'chunk_id': r['chunk_id'],
                    'text': r['text'][:200] + '...' if len(r['text']) > 200 else r['text'],
                    'full_text': r['text'],  # 保留完整文本
                    'similarity': r['similarity'],
                    'document_id': r.get('document_id'),
                    'chunk_index': r.get('chunk_index', 0)
                }
                for r in results[:top_k]
            ]

        except Exception as e:
            logger.error(f"搜索chunks失败: {e}")
            return []

    def _get_project_statistics(self, project_id: int) -> Dict[str, Any]:
        """获取项目统计信息"""
        from app.services.vectorization_service_complete import DocumentChunk

        doc_count = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).count()

        chunk_count = self.db.query(DocumentChunk).filter(
            DocumentChunk.project_id == project_id
        ).count()

        analysis_count = self.db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id
        ).count()

        return {
            'total_documents': doc_count,
            'total_chunks': chunk_count,
            'total_analyses': analysis_count
        }

    def generate_contextualized_response(
        self,
        project_id: int,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成带上下文的回答

        Args:
            project_id: 项目ID
            query: 用户问题
            context: 预先准备的上下文（可选）

        Returns:
            包含回答和引用来源的结果
        """
        # 1. 准备上下文（如果未提供）
        if context is None:
            context = self.prepare_context(project_id, query)

        # 2. 构建提示词
        prompt = self._build_prompt(query, context)

        # 3. 调用LLM生成回答（这里简化处理）
        response = self._generate_response(prompt, context)

        # 4. 标注引用来源
        response_with_citations = self._add_citations(response, context)

        # 添加到对话历史
        self.history_manager.add_conversation(
            project_id=project_id,
            query=query,
            response=response_with_citations
        )

        return response_with_citations

    def _build_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """构建带上下文的提示词"""
        prompt_parts = []

        # 对话历史
        project_id = context.get('project_id')
        if project_id:
            history_context = self.history_manager.get_context_for_prompt(project_id, last_n=3)
            if history_context:
                prompt_parts.append(history_context)

        # 项目信息
        stats = context.get('statistics', {})
        prompt_parts.append(f"项目背景: 共有{stats.get('total_documents', 0)}个文档，"
                          f"{stats.get('total_chunks', 0)}个文本片段，"
                          f"{stats.get('total_analyses', 0)}次分析。")

        # 最近分析
        analyses = context.get('analyses', [])
        if analyses:
            prompt_parts.append("\n最近的分析:")
            for analysis in analyses[:3]:
                prompt_parts.append(f"- {analysis['title']}: {analysis['summary']}")

        # 相关chunks
        chunks = context.get('relevant_chunks', [])
        if chunks:
            prompt_parts.append("\n相关材料:")
            for idx, chunk in enumerate(chunks[:5], 1):
                prompt_parts.append(f"{idx}. {chunk['text']} (相似度: {chunk['similarity']:.2f})")

        # 用户问题
        prompt_parts.append(f"\n用户问题: {query}")
        prompt_parts.append("\n请基于以上项目背景和材料回答，并标注引用来源。")

        return "\n".join(prompt_parts)

    def _generate_response(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成回答（增强版本）

        根据上下文生成高质量回答
        """
        chunks = context.get('relevant_chunks', [])
        analyses = context.get('analyses', [])
        statistics = context.get('statistics', {})
        query = context.get('query', '')

        # 构建更详细的回答
        answer_parts = []

        # 1. 如果有相关chunks，提取并整合关键信息
        if chunks:
            answer_parts.append("根据项目材料，我找到以下相关信息：\n\n")

            for idx, chunk in enumerate(chunks[:5], 1):
                full_text = chunk.get('full_text', chunk.get('text', ''))
                similarity = chunk['similarity']

                # 提取关键句子
                sentences = full_text.replace('\n', '').split('。')
                key_sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10][:2]

                if key_sentences:
                    content = '。'.join(key_sentences) + '。'
                    answer_parts.append(f"**{idx}.** {content}\n")
                    if similarity > 0:
                        answer_parts.append(f"   _（相关度: {similarity:.2f}）_\n\n")

            # 添加总结
            answer_parts.append(f"\n**总结：** 基于以上 {len(chunks)} 段材料，")

            # 尝试提取关键词作为答案要点
            all_text = ' '.join([c.get('full_text', c.get('text', '')) for c in chunks[:3]])
            if '类型' in query or '有哪些' in query:
                # 如果问题是关于类型/列举，尝试提取列表
                types_found = self._extract_types_from_text(all_text, query)
                if types_found:
                    answer_parts.append(f"可以总结出以下要点：\n")
                    for t in types_found:
                        answer_parts.append(f"- {t}\n")
                else:
                    answer_parts.append("项目材料中包含相关描述，建议查看上述来源获取详细信息。")
            else:
                answer_parts.append("项目材料中包含相关信息，详见上述内容。")

        # 2. 如果没有chunks但有分析结果
        elif analyses:
            answer_parts.append("根据历史分析结果：\n\n")
            for idx, analysis in enumerate(analyses[:3], 1):
                title = analysis.get('title', '')
                summary = analysis.get('summary', '')
                answer_parts.append(f"**{idx}.** {title}\n   {summary}\n\n")
            answer_parts.append("\n建议：可以查看完整分析报告获取更多细节。")

        # 3. 如果都没有
        else:
            answer_parts.append(
                f"抱歉，在当前项目的 {statistics.get('total_documents', 0)} 份文档和 "
                f"{statistics.get('total_chunks', 0)} 个文本片段中，暂未找到直接相关的信息。\n\n"
                "建议：\n"
                "- 尝试换个角度或关键词重新提问\n"
                "- 上传更多相关文档\n"
                "- 查看项目中已有的其他分析"
            )

        answer = "".join(answer_parts)

        # 计算置信度
        confidence = 0.3  # 基础置信度
        if chunks:
            # 根据chunk数量和相似度提升置信度
            avg_similarity = sum(c['similarity'] for c in chunks[:3]) / min(len(chunks), 3)
            confidence = 0.5 + avg_similarity * 0.4
        elif analyses:
            confidence = 0.6

        return {
            'answer': answer,
            'confidence': min(confidence, 1.0),
            'sources': {
                'chunks': [c['chunk_id'] for c in chunks[:5]],
                'analyses': [a['id'] for a in analyses[:3]]
            },
            'has_sources': len(chunks) > 0 or len(analyses) > 0,
            'chunk_count': len(chunks),
            'analysis_count': len(analyses)
        }

    def _extract_types_from_text(self, text: str, query: str) -> List[str]:
        """从文本中提取类型/列表项"""
        types = []

        # 简单的模式匹配提取
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # 查找包含数字、bullet point或"："的行
            if any(marker in line for marker in ['1.', '2.', '3.', '•', '○', '一、', '二、', '三、', '：']):
                # 清理并提取内容
                cleaned = line.lstrip('0123456789.•○一二三四五、 ')
                if len(cleaned) > 5 and len(cleaned) < 100:
                    types.append(cleaned)

            if len(types) >= 5:  # 最多提取5个
                break

        return types

    def _add_citations(
        self,
        response: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """为回答添加引用标注（增强版）"""
        sources = response.get('sources', {})
        citations = []

        # 添加chunk引用
        chunk_ids = sources.get('chunks', [])
        relevant_chunks = context.get('relevant_chunks', [])

        for chunk_id in chunk_ids:
            matching_chunk = next(
                (c for c in relevant_chunks if c['chunk_id'] == chunk_id),
                None
            )
            if matching_chunk:
                # 提取关键句子作为引用片段
                text = matching_chunk['text']
                sentences = text.split('。')
                key_sentence = sentences[0] + '。' if sentences else text[:100]

                citations.append({
                    'type': 'chunk',
                    'id': chunk_id,
                    'text': matching_chunk['text'],
                    'key_excerpt': key_sentence,  # 关键摘录
                    'similarity': matching_chunk['similarity'],
                    'document_id': matching_chunk.get('document_id'),
                    'position': f"第{matching_chunk.get('chunk_index', 0) + 1}段",
                    'confidence': 'high' if matching_chunk['similarity'] > 0.7 else 'medium'
                })

        # 添加分析引用
        analysis_ids = sources.get('analyses', [])
        recent_analyses = context.get('analyses', [])

        for analysis_id in analysis_ids:
            matching_analysis = next(
                (a for a in recent_analyses if a['id'] == analysis_id),
                None
            )
            if matching_analysis:
                citations.append({
                    'type': 'analysis',
                    'id': analysis_id,
                    'title': matching_analysis['title'],
                    'summary': matching_analysis['summary'],
                    'created_at': matching_analysis.get('created_at'),
                    'confidence': 'high'
                })

        # 按置信度排序
        citations.sort(key=lambda x: (
            1 if x.get('confidence') == 'high' else 0,
            x.get('similarity', 0)
        ), reverse=True)

        response['citations'] = citations
        response['citation_count'] = len(citations)
        response['has_high_confidence_sources'] = any(
            c.get('confidence') == 'high' for c in citations
        )

        return response

    def save_conversation(
        self,
        project_id: int,
        query: str,
        response: Dict[str, Any]
    ) -> int:
        """
        保存对话历史到项目知识库

        对话内容作为"第四层分析"保存，下次对话时可以引用
        """
        from app.models.analysis import AnalysisResult

        conversation_record = AnalysisResult(
            project_id=project_id,
            analysis_type='conversation',
            title=f'对话: {query[:50]}...',
            parameters={'query': query},
            result={
                'query': query,
                'answer': response.get('answer'),
                'citations': response.get('citations', []),
                'confidence': response.get('confidence')
            }
        )

        self.db.add(conversation_record)
        self.db.commit()

        logger.info(f"对话已保存为分析记录: {conversation_record.id}")

        return conversation_record.id
