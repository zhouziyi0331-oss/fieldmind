"""
SuperKnowledgeAgent - Advanced Knowledge Graph Construction and Query Agent

⚠️ 已废弃：此Agent将在v2.0中移除，请使用 app.tools.knowledge.graphrag_query

This agent integrates multiple knowledge graph plugins (graphrag, graphiti, cognee)
to provide superior knowledge extraction, temporal reasoning, and cognitive mapping.

Capabilities:
- Multi-strategy knowledge graph construction
- Temporal relationship tracking
- Cognitive reasoning over knowledge
- Entity extraction and relationship mapping
- Community detection and hierarchical summarization

Integration Strategy:
- Primary: GraphRAG for comprehensive entity/relationship extraction
- Secondary: Graphiti for temporal graph evolution tracking
- Tertiary: Cognee for cognitive reasoning and semantic connections
- Automatic fallback if primary plugin fails
- Result fusion for enhanced accuracy

Author: FieldMind Agent Mesh Team
Date: 2026-08-14
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time

from .base_agent import AgentBase, AgentRole, AgentStatus, AgentTask, AgentResult
from .agent_mesh import AgentState
from app.services.plugins.plugin_interface import (
    PluginInput,
    PluginOutput,
    PluginContext,
    PluginExecutionStatus,
    create_plugin_input
)
from app.services.plugins.plugin_loader import PluginLoader, LoadStrategy
from app.services.plugins.plugin_adapter import AdapterFactory
from app.services.plugins.plugin_registry import PluginRegistry
from app.utils.deprecation import deprecated


logger = logging.getLogger(__name__)


class KnowledgeGraphStrategy(Enum):
    """Strategy for knowledge graph construction"""
    COMPREHENSIVE = "comprehensive"  # Use all available plugins, merge results
    FAST = "fast"  # Use fastest plugin only
    TEMPORAL = "temporal"  # Focus on temporal relationships (Graphiti)
    COGNITIVE = "cognitive"  # Focus on cognitive reasoning (Cognee)
    HIERARCHICAL = "hierarchical"  # Focus on communities (GraphRAG)


class KnowledgeQueryType(Enum):
    """Types of knowledge queries"""
    ENTITY_EXTRACTION = "entity_extraction"
    RELATIONSHIP_MAPPING = "relationship_mapping"
    COMMUNITY_DETECTION = "community_detection"
    TEMPORAL_EVOLUTION = "temporal_evolution"
    SEMANTIC_SEARCH = "semantic_search"
    GRAPH_REASONING = "graph_reasoning"


@dataclass
class KnowledgeGraphResult:
    """Result from knowledge graph operations"""
    entities: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    communities: List[Dict[str, Any]] = field(default_factory=list)
    temporal_events: List[Dict[str, Any]] = field(default_factory=list)
    cognitive_insights: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    source_plugins: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    confidence_score: float = 0.0

    # Graph statistics
    entity_count: int = 0
    relationship_count: int = 0
    community_count: int = 0

    def merge(self, other: 'KnowledgeGraphResult') -> 'KnowledgeGraphResult':
        """Merge two knowledge graph results, deduplicating entities/relationships"""
        merged = KnowledgeGraphResult()

        # Merge entities (deduplicate by name+type)
        entity_keys = set()
        for entity in self.entities + other.entities:
            key = (entity.get('name', ''), entity.get('type', ''))
            if key not in entity_keys:
                merged.entities.append(entity)
                entity_keys.add(key)

        # Merge relationships (deduplicate by source+target+type)
        rel_keys = set()
        for rel in self.relationships + other.relationships:
            key = (rel.get('source', ''), rel.get('target', ''), rel.get('type', ''))
            if key not in rel_keys:
                merged.relationships.append(rel)
                rel_keys.add(key)

        # Merge communities, temporal events, cognitive insights
        merged.communities = self.communities + other.communities
        merged.temporal_events = self.temporal_events + other.temporal_events
        merged.cognitive_insights = self.cognitive_insights + other.cognitive_insights

        # Combine metadata
        merged.source_plugins = list(set(self.source_plugins + other.source_plugins))
        merged.execution_time = self.execution_time + other.execution_time
        merged.confidence_score = (self.confidence_score + other.confidence_score) / 2

        # Update statistics
        merged.entity_count = len(merged.entities)
        merged.relationship_count = len(merged.relationships)
        merged.community_count = len(merged.communities)

        return merged

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for AgentResult"""
        return {
            'entities': self.entities,
            'relationships': self.relationships,
            'communities': self.communities,
            'temporal_events': self.temporal_events,
            'cognitive_insights': self.cognitive_insights,
            'source_plugins': self.source_plugins,
            'execution_time': self.execution_time,
            'confidence_score': self.confidence_score,
            'entity_count': self.entity_count,
            'relationship_count': self.relationship_count,
            'community_count': self.community_count
        }


