"""
ACP (Agent Communication Protocol) adapter for Claude Code integration.

This module provides hooks for Claude Code to:
1. Extract memories from conversations
2. Inject relevant memories into prompts
3. Manage project-specific memory contexts
"""
from typing import List, Dict, Any, Optional
from claude_memory.core.engine import MemoryEngine
from claude_memory.core.models import Memory


class ACPMemoryAdapter:
    """Adapter for integrating with Claude Code via ACP/MCP"""
    
    def __init__(self, project_id: str = "default", persist_dir: str = "./memory_db"):
        self.project_id = project_id
        self.engine = MemoryEngine(persist_dir=persist_dir)
    
    def on_conversation_start(self, conversation_id: str) -> None:
        """Called when a new conversation starts"""
        # Could log conversation start, initialize context, etc.
        pass
    
    def on_conversation_end(self, conversation: List[Dict[str, str]]) -> List[Memory]:
        """Called when conversation ends - extract and store memories"""
        return self.engine.process_conversation(conversation, project_id=self.project_id)
    
    def enhance_system_prompt(
        self, 
        base_prompt: str, 
        conversation: List[Dict[str, str]],
    ) -> str:
        """Enhance system prompt with relevant memories"""
        return self.engine.get_enhanced_system_prompt(
            base_prompt, 
            conversation, 
            project_id=self.project_id,
        )
    
    def get_memory_context(
        self, 
        conversation: List[Dict[str, str]], 
        max_memories: int = 3,
    ) -> List[Memory]:
        """Get relevant memory context for conversation"""
        return self.engine.get_context(
            conversation, 
            project_id=self.project_id,
            max_memories=max_memories,
        )
    
    def search(self, query: str, limit: int = 5) -> List[Memory]:
        """Search memories"""
        return self.engine.search_memories(query, project_id=self.project_id, limit=limit)
    
    def add_manual_memory(self, content: str, memory_type: str = "fact") -> str:
        """Manually add a memory"""
        from claude_memory.core.models import Memory, EntityType
        
        memory = Memory(
            content=content,
            entity_type=EntityType(memory_type),
            project_id=self.project_id,
            importance=0.7,
        )
        return self.engine.store.add(memory)
