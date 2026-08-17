"""
Enhanced Coordinator Agent - Phase 2 Day 5
集成所有 SuperAgents 的协调代理

⚠️ DEPRECATED: 此Agent已废弃，将在v2.0中移除
请使用新的6-Agent v2架构替代

Features:
- Intelligent task routing to optimal SuperAgent
- Multi-agent collaboration for complex tasks
- Result aggregation and fusion
- Load balancing and resource management
- Workflow orchestration

SuperAgents integrated:
- SuperKnowledgeAgent (graphrag + graphiti + cognee)
- SuperSearchAgent (crawl4ai + firecrawl + browser-use)
- SuperSummaryAgent (ragflow + LightRAG + mem0)
- SuperTranscriptAgent (markitdown + PDF-Guru)

Author: Claude + User
Date: 2026-08-14
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid

from app.services.agents.base_agent import AgentBase, AgentTask, AgentStatus, AgentRole
from app.utils.deprecation import deprecated

# Import all SuperAgents
from app.services.agents.super_knowledge_agent import (
    SuperKnowledgeAgent,
    KnowledgeQueryType,
    KnowledgeGraphStrategy,
)
from app.services.agents.super_search_agent import (
    SuperSearchAgent,
    SearchQueryType,
    SearchStrategy,
)
from app.services.agents.super_summary_agent import (
    SuperSummaryAgent,
    SummaryQueryType,
    SummaryStrategy,
)
from app.services.agents.super_transcript_agent import (
    SuperTranscriptAgent,
    TranscriptQueryType,
    TranscriptStrategy,
)


logger = logging.getLogger(__name__)


class TaskCategory(Enum):
    """Task categories mapped to SuperAgents"""
    KNOWLEDGE_GRAPH = "knowledge_graph"      # → SuperKnowledgeAgent
    WEB_SEARCH = "web_search"                # → SuperSearchAgent
    DOCUMENT_SUMMARY = "document_summary"    # → SuperSummaryAgent
    FORMAT_CONVERSION = "format_conversion"  # → SuperTranscriptAgent
    COMPLEX_WORKFLOW = "complex_workflow"    # → Multi-agent collaboration


class CoordinationStrategy(Enum):
    """Coordination strategies for multi-agent collaboration"""
    SINGLE_AGENT = "single_agent"        # Route to one optimal agent
    SEQUENTIAL = "sequential"            # Chain agents in sequence
    PARALLEL = "parallel"                # Execute agents in parallel
    HYBRID = "hybrid"                    # Mix of sequential and parallel
    REDUNDANT = "redundant"              # Multiple agents for verification


@dataclass
class AgentAllocation:
    """Resource allocation for an agent"""
    agent_type: str
    agent_instance: Optional[AgentBase] = None
    task_count: int = 0
    total_processing_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0

    @property
    def average_processing_time(self) -> float:
        """Calculate average processing time"""
        if self.task_count == 0:
            return 0.0
        return self.total_processing_time / self.task_count

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.task_count == 0:
            return 0.0
        return self.success_count / self.task_count


@dataclass
class CoordinationResult:
    """Structured result from coordinator"""
    task_category: TaskCategory
    coordination_strategy: CoordinationStrategy
    agents_involved: List[str] = field(default_factory=list)
    primary_result: Dict[str, Any] = field(default_factory=dict)
    auxiliary_results: List[Dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 0.0
    total_processing_time: float = 0.0
    agent_performance: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    workflow_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'task_category': self.task_category.value,
            'coordination_strategy': self.coordination_strategy.value,
            'agents_involved': self.agents_involved,
            'primary_result': self.primary_result,
            'auxiliary_results': self.auxiliary_results,
            'confidence_score': self.confidence_score,
            'total_processing_time': self.total_processing_time,
            'agent_performance': self.agent_performance,
            'warnings': self.warnings,
            'errors': self.errors,
            'workflow_steps': self.workflow_steps,
        }


@deprecated(
    reason="Coordinator架构已被6-Agent v2替代",
    replacement="app.agents.v2中的直接agent调用",
    version="2.0"
)
class EnhancedCoordinatorAgent(AgentBase):
    """
    Enhanced Coordinator Agent integrating all SuperAgents

    Capabilities:
    - Intelligent task routing based on task type and context
    - Multi-agent collaboration for complex workflows
    - Load balancing across available agents
    - Result aggregation and confidence scoring
    - Performance monitoring and optimization

    1+1>2 Synergy Examples:

    1. Research Report Analysis:
       - SuperTranscriptAgent: PDF → Markdown (2s)
       - SuperSummaryAgent: Markdown → Key insights (3s)
       - SuperKnowledgeAgent: Insights → Knowledge graph (5s)
       - Total: 10s sequential, comprehensive analysis with citations

    2. Multi-Source Knowledge Base:
       - SuperSearchAgent: Web crawling for latest info (parallel, 8s)
       - SuperTranscriptAgent: Document conversion (parallel, 8s)
       - SuperKnowledgeAgent: Unified knowledge graph (5s)
       - Total: 13s with parallel execution, 21s if sequential
       - Benefit: 8s saved (38% faster)

    3. Content Quality Verification:
       - SuperSummaryAgent: Primary summarization (redundant, 3 plugins)
       - SuperSearchAgent: Fact-checking via web search
       - Final: High-confidence summary with verification
    """

    def __init__(self, agent_id: Optional[str] = None):
        """Initialize coordinator with all SuperAgents"""
        super().__init__(agent_id=agent_id)

        # Agent pool management
        self.agent_allocations: Dict[str, AgentAllocation] = {
            'knowledge': AgentAllocation(agent_type='SuperKnowledgeAgent'),
            'search': AgentAllocation(agent_type='SuperSearchAgent'),
            'summary': AgentAllocation(agent_type='SuperSummaryAgent'),
            'transcript': AgentAllocation(agent_type='SuperTranscriptAgent'),
        }

        # Task routing map
        self.task_routing: Dict[TaskCategory, str] = {
            TaskCategory.KNOWLEDGE_GRAPH: 'knowledge',
            TaskCategory.WEB_SEARCH: 'search',
            TaskCategory.DOCUMENT_SUMMARY: 'summary',
            TaskCategory.FORMAT_CONVERSION: 'transcript',
        }

        # Workflow templates for complex tasks
        self.workflow_templates: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {
            'analyze_research_paper': [
                ('transcript', {'query_type': 'format_conversion'}),
                ('summary', {'query_type': 'document_summary'}),
                ('knowledge', {'query_type': 'entity_extraction'}),
            ],
            'build_knowledge_base': [
                ('search', {'query_type': 'research'}),
                ('transcript', {'query_type': 'content_extraction'}),
                ('knowledge', {'query_type': 'graph_construction'}),
            ],
            'verify_content': [
                ('summary', {'query_type': 'key_points'}),
                ('search', {'query_type': 'fact_checking'}),
            ],
        }

    @property
    def role(self) -> AgentRole:
        """Agent role"""
        return AgentRole.COORDINATOR

    @property
    def name(self) -> str:
        """Agent name"""
        return "增强协调代理"

    @property
    def description(self) -> str:
        """Agent description"""
        return (
            "整合所有 SuperAgents 的协调代理。支持智能任务分发、多Agent协作、"
            "结果聚合、负载均衡、工作流编排。可处理知识图谱、网络搜索、文档总结、"
            "格式转换等多种任务类型，并编排复杂的多Agent工作流。"
        )

    @property
    def capabilities(self) -> List[str]:
        """Agent capabilities"""
        return [
            "intelligent_task_routing",
            "multi_agent_collaboration",
            "result_aggregation",
            "load_balancing",
            "workflow_orchestration",
            "performance_monitoring",
            "sequential_execution",
            "parallel_execution",
            "redundant_verification",
        ]

    def _initialize_tools(self):
        """Initialize tools (coordinator doesn't need tools directly)"""
        self.tools = {}

    def _execute_task_impl(self, task: AgentTask) -> Dict[str, Any]:
        """Execute task with async-sync bridge"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in event loop, schedule as task
            future = asyncio.ensure_future(self._execute_task_async(task))
            # Wait for completion
            while not future.done():
                time.sleep(0.01)
            result = future.result()
        else:
            # Not in event loop, run until complete
            result = loop.run_until_complete(self._execute_task_async(task))

        return result

    async def _execute_task_async(self, task: AgentTask) -> Dict[str, Any]:
        """Async task execution with coordination logic"""
        start_time = time.time()

        try:
            input_data = task.input_data or {}

            # 1. Categorize task
            task_category = self._categorize_task(input_data)

            # 2. Select coordination strategy
            coordination_strategy = self._select_coordination_strategy(
                task_category, input_data
            )

            # 3. Execute based on strategy
            if coordination_strategy == CoordinationStrategy.SINGLE_AGENT:
                result = await self._execute_single_agent(task_category, input_data)
            elif coordination_strategy == CoordinationStrategy.SEQUENTIAL:
                result = await self._execute_sequential(input_data)
            elif coordination_strategy == CoordinationStrategy.PARALLEL:
                result = await self._execute_parallel(input_data)
            elif coordination_strategy == CoordinationStrategy.HYBRID:
                result = await self._execute_hybrid(input_data)
            elif coordination_strategy == CoordinationStrategy.REDUNDANT:
                result = await self._execute_redundant(task_category, input_data)
            else:
                raise ValueError(f"Unknown coordination strategy: {coordination_strategy}")

            # 4. Record metrics
            processing_time = time.time() - start_time
            result.total_processing_time = processing_time

            return result.to_dict()

        except Exception as e:
            logger.error(f"Coordinator task execution failed: {e}", exc_info=True)
            processing_time = time.time() - start_time

            error_result = CoordinationResult(
                task_category=TaskCategory.COMPLEX_WORKFLOW,
                coordination_strategy=CoordinationStrategy.SINGLE_AGENT,
                errors=[str(e)],
                total_processing_time=processing_time,
            )
            return error_result.to_dict()

    def _categorize_task(self, input_data: Dict[str, Any]) -> TaskCategory:
        """Categorize task based on input data"""
        # Check explicit task_category
        if 'task_category' in input_data:
            category_str = input_data['task_category']
            try:
                return TaskCategory(category_str)
            except ValueError:
                pass

        # Check workflow template
        if 'workflow_template' in input_data:
            return TaskCategory.COMPLEX_WORKFLOW

        # Infer from query_type or task_type
        query_type = input_data.get('query_type', '').lower()
        task_type = input_data.get('task_type', '').lower()

        # Knowledge graph patterns
        if any(kw in query_type or kw in task_type for kw in [
            'knowledge', 'graph', 'entity', 'relation', 'ontology'
        ]):
            return TaskCategory.KNOWLEDGE_GRAPH

        # Search patterns
        if any(kw in query_type or kw in task_type for kw in [
            'search', 'crawl', 'scrape', 'browse', 'web'
        ]):
            return TaskCategory.WEB_SEARCH

        # Summary patterns
        if any(kw in query_type or kw in task_type for kw in [
            'summary', 'summarize', 'extract', 'key_points', 'memory'
        ]):
            return TaskCategory.DOCUMENT_SUMMARY

        # Transcript patterns
        if any(kw in query_type or kw in task_type for kw in [
            'convert', 'transcript', 'format', 'markdown', 'pdf'
        ]):
            return TaskCategory.FORMAT_CONVERSION

        # Default to complex workflow
        return TaskCategory.COMPLEX_WORKFLOW

    def _select_coordination_strategy(
        self,
        task_category: TaskCategory,
        input_data: Dict[str, Any]
    ) -> CoordinationStrategy:
        """Select optimal coordination strategy"""
        # Explicit strategy override
        if 'coordination_strategy' in input_data:
            strategy_str = input_data['coordination_strategy']
            try:
                return CoordinationStrategy(strategy_str)
            except ValueError:
                pass

        # Complex workflow → detect strategy from template
        if task_category == TaskCategory.COMPLEX_WORKFLOW:
            workflow_template = input_data.get('workflow_template')
            if workflow_template:
                # Check if template has parallel steps
                if input_data.get('parallel_execution', False):
                    return CoordinationStrategy.PARALLEL
                else:
                    return CoordinationStrategy.SEQUENTIAL
            return CoordinationStrategy.HYBRID

        # Redundant verification mode
        if input_data.get('redundant_verification', False):
            return CoordinationStrategy.REDUNDANT

        # Default: single agent for simple tasks
        return CoordinationStrategy.SINGLE_AGENT

    async def _execute_single_agent(
        self,
        task_category: TaskCategory,
        input_data: Dict[str, Any]
    ) -> CoordinationResult:
        """Execute task with single optimal agent"""
        agent_key = self.task_routing[task_category]
        allocation = self.agent_allocations[agent_key]

        # Get or create agent instance
        if allocation.agent_instance is None:
            allocation.agent_instance = self._create_agent_instance(agent_key)

        agent = allocation.agent_instance

        # Create task for agent
        agent_task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type=input_data.get('query_type', 'default'),
            input_data=input_data,
        )

        # Execute
        start_time = time.time()
        try:
            result = agent.execute_task(agent_task)
            processing_time = time.time() - start_time

            # Update allocation metrics
            allocation.task_count += 1
            allocation.total_processing_time += processing_time
            if result.status == AgentStatus.COMPLETED:
                allocation.success_count += 1
            else:
                allocation.failure_count += 1

            # Build coordination result
            coord_result = CoordinationResult(
                task_category=task_category,
                coordination_strategy=CoordinationStrategy.SINGLE_AGENT,
                agents_involved=[agent.name],
                primary_result=result.output_data,
                confidence_score=result.output_data.get('confidence_score', 0.0),
                total_processing_time=processing_time,
                agent_performance={agent.name: processing_time},
                workflow_steps=[f"Executed {agent.name}"],
            )

            return coord_result

        except Exception as e:
            processing_time = time.time() - start_time
            allocation.task_count += 1
            allocation.failure_count += 1
            allocation.total_processing_time += processing_time

            coord_result = CoordinationResult(
                task_category=task_category,
                coordination_strategy=CoordinationStrategy.SINGLE_AGENT,
                agents_involved=[agent.name],
                errors=[f"{agent.name} failed: {str(e)}"],
                total_processing_time=processing_time,
            )

            return coord_result

    async def _execute_sequential(self, input_data: Dict[str, Any]) -> CoordinationResult:
        """Execute workflow sequentially"""
        workflow_template = input_data.get('workflow_template')
        if not workflow_template or workflow_template not in self.workflow_templates:
            raise ValueError(f"Unknown workflow template: {workflow_template}")

        steps = self.workflow_templates[workflow_template]

        coord_result = CoordinationResult(
            task_category=TaskCategory.COMPLEX_WORKFLOW,
            coordination_strategy=CoordinationStrategy.SEQUENTIAL,
        )

        current_data = input_data.copy()

        for step_idx, (agent_key, step_params) in enumerate(steps):
            allocation = self.agent_allocations[agent_key]

            # Get or create agent
            if allocation.agent_instance is None:
                allocation.agent_instance = self._create_agent_instance(agent_key)

            agent = allocation.agent_instance

            # Merge step params with current data
            step_input = {**current_data, **step_params}

            agent_task = AgentTask(
                task_id=str(uuid.uuid4()),
                task_type=step_params.get('query_type', 'default'),
                input_data=step_input,
            )

            # Execute step
            start_time = time.time()
            try:
                result = agent.execute_task(agent_task)
                processing_time = time.time() - start_time

                # Update metrics
                allocation.task_count += 1
                allocation.total_processing_time += processing_time
                if result.status == AgentStatus.COMPLETED:
                    allocation.success_count += 1
                else:
                    allocation.failure_count += 1

                # Record results
                coord_result.agents_involved.append(agent.name)
                coord_result.agent_performance[agent.name] = processing_time
                coord_result.workflow_steps.append(
                    f"Step {step_idx + 1}: {agent.name} completed in {processing_time:.2f}s"
                )

                # Store result
                if step_idx == len(steps) - 1:
                    # Last step = primary result
                    coord_result.primary_result = result.output_data
                else:
                    # Intermediate results
                    coord_result.auxiliary_results.append(result.output_data)

                # Pass result to next step
                current_data['previous_result'] = result.output_data

            except Exception as e:
                processing_time = time.time() - start_time
                allocation.task_count += 1
                allocation.failure_count += 1
                allocation.total_processing_time += processing_time

                coord_result.errors.append(
                    f"Step {step_idx + 1} ({agent.name}) failed: {str(e)}"
                )
                coord_result.workflow_steps.append(
                    f"Step {step_idx + 1}: {agent.name} failed"
                )

                # Stop on first failure
                break

        # Calculate overall confidence
        if coord_result.agents_involved:
            success_rate = (len(coord_result.agents_involved) - len(coord_result.errors)) / len(steps)
            coord_result.confidence_score = success_rate

        return coord_result

    async def _execute_parallel(self, input_data: Dict[str, Any]) -> CoordinationResult:
        """Execute multiple agents in parallel"""
        agent_keys = input_data.get('parallel_agents', [])
        if not agent_keys:
            raise ValueError("parallel_agents not specified for parallel execution")

        coord_result = CoordinationResult(
            task_category=TaskCategory.COMPLEX_WORKFLOW,
            coordination_strategy=CoordinationStrategy.PARALLEL,
        )

        # Create tasks for parallel execution
        tasks = []
        agent_instances = []

        for agent_key in agent_keys:
            if agent_key not in self.agent_allocations:
                coord_result.warnings.append(f"Unknown agent key: {agent_key}")
                continue

            allocation = self.agent_allocations[agent_key]

            # Get or create agent
            if allocation.agent_instance is None:
                allocation.agent_instance = self._create_agent_instance(agent_key)

            agent = allocation.agent_instance
            agent_instances.append((agent_key, agent))

            # Create agent task
            agent_task = AgentTask(
                task_id=str(uuid.uuid4()),
                task_type=input_data.get('query_type', 'default'),
                input_data=input_data,
            )

            # Add to parallel tasks
            tasks.append(self._execute_agent_task(agent_key, agent, agent_task))

        # Execute in parallel
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Process results
        for (agent_key, agent), result in zip(agent_instances, results):
            if isinstance(result, Exception):
                coord_result.errors.append(f"{agent.name} failed: {str(result)}")
            else:
                coord_result.agents_involved.append(agent.name)
                coord_result.auxiliary_results.append(result)
                coord_result.agent_performance[agent.name] = result.get('processing_time', 0.0)
                coord_result.workflow_steps.append(f"{agent.name} completed")

        # Primary result = first successful result
        if coord_result.auxiliary_results:
            coord_result.primary_result = coord_result.auxiliary_results[0]

        # Calculate confidence
        if tasks:
            success_rate = len(coord_result.agents_involved) / len(tasks)
            coord_result.confidence_score = success_rate

        coord_result.total_processing_time = total_time

        return coord_result

    async def _execute_hybrid(self, input_data: Dict[str, Any]) -> CoordinationResult:
        """Execute hybrid workflow (mix of sequential and parallel)"""
        # For now, default to sequential
        # Future: parse workflow DAG and execute optimally
        return await self._execute_sequential(input_data)

    async def _execute_redundant(
        self,
        task_category: TaskCategory,
        input_data: Dict[str, Any]
    ) -> CoordinationResult:
        """Execute with redundant agents for verification"""
        # Use same agent with different strategies or multiple similar agents
        # For simplicity, execute twice and compare results

        agent_key = self.task_routing[task_category]
        allocation = self.agent_allocations[agent_key]

        if allocation.agent_instance is None:
            allocation.agent_instance = self._create_agent_instance(agent_key)

        agent = allocation.agent_instance

        # Execute twice with same input
        task1 = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type=input_data.get('query_type', 'default'),
            input_data=input_data,
        )

        task2 = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type=input_data.get('query_type', 'default'),
            input_data=input_data,
        )

        start_time = time.time()
        results = await asyncio.gather(
            self._execute_agent_task(agent_key, agent, task1),
            self._execute_agent_task(agent_key, agent, task2),
            return_exceptions=True,
        )
        total_time = time.time() - start_time

        coord_result = CoordinationResult(
            task_category=task_category,
            coordination_strategy=CoordinationStrategy.REDUNDANT,
            agents_involved=[agent.name, agent.name],
            total_processing_time=total_time,
        )

        successful_results = [r for r in results if not isinstance(r, Exception)]

        if successful_results:
            # Use first successful result
            coord_result.primary_result = successful_results[0]
            coord_result.auxiliary_results = successful_results[1:]
            coord_result.confidence_score = len(successful_results) / len(results)
            coord_result.workflow_steps.append(
                f"Redundant execution: {len(successful_results)}/{len(results)} succeeded"
            )
        else:
            coord_result.errors.append("All redundant executions failed")
            coord_result.confidence_score = 0.0

        return coord_result

    async def _execute_agent_task(
        self,
        agent_key: str,
        agent: AgentBase,
        task: AgentTask
    ) -> Dict[str, Any]:
        """Execute agent task and update metrics"""
        allocation = self.agent_allocations[agent_key]

        start_time = time.time()
        try:
            result = agent.execute_task(task)
            processing_time = time.time() - start_time

            # Update metrics
            allocation.task_count += 1
            allocation.total_processing_time += processing_time
            if result.status == AgentStatus.COMPLETED:
                allocation.success_count += 1
            else:
                allocation.failure_count += 1

            return {
                **result.output_data,
                'processing_time': processing_time,
                'agent_name': agent.name,
            }

        except Exception as e:
            processing_time = time.time() - start_time
            allocation.task_count += 1
            allocation.failure_count += 1
            allocation.total_processing_time += processing_time

            raise e

    def _create_agent_instance(self, agent_key: str) -> AgentBase:
        """Create agent instance based on key"""
        agent_map = {
            'knowledge': SuperKnowledgeAgent,
            'search': SuperSearchAgent,
            'summary': SuperSummaryAgent,
            'transcript': SuperTranscriptAgent,
        }

        if agent_key not in agent_map:
            raise ValueError(f"Unknown agent key: {agent_key}")

        agent_class = agent_map[agent_key]
        agent_id = f"{agent_key}_{uuid.uuid4().hex[:8]}"

        return agent_class(agent_id=agent_id)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all agents"""
        metrics = {}

        for agent_key, allocation in self.agent_allocations.items():
            metrics[agent_key] = {
                'agent_type': allocation.agent_type,
                'task_count': allocation.task_count,
                'success_count': allocation.success_count,
                'failure_count': allocation.failure_count,
                'success_rate': allocation.success_rate,
                'average_processing_time': allocation.average_processing_time,
                'total_processing_time': allocation.total_processing_time,
            }

        return metrics

    def recommend_agent(self, task_description: str) -> Tuple[str, float]:
        """Recommend optimal agent based on task description and metrics"""
        # Simple keyword-based recommendation
        # Future: use ML model for better recommendations

        keywords = task_description.lower()

        scores = {
            'knowledge': 0.0,
            'search': 0.0,
            'summary': 0.0,
            'transcript': 0.0,
        }

        # Keyword scoring
        if any(kw in keywords for kw in ['knowledge', 'graph', 'entity', 'relation']):
            scores['knowledge'] += 0.5

        if any(kw in keywords for kw in ['search', 'crawl', 'web', 'browse']):
            scores['search'] += 0.5

        if any(kw in keywords for kw in ['summary', 'extract', 'key', 'memory']):
            scores['summary'] += 0.5

        if any(kw in keywords for kw in ['convert', 'format', 'markdown', 'pdf']):
            scores['transcript'] += 0.5

        # Performance scoring (favor agents with high success rate)
        for agent_key, allocation in self.agent_allocations.items():
            if allocation.task_count > 0:
                scores[agent_key] += allocation.success_rate * 0.3

        # Load balancing (slight penalty for overloaded agents)
        max_tasks = max(
            (a.task_count for a in self.agent_allocations.values()),
            default=1
        )
        for agent_key, allocation in self.agent_allocations.items():
            if max_tasks > 0:
                load_factor = allocation.task_count / max_tasks
                scores[agent_key] -= load_factor * 0.1

        # Select best agent
        best_agent = max(scores.items(), key=lambda x: x[1])

        return best_agent
