"""Memory store implementation using ChromaDB."""
import json
import os
from datetime import datetime
from typing import List, Optional

import chromadb
from chromadb.config import Settings

from claude_memory.core.models import EntityType, Memory, Relation


class MemoryStore:
    """ChromaDB-based memory storage with semantic search capabilities."""
    
    def __init__(self, persist_dir: str = "./memory_db"):
        """Initialize ChromaDB client and collection.
        
        Args:
            persist_dir: Directory to persist ChromaDB data
        """
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # Get or create the memories collection
        self.collection = self.client.get_or_create_collection(
            name="memories",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add(self, memory: Memory) -> str:
        """Add a memory to the store.
        
        Args:
            memory: The memory to add
            
        Returns:
            The memory_id of the added memory
        """
        # Serialize relations to JSON for storage
        relations_json = json.dumps([
            {
                "target_memory_id": r.target_memory_id,
                "relation_type": r.relation_type,
                "confidence": r.confidence
            }
            for r in memory.relations
        ])
        
        # Prepare metadata
        metadata = {
            "entity_type": memory.entity_type.value,
            "source": memory.source or "",
            "project_id": memory.project_id,
            "importance": memory.importance,
            "timestamp": memory.timestamp.isoformat(),
            "relations": relations_json,
        }
        
        # Add to collection - ChromaDB will generate embeddings from content
        self.collection.add(
            ids=[memory.id],
            documents=[memory.content],
            metadatas=[metadata]
        )
        
        return memory.id
    
    def search(self, query: str, limit: int = 5, project_id: Optional[str] = None) -> List[Memory]:
        """Search memories by semantic similarity.
        
        Args:
            query: The search query
            limit: Maximum number of results
            project_id: Optional project ID to filter by
            
        Returns:
            List of matching memories
        """
        # Build where clause if project_id is specified
        where_clause = {"project_id": project_id} if project_id else None
        
        # Perform semantic search
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_clause
        )
        
        return self._results_to_memories(results)
    
    def get_by_project(self, project_id: str) -> List[Memory]:
        """Get all memories for a specific project.
        
        Args:
            project_id: The project ID to filter by
            
        Returns:
            List of memories in the project
        """
        results = self.collection.get(
            where={"project_id": project_id}
        )
        
        return self._get_results_to_memories(results)
    
    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception:
            return False
    
    def _results_to_memories(self, results) -> List[Memory]:
        """Convert ChromaDB query results to Memory objects."""
        memories = []
        
        if not results or not results['ids'] or not results['ids'][0]:
            return memories
        
        for i, memory_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            document = results['documents'][0][i] if results['documents'] else ""
            
            memory = self._metadata_to_memory(memory_id, document, metadata)
            memories.append(memory)
        
        return memories
    
    def _get_results_to_memories(self, results) -> List[Memory]:
        """Convert ChromaDB get results to Memory objects."""
        memories = []
        
        if not results or not results['ids']:
            return memories
        
        for i, memory_id in enumerate(results['ids']):
            metadata = results['metadatas'][i] if results['metadatas'] else {}
            document = results['documents'][i] if results['documents'] else ""
            
            memory = self._metadata_to_memory(memory_id, document, metadata)
            memories.append(memory)
        
        return memories
    
    def _metadata_to_memory(self, memory_id: str, content: str, metadata: dict) -> Memory:
        """Convert metadata dict to Memory object."""
        # Parse relations from JSON
        relations = []
        relations_json = metadata.get('relations', '[]')
        if relations_json:
            try:
                relations_data = json.loads(relations_json)
                relations = [
                    Relation(
                        target_memory_id=r['target_memory_id'],
                        relation_type=r['relation_type'],
                        confidence=r['confidence']
                    )
                    for r in relations_data
                ]
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Parse timestamp
        timestamp_str = metadata.get('timestamp', '')
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            timestamp = datetime.now()
        
        return Memory(
            id=memory_id,
            content=content,
            entity_type=EntityType(metadata.get('entity_type', 'fact')),
            relations=relations,
            source=metadata.get('source') or None,
            project_id=metadata.get('project_id', 'default'),
            importance=metadata.get('importance', 0.5),
            timestamp=timestamp
        )