@deprecated(
    reason="SuperAgent架构已被6-Agent v2替代",
    replacement="app.tools.knowledge.graphrag_query",
    version="2.0"
)
class SuperKnowledgeAgent(AgentBase):
    """
    SuperKnowledgeAgent - Elite knowledge graph construction and reasoning

    This agent demonstrates 1+1>2 synergistic effects by:
    1. Using multiple knowledge graph plugins in parallel
    2. Merging and cross-validating results
    3. Automatic fallback and error recovery
    4. Specialized strategies for different query types
    5. Deep integration with the plugin system
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        registry: Optional[PluginRegistry] = None,
        loader: Optional[PluginLoader] = None
    ):
        """Initialize SuperKnowledgeAgent with plugin integration"""

        # Plugin system integration (before super().__init__)
        self.registry = registry or PluginRegistry.get_instance()
        self.loader = loader or PluginLoader(
            registry=self.registry,
            strategy=LoadStrategy.LAZY
        )

        # Knowledge graph plugin capabilities
        self.kg_capabilities = {
            'graph_rag': 'graphrag',
            'temporal_graph': 'graphiti',
            'cognitive_graph': 'cognee'
        }

        # Execution statistics
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'plugin_usage': {},
            'average_execution_time': 0.0,
            'entities_extracted': 0,
            'relationships_mapped': 0
        }

        # Initialize base agent
        super().__init__(agent_id=agent_id)

        logger.info(f"SuperKnowledgeAgent initialized: {self.agent_id}")

    @property
    def role(self) -> AgentRole:
        """Return agent role"""
        return AgentRole.KNOWLEDGE

    @property
    def name(self) -> str:
        """Return agent name"""
        return "超级知识图谱Agent"

    @property
    def description(self) -> str:
        """Return agent description"""
        return "整合多个知识图谱插件的精英Agent，支持实体提取、关系映射、社区发现、时序追踪和认知推理"

    @property
    def capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return [
            "entity_extraction",
            "relationship_mapping",
            "community_detection",
            "temporal_evolution",
            "semantic_search",
            "graph_reasoning",
            "multi_plugin_fusion",
            "automatic_fallback"
        ]

    def _initialize_tools(self):
        """Initialize agent tools"""
        # SuperKnowledgeAgent uses plugin system, not traditional tools
        self.tools = {
            'plugin_loader': self.loader,
            'plugin_registry': self.registry,
            'adapter_factory': AdapterFactory
        }

    def _execute_task_impl(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute task implementation (synchronous wrapper for async operations)

        Task input_data format:
        {
            'query_type': KnowledgeQueryType,
            'content': str or List[str],
            'strategy': KnowledgeGraphStrategy (optional),
            'parameters': Dict (optional)
        }
        """
        # Run async operation synchronously
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new task
            future = asyncio.ensure_future(self._execute_task_async(task))
            # Wait for completion
            while not future.done():
                time.sleep(0.01)
            result = future.result()
        else:
            result = loop.run_until_complete(self._execute_task_async(task))

        return result

    async def _execute_task_async(self, task: AgentTask) -> Dict[str, Any]:
        """
        Async task execution implementation
        """
        try:
            input_data = task.input_data

            query_type_str = input_data.get('query_type', 'entity_extraction')
            query_type = KnowledgeQueryType(query_type_str) if isinstance(query_type_str, str) else query_type_str

            content = input_data.get('content', '')

            strategy_str = input_data.get('strategy', 'comprehensive')
            strategy = KnowledgeGraphStrategy(strategy_str) if isinstance(strategy_str, str) else strategy_str

            parameters = input_data.get('parameters', {})

            logger.info(f"Processing knowledge query: {query_type}, strategy: {strategy}")

            # Route to appropriate handler
            if query_type == KnowledgeQueryType.ENTITY_EXTRACTION:
                result = await self.extract_entities(content, strategy, parameters)
            elif query_type == KnowledgeQueryType.RELATIONSHIP_MAPPING:
                result = await self.map_relationships(content, strategy, parameters)
            elif query_type == KnowledgeQueryType.COMMUNITY_DETECTION:
                result = await self.detect_communities(content, strategy, parameters)
            elif query_type == KnowledgeQueryType.TEMPORAL_EVOLUTION:
                result = await self.track_temporal_evolution(content, strategy, parameters)
            elif query_type == KnowledgeQueryType.SEMANTIC_SEARCH:
                result = await self.semantic_search(content, parameters)
            elif query_type == KnowledgeQueryType.GRAPH_REASONING:
                result = await self.reason_over_graph(content, parameters)
            else:
                raise ValueError(f"Unknown query type: {query_type}")

            # Update statistics
            self.stats['total_queries'] += 1
            self.stats['successful_queries'] += 1
            self.stats['entities_extracted'] += result.entity_count
            self.stats['relationships_mapped'] += result.relationship_count

            return result.to_dict()

        except Exception as e:
            logger.error(f"Error processing knowledge query: {e}", exc_info=True)
            self.stats['failed_queries'] += 1
            raise

    async def extract_entities(
        self,
        content: str,
        strategy: KnowledgeGraphStrategy,
        parameters: Dict[str, Any]
    ) -> KnowledgeGraphResult:
        """Extract entities from text using configured strategy"""

        start_time = time.time()

        if strategy == KnowledgeGraphStrategy.COMPREHENSIVE:
            result = await self._comprehensive_extraction(content, parameters)
        elif strategy == KnowledgeGraphStrategy.FAST:
            result = await self._fast_extraction(content, parameters)
        elif strategy == KnowledgeGraphStrategy.COGNITIVE:
            result = await self._cognitive_extraction(content, parameters)
        else:
            result = await self._fast_extraction(content, parameters)

        result.execution_time = time.time() - start_time
        return result

    async def map_relationships(
        self,
        content: str,
        strategy: KnowledgeGraphStrategy,
        parameters: Dict[str, Any]
    ) -> KnowledgeGraphResult:
        """Map relationships between entities"""

        start_time = time.time()

        # GraphRAG is strongest at relationship mapping
        result = await self._execute_graphrag(content, parameters, focus='relationships')

        # If comprehensive strategy, enhance with temporal relationships
        if strategy == KnowledgeGraphStrategy.COMPREHENSIVE:
            try:
                temporal_result = await self._execute_graphiti(content, parameters)
                result = result.merge(temporal_result)
            except Exception as e:
                logger.warning(f"Temporal enhancement failed: {e}")

        result.execution_time = time.time() - start_time
        return result

    async def detect_communities(
        self,
        content: str,
        strategy: KnowledgeGraphStrategy,
        parameters: Dict[str, Any]
    ) -> KnowledgeGraphResult:
        """Detect communities and hierarchical structures in knowledge graph"""

        start_time = time.time()

        # GraphRAG excels at community detection
        result = await self._execute_graphrag(content, parameters, focus='communities')

        result.execution_time = time.time() - start_time
        return result

    async def track_temporal_evolution(
        self,
        content: str,
        strategy: KnowledgeGraphStrategy,
        parameters: Dict[str, Any]
    ) -> KnowledgeGraphResult:
        """Track how knowledge evolves over time"""

        start_time = time.time()

        # Graphiti specializes in temporal graphs
        result = await self._execute_graphiti(content, parameters)

        result.execution_time = time.time() - start_time
        return result

    async def semantic_search(
        self,
        query: str,
        parameters: Dict[str, Any]
    ) -> KnowledgeGraphResult:
        """Perform semantic search over knowledge graph"""

        start_time = time.time()

        # Use Cognee for cognitive semantic search
        result = await self._execute_cognee(query, parameters, operation='search')

        result.execution_time = time.time() - start_time
        return result

    async def reason_over_graph(
        self,
        query: str,
        parameters: Dict[str, Any]
    ) -> KnowledgeGraphResult:
        """Perform reasoning over knowledge graph"""

        start_time = time.time()

        # Use Cognee for cognitive reasoning
        result = await self._execute_cognee(query, parameters, operation='reasoning')

        result.execution_time = time.time() - start_time
        return result

    # ==================== Plugin Execution Methods ====================

    async def _comprehensive_extraction(
        self,
        content: str,
        parameters: Dict[str, Any]
    ) -> KnowledgeGraphResult:
        """Execute all knowledge graph plugins in parallel and merge results"""

        tasks = [
            self._execute_graphrag(content, parameters),
            self._execute_graphiti(content, parameters),
            self._execute_cognee(content, parameters)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge all successful results
        merged_result = KnowledgeGraphResult()
        for result in results:
            if isinstance(result, KnowledgeGraphResult):
                merged_result = merged_result.merge(result)
            elif isinstance(result, Exception):
                logger.warning(f"Plugin execution failed: {result}")

        # Calculate confidence score based on how many plugins succeeded
        successful_count = sum(1 for r in results if isinstance(r, KnowledgeGraphResult))
        merged_result.confidence_score = successful_count / len(tasks) if tasks else 0.0

        return merged_result

    async def _fast_extraction(
        self,
        content: str,
        parameters: Dict[str, Any]
    ) -> KnowledgeGraphResult:
        """Execute fastest plugin (GraphRAG) for quick results"""
        return await self._execute_graphrag(content, parameters)

    async def _cognitive_extraction(
        self,
        content: str,
        parameters: Dict[str, Any]
    ) -> KnowledgeGraphResult:
        """Execute Cognee for cognitive-focused extraction"""
        return await self._execute_cognee(content, parameters)

    async def _execute_graphrag(
        self,
        content: str,
        parameters: Dict[str, Any],
        focus: str = 'entities'
    ) -> KnowledgeGraphResult:
        """Execute GraphRAG plugin"""

        try:
            # Load GraphRAG adapter
            loaded_plugin = self.loader.load_by_capability('graph_rag')
            adapter = AdapterFactory.create('graphrag', 'graph_rag')

            # Create plugin input
            plugin_input = create_plugin_input(
                capability_id='graph_rag',
                input_type='text',
                data=content,
                parameters={**parameters, 'focus': focus}
            )

            # Execute plugin
            output = await adapter.execute_async(plugin_input)

            # Update usage statistics
            self.stats['plugin_usage']['graphrag'] = self.stats['plugin_usage'].get('graphrag', 0) + 1

            # Parse output to KnowledgeGraphResult
            result = self._parse_graphrag_output(output)
            result.source_plugins.append('graphrag')

            return result

        except Exception as e:
            logger.error(f"GraphRAG execution failed: {e}")
            raise

    async def _execute_graphiti(
        self,
        content: str,
        parameters: Dict[str, Any]
    ) -> KnowledgeGraphResult:
        """Execute Graphiti plugin for temporal graph"""

        try:
            # Load Graphiti adapter
            loaded_plugin = self.loader.load_by_capability('temporal_graph')
            adapter = AdapterFactory.create('graphiti', 'temporal_graph')

            # Create plugin input
            plugin_input = create_plugin_input(
                capability_id='temporal_graph',
                input_type='text',
                data=content,
                parameters=parameters
            )

            # Execute plugin
            output = await adapter.execute_async(plugin_input)

            # Update usage statistics
            self.stats['plugin_usage']['graphiti'] = self.stats['plugin_usage'].get('graphiti', 0) + 1

            # Parse output
            result = self._parse_graphiti_output(output)
            result.source_plugins.append('graphiti')

            return result

        except Exception as e:
            logger.error(f"Graphiti execution failed: {e}")
            raise

    async def _execute_cognee(
        self,
        content: str,
        parameters: Dict[str, Any],
        operation: str = 'extraction'
    ) -> KnowledgeGraphResult:
        """Execute Cognee plugin for cognitive graph"""

        try:
            # Load Cognee adapter
            loaded_plugin = self.loader.load_by_capability('cognitive_graph')
            adapter = AdapterFactory.create('cognee', 'cognitive_graph')

            # Create plugin input
            plugin_input = create_plugin_input(
                capability_id='cognitive_graph',
                input_type='text',
                data=content,
                parameters={**parameters, 'operation': operation}
            )

            # Execute plugin
            output = await adapter.execute_async(plugin_input)

            # Update usage statistics
            self.stats['plugin_usage']['cognee'] = self.stats['plugin_usage'].get('cognee', 0) + 1

            # Parse output
            result = self._parse_cognee_output(output)
            result.source_plugins.append('cognee')

            return result

        except Exception as e:
            logger.error(f"Cognee execution failed: {e}")
            raise

    # ==================== Output Parsing Methods ====================

    def _parse_graphrag_output(self, output: PluginOutput) -> KnowledgeGraphResult:
        """Parse GraphRAG output into standardized KnowledgeGraphResult"""

        result = KnowledgeGraphResult()

        if output.status == PluginExecutionStatus.SUCCESS and output.data:
            result.entities = output.data.get('entities', [])
            result.relationships = output.data.get('relationships', [])
            result.communities = output.data.get('communities', [])

            result.entity_count = len(result.entities)
            result.relationship_count = len(result.relationships)
            result.community_count = len(result.communities)
            result.confidence_score = 0.9  # GraphRAG is highly reliable

        return result

    def _parse_graphiti_output(self, output: PluginOutput) -> KnowledgeGraphResult:
        """Parse Graphiti output into standardized KnowledgeGraphResult"""

        result = KnowledgeGraphResult()

        if output.status == PluginExecutionStatus.SUCCESS and output.data:
            result.entities = output.data.get('nodes', [])
            result.relationships = output.data.get('edges', [])
            result.temporal_events = output.data.get('temporal_events', [])

            result.entity_count = len(result.entities)
            result.relationship_count = len(result.relationships)
            result.confidence_score = 0.85  # Temporal tracking adds uncertainty

        return result

    def _parse_cognee_output(self, output: PluginOutput) -> KnowledgeGraphResult:
        """Parse Cognee output into standardized KnowledgeGraphResult"""

        result = KnowledgeGraphResult()

        if output.status == PluginExecutionStatus.SUCCESS and output.data:
            result.entities = output.data.get('concepts', [])
            result.relationships = output.data.get('connections', [])
            result.cognitive_insights = output.data.get('insights', [])

            result.entity_count = len(result.entities)
            result.relationship_count = len(result.relationships)
            result.confidence_score = 0.8  # Cognitive reasoning has more interpretation

        return result

    # ==================== Agent Status Methods ====================

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status with execution statistics"""
        base_status = super().get_status()
        base_status.update({
            'statistics': self.stats,
            'loaded_plugins': list(self.loader._loaded_plugins.keys()),
            'available_capabilities': list(self.kg_capabilities.keys())
        })
        return base_status

    def get_capabilities_info(self) -> Dict[str, Any]:
        """Get detailed information about available knowledge graph capabilities"""
        return {
            'knowledge_graph_plugins': {
                'graphrag': {
                    'capability': 'graph_rag',
                    'strengths': ['entity_extraction', 'relationship_mapping', 'community_detection'],
                    'description': 'Comprehensive knowledge graph with hierarchical communities'
                },
                'graphiti': {
                    'capability': 'temporal_graph',
                    'strengths': ['temporal_tracking', 'evolution_analysis'],
                    'description': 'Temporal knowledge graph tracking changes over time'
                },
                'cognee': {
                    'capability': 'cognitive_graph',
                    'strengths': ['semantic_reasoning', 'cognitive_insights'],
                    'description': 'Cognitive knowledge graph with reasoning capabilities'
                }
            },
            'query_types': [qt.value for qt in KnowledgeQueryType],
            'strategies': [s.value for s in KnowledgeGraphStrategy],
            'usage_statistics': self.stats
        }
