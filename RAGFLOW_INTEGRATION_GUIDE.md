# RAGFlow Integration Guide for FieldMind

## Overview

**RAGFlow** is an open-source RAG (Retrieval-Augmented Generation) engine based on deep document understanding. It provides enterprise-grade document parsing, chunking, embedding, and retrieval capabilities.

## Repository Information

- **GitHub**: https://github.com/infiniflow/ragflow
- **Version**: v0.26.4
- **License**: Apache 2.0
- **Local Clone**: `/Users/alwan/FieldMind-Rebuild/external-tools/ragflow/`

## Key Features

### 🍭 Deep Document Understanding
- Advanced knowledge extraction from complex document formats
- Finds "needle in a haystack" with unlimited tokens
- Supports Word, Slides, Excel, TXT, images, scanned copies, web pages

### 🍱 Template-based Chunking
- Intelligent and explainable chunking strategies
- Multiple template options for different document types

### 🌱 Grounded Citations
- Visualization of text chunking
- Traceable citations with reduced hallucinations
- Quick view of key references

### 🛀 Automated RAG Workflow
- Streamlined orchestration for personal and enterprise use
- Configurable LLMs and embedding models
- Multiple recall with fused re-ranking
- Intuitive APIs for integration

### Latest Updates (2026)
- Support for multiple chat channels (Feishu, Discord, Telegram, Line)
- DeepSeek v4 support
- Memory support for AI agents
- Gemini 3 Pro support
- Data sync from Confluence, S3, Notion, Discord, Google Drive
- MinerU & Docling document parsing
- Orchestrable ingestion pipeline
- Agentic workflow and MCP support

## Architecture Components

RAGFlow consists of:
1. **DeepDoc** - Advanced document parsing engine
2. **RAG** - Retrieval engine with vector/full-text search
3. **Agent** - Agentic workflow capabilities
4. **Memory** - Agent memory system
5. **Web** - Frontend interface
6. **SDK** - Python and JavaScript SDKs
7. **API** - RESTful APIs

## Python SDK

**Package**: `ragflow-sdk`
**Version**: 0.26.4
**Location**: `/Users/alwan/FieldMind-Rebuild/external-tools/ragflow/sdk/python/`
**Python Requirement**: >= 3.13

### Dependencies
- requests >= 2.30.0
- beartype >= 0.20.0

## Integration Strategy for FieldMind

### Option 1: Use RAGFlow as External Service (Recommended)

**Approach**: Deploy RAGFlow as a separate Docker service and integrate via API

**Advantages**:
- Full-featured RAG system out of the box
- Battle-tested enterprise solution
- Regular updates and community support
- No need to reimplement complex RAG logic

**Requirements**:
- Docker >= 24.0.0
- Docker Compose >= v2.26.1
- CPU >= 4 cores
- RAM >= 16 GB
- Disk >= 50 GB

**Setup**:
```bash
cd /Users/alwan/FieldMind-Rebuild/external-tools/ragflow/docker
docker compose -f docker-compose.yml up -d
```

**Integration Points**:
1. **Document Upload**: Send documents to RAGFlow for processing
2. **Knowledge Base**: Create RAGFlow datasets per FieldMind project
3. **Semantic Search**: Query RAGFlow for memory retrieval
4. **Chat**: Use RAGFlow chat API for enhanced conversations

### Option 2: Use RAGFlow Python SDK

**Approach**: Install ragflow-sdk and integrate directly

**Installation**:
```bash
pip install ragflow-sdk
```

**Basic Usage**:
```python
import ragflow_sdk

# Connect to RAGFlow instance
client = ragflow_sdk.RAGFlow(
    api_key="your_api_key",
    base_url="http://localhost:9380"
)

# Create a dataset (knowledge base)
dataset = client.create_dataset(
    name="Project_123_Knowledge",
    description="Knowledge base for project 123"
)

# Upload document
with open("document.pdf", "rb") as f:
    dataset.upload_document(f, name="document.pdf")

# Query
results = dataset.query(
    query="What is the main topic?",
    top_k=5
)
```

### Option 3: Hybrid Approach (Recommended for FieldMind)

**Combine**: RAGFlow for heavy RAG tasks + Custom MemoryService for lightweight operations

**Architecture**:
```
FieldMind Backend
├── Local Memory Service (for quick access)
│   ├── Three-tier memory (short/mid/long)
│   └── SQLite/PostgreSQL storage
│
└── RAGFlow Service (for deep RAG)
    ├── Document parsing & chunking
    ├── Vector embeddings
    ├── Semantic search
    └── Context retrieval
```

**When to Use RAGFlow**:
- Large documents (>10 pages)
- Complex document formats (scanned PDFs, presentations)
- Semantic search across document corpus
- Need for grounded citations
- Multi-modal content (images in documents)

**When to Use Local Memory**:
- Chat message storage
- Quick keyword search
- Recent memory access (short-term)
- Session context management

## Implementation Plan

### Phase 1: RAGFlow Service Setup
1. ✅ Clone RAGFlow repository
2. Configure Docker deployment
3. Set up LLM API keys
4. Test document upload and retrieval
5. Expose RAGFlow API endpoint

### Phase 2: SDK Integration
1. Install ragflow-sdk in fieldmind-backend
2. Create RAGFlow client service wrapper
3. Implement dataset management (one per project)
4. Add document sync from FieldMind to RAGFlow

### Phase 3: Backend Integration
1. Extend MemoryService with RAGFlow client
2. Add RAGFlow document processing endpoint
3. Implement hybrid retrieval (local + RAGFlow)
4. Add configuration for RAGFlow URL and API key

