"""Smart memory retriever with ranking."""
from typing import List, Optional
from datetime import datetime, timedelta

from claude_memory.core.store import MemoryStore
from claude_memory.core.models import Memory, EntityType


class SmartRetriever:
    """Intelligent memory retrieval with ranking"""
    
    def __init__(self, store: MemoryStore):
        self.store = store
    
    def retrieve(
        self, 
        query: str, 
        project_id: str = "default",
        limit: int = 5,
        entity_types: Optional[List[EntityType]] = None,
    ) -> List[Memory]:
        """Retrieve and rank relevant memories"""
        # Get candidates from vector search
        candidates = self.store.search(query, limit=limit * 2, project_id=project_id)
        
        if not candidates:
            return []
        
        # Score and rank
        scored = []
        for memory in candidates:
            score = self._calculate_relevance_score(memory, query)
            scored.append((score, memory))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Filter by entity type if specified
        if entity_types:
            scored = [(s, m) for s, m in scored if m.entity_type in entity_types]
        
        return [m for _, m in scored[:limit]]
    
    def _calculate_relevance_score(self, memory: Memory, query: str) -> float:
        """Calculate relevance score for a memory"""
        score = 0.0
        
        # Base score from importance
        score += memory.importance * 0.4
        
        # Recency boost (memories from last 7 days get boost)
        days_old = (datetime.now() - memory.timestamp).days
        if days_old < 7:
            score += 0.2 * (1 - days_old / 7)
        
        # Entity type boost (preferences and decisions are more important)
        type_weights = {
            EntityType.DECISION: 0.2,
            EntityType.PREFERENCE: 0.15,
            EntityType.PROJECT: 0.1,
            EntityType.CODE_STYLE: 0.1,
            EntityType.FACT: 0.05,
            EntityType.TASK: 0.05,
        }
        score += type_weights.get(memory.entity_type, 0)
        
        return min(score, 1.0)
    
    def get_context_for_conversation(
        self, 
        conversation: List[dict], 
        project_id: str = "default",
        max_memories: int = 3,
    ) -> List[Memory]:
        """Get relevant context for a conversation"""
        if not conversation:
            return []
        
        # Use last user message as query
        last_user_msg = None
        for msg in reversed(conversation):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        
        if not last_user_msg:
            return []
        
        return self.retrieve(last_user_msg, project_id=project_id, limit=max_memories)
