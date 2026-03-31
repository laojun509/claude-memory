"""Core memory orchestration engine."""
from typing import List, Dict, Any
from pathlib import Path

from claude_memory.core.store import MemoryStore
from claude_memory.core.models import Memory
from claude_memory.extractors.llm_extractor import LLMMemoryExtractor
from claude_memory.retrievers.smart_retriever import SmartRetriever
from claude_memory.injectors.prompt_injector import PromptInjector


class MemoryEngine:
    """Core memory orchestration engine"""
    
    def __init__(self, persist_dir: str = "./memory_db"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.store = MemoryStore(str(self.persist_dir))
        self.extractor = LLMMemoryExtractor()
        self.retriever = SmartRetriever(self.store)
        self.injector = PromptInjector()
    
    def process_conversation(
        self, 
        conversation: List[Dict[str, str]], 
        project_id: str = "default",
    ) -> List[Memory]:
        """Process conversation: extract and store memories"""
        # Extract memories
        memories = self.extractor.extract(conversation, project_id=project_id)
        
        # Store each memory
        stored = []
        for memory in memories:
            memory_id = self.store.add(memory)
            stored.append(memory)
        
        return stored
    
    def get_context(
        self, 
        conversation: List[Dict[str, str]], 
        project_id: str = "default",
        max_memories: int = 3,
    ) -> List[Memory]:
        """Get relevant context for conversation"""
        return self.retriever.get_context_for_conversation(
            conversation, 
            project_id=project_id,
            max_memories=max_memories,
        )
    
    def get_enhanced_system_prompt(
        self,
        base_prompt: str,
        conversation: List[Dict[str, str]],
        project_id: str = "default",
    ) -> str:
        """Get system prompt with injected memories"""
        # Retrieve relevant memories
        memories = self.get_context(conversation, project_id=project_id)
        
        # Decide if injection is needed
        if self.injector.should_inject(conversation, memories):
            return self.injector.create_system_prompt(base_prompt, memories)
        
        return base_prompt
    
    def search_memories(
        self, 
        query: str, 
        project_id: str = "default",
        limit: int = 5,
    ) -> List[Memory]:
        """Search stored memories"""
        return self.store.search(query, limit=limit, project_id=project_id)
    
    def get_project_memories(self, project_id: str) -> List[Memory]:
        """Get all memories for a project"""
        return self.store.get_by_project(project_id)
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory"""
        return self.store.delete(memory_id)