### Phase 4: API Endpoints
```python
# New endpoints in app/api/v1/project_documents.py

@router.post("/{project_id}/documents/{doc_id}/parse-with-ragflow")
async def parse_document_with_ragflow(
    project_id: int,
    doc_id: int,
    db: Session = Depends(get_db)
):
    """Send document to RAGFlow for deep parsing"""
    pass

@router.post("/{project_id}/search/semantic")
async def semantic_search(
    project_id: int,
    query: str,
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    """Search using RAGFlow semantic search"""
    pass
```

### Phase 5: Frontend Integration
1. Add "Deep Analysis" button for documents
2. Show RAGFlow parsing results
3. Display chunking visualization
4. Show grounded citations in chat

## Configuration

Add to `fieldmind-backend/.env`:
```bash
# RAGFlow Configuration
RAGFLOW_ENABLED=true
RAGFLOW_BASE_URL=http://localhost:9380
RAGFLOW_API_KEY=your_api_key_here
RAGFLOW_DEFAULT_PARSER=deepdoc
RAGFLOW_CHUNK_SIZE=512
```

## Code Structure

```
fieldmind-backend/
├── app/
│   ├── services/
│   │   ├── memory_service.py (existing)
│   │   ├── document_converter.py (existing - MarkItDown)
│   │   └── ragflow_service.py (new)
│   │       ├── RAGFlowClient
│   │       ├── DatasetManager
│   │       ├── DocumentParser
│   │       └── SemanticSearcher
│   ├── api/v1/
│   │   ├── project_documents.py (extend)
│   │   └── ragflow_integration.py (new)
```

## Sample RAGFlowService Implementation

```python
# app/services/ragflow_service.py
import os
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RAGFlowService:
    """RAGFlow integration service for FieldMind"""
    
    def __init__(self):
        self.enabled = os.getenv("RAGFLOW_ENABLED", "false").lower() == "true"
        self.base_url = os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380")
        self.api_key = os.getenv("RAGFLOW_API_KEY")
        
        if self.enabled and self.api_key:
            try:
                import ragflow_sdk
                self.client = ragflow_sdk.RAGFlow(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                logger.warning("ragflow-sdk not installed")
                self.enabled = False
    
    def is_available(self) -> bool:
        return self.enabled and hasattr(self, 'client')
    
    def create_project_dataset(self, project_id: int, project_name: str) -> Optional[str]:
        """Create a RAGFlow dataset for a FieldMind project"""
        if not self.is_available():
            return None
        
        try:
            dataset = self.client.create_dataset(
                name=f"FieldMind_Project_{project_id}",
                description=f"Knowledge base for {project_name}"
            )
            return dataset.id
        except Exception as e:
            logger.error(f"Failed to create RAGFlow dataset: {e}")
            return None
    
    def upload_document(
        self, 
        dataset_id: str, 
        file_path: str,
        filename: str
    ) -> Optional[Dict[str, Any]]:
        """Upload document to RAGFlow for processing"""
        if not self.is_available():
            return None
        
        try:
            dataset = self.client.get_dataset(dataset_id)
            with open(file_path, "rb") as f:
                result = dataset.upload_document(f, name=filename)
            return result
        except Exception as e:
            logger.error(f"Failed to upload to RAGFlow: {e}")
            return None
    
    def semantic_search(
        self,
        dataset_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform semantic search in RAGFlow dataset"""
        if not self.is_available():
            return []
        
        try:
            dataset = self.client.get_dataset(dataset_id)
            results = dataset.query(query=query, top_k=top_k)
            return results
        except Exception as e:
            logger.error(f"RAGFlow search failed: {e}")
            return []

# Global instance
ragflow_service = RAGFlowService()
```

## Benefits for FieldMind

1. **Superior Document Understanding**: Better than basic PDF parsing
2. **Enterprise-Grade RAG**: Battle-tested in production
3. **Grounded Responses**: Citations reduce AI hallucinations
4. **Scalability**: Handles large document collections
5. **Multi-Modal**: Supports images within documents
6. **Active Development**: Regular updates and new features
7. **Open Source**: No vendor lock-in

## Considerations

1. **Resource Requirements**: RAGFlow needs substantial resources (16GB RAM)
2. **Complexity**: Additional service to deploy and maintain
3. **Python Version**: Requires Python 3.13 (FieldMind might need upgrade)
4. **Deployment**: Docker-based deployment adds infrastructure complexity
5. **Learning Curve**: Team needs to learn RAGFlow concepts

## Alternatives to Full RAGFlow Integration

If full RAGFlow deployment is too heavy:

1. **Use LlamaIndex**: Lightweight Python RAG framework
2. **Use LangChain**: Popular LLM orchestration framework
3. **Custom RAG**: Build with ChromaDB + Sentence Transformers
4. **Hybrid**: RAGFlow cloud service (if available)

## Next Steps

1. Deploy RAGFlow locally for testing
2. Experiment with document parsing quality
3. Compare with MarkItDown results
4. Decide on integration approach
5. Implement RAGFlowService wrapper
6. Add configuration and API endpoints
7. Test end-to-end integration

---

**Status**: ✅ RAGFlow cloned successfully, ready for evaluation
**Priority**: 🔥 High - Core functionality for long memory and document understanding
**Estimated Integration Time**: 1-2 weeks for full integration
**Dependencies**: Docker, Python 3.13, 16GB RAM
