"""
RAGFlow Service - Integration with RAGFlow for advanced document processing
"""
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Try to import RAGFlow SDK
try:
    from ragflow import RAGFlow
    RAGFLOW_SDK_AVAILABLE = True
except ImportError:
    logger.warning("RAGFlow SDK not installed. Run: pip install ragflow-sdk")
    RAGFLOW_SDK_AVAILABLE = False
    RAGFlow = None

# RAGFlow configuration (from settings)
RAGFLOW_API_URL = settings.RAGFLOW_API_URL
RAGFLOW_API_KEY = settings.RAGFLOW_API_KEY

RAGFLOW_AVAILABLE = RAGFLOW_SDK_AVAILABLE and bool(RAGFLOW_API_KEY)


class RAGFlowService:
    """Service for interacting with RAGFlow engine"""

    def __init__(self, api_url: str = RAGFLOW_API_URL, api_key: str = RAGFLOW_API_KEY):
        """
        Initialize RAGFlow service

        Args:
            api_url: RAGFlow API endpoint
            api_key: RAGFlow API key
        """
        self.api_url = api_url
        self.api_key = api_key
        self.client = None

        if api_key:
            try:
                self.client = RAGFlow(api_url, api_key)
                logger.info("RAGFlow client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize RAGFlow client: {e}")
                self.client = None

    def is_available(self) -> bool:
        """Check if RAGFlow service is available"""
        return self.client is not None

    def create_dataset(self, name: str, description: str = "") -> Optional[Dict[str, Any]]:
        """
        Create a new dataset in RAGFlow

        Args:
            name: Dataset name
            description: Dataset description

        Returns:
            Dataset information or None if failed
        """
        if not self.is_available():
            logger.warning("RAGFlow service not available")
            return None

        try:
            dataset = self.client.create_dataset(
                name=name,
                description=description,
                embedding_model="BAAI/bge-large-zh-v1.5",  # Default Chinese embedding
                chunk_method="naive"
            )
            logger.info(f"Created RAGFlow dataset: {name}")
            return {
                "id": dataset.id,
                "name": dataset.name,
                "description": description
            }
        except Exception as e:
            logger.error(f"Failed to create RAGFlow dataset: {e}")
            return None

    def upload_document(self, dataset_id: str, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Upload a document to RAGFlow dataset

        Args:
            dataset_id: RAGFlow dataset ID
            file_path: Path to document file

        Returns:
            Document information or None if failed
        """
        if not self.is_available():
            return None

        try:
            dataset = self.client.get_dataset(dataset_id)
            document = dataset.upload_document(file_path)

            logger.info(f"Uploaded document to RAGFlow: {file_path}")
            return {
                "id": document.id,
                "name": Path(file_path).name,
                "status": "processing"
            }
        except Exception as e:
            logger.error(f"Failed to upload document to RAGFlow: {e}")
            return None

    def parse_document(self, dataset_id: str, document_ids: List[str]) -> bool:
        """
        Trigger document parsing in RAGFlow

        Args:
            dataset_id: RAGFlow dataset ID
            document_ids: List of document IDs to parse

        Returns:
            True if parsing started successfully
        """
        if not self.is_available():
            return False

        try:
            dataset = self.client.get_dataset(dataset_id)
            dataset.parse_documents(document_ids)
            logger.info(f"Started parsing {len(document_ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Failed to parse documents: {e}")
            return False

    def search(
        self,
        dataset_id: str,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search documents in RAGFlow dataset

        Args:
            dataset_id: RAGFlow dataset ID
            query: Search query
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of search results with content and metadata
        """
        if not self.is_available():
            return []

        try:
            dataset = self.client.get_dataset(dataset_id)
            results = dataset.search(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.get("content", ""),
                    "document_name": result.get("document_name", ""),
                    "similarity": result.get("similarity", 0.0),
                    "metadata": result.get("metadata", {})
                })

            logger.info(f"RAGFlow search returned {len(formatted_results)} results")
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to search in RAGFlow: {e}")
            return []

    def get_document_status(self, dataset_id: str, document_id: str) -> Optional[str]:
        """
        Get document processing status

        Args:
            dataset_id: RAGFlow dataset ID
            document_id: Document ID

        Returns:
            Status string or None if failed
        """
        if not self.is_available():
            return None

        try:
            dataset = self.client.get_dataset(dataset_id)
            document = dataset.get_document(document_id)
            return document.status
        except Exception as e:
            logger.error(f"Failed to get document status: {e}")
            return None


# Global RAGFlow service instance
ragflow_service = RAGFlowService()
