"""Prompt injector for memory enhancement."""
from typing import List
from claude_memory.core.models import Memory, EntityType


class PromptInjector:
    """Inject memories into prompts"""
    
    def format_memories(self, memories: List[Memory]) -> str:
        """Format memories for injection into prompt"""
        if not memories:
            return ""
        
        lines = ["\n[RELEVANT CONTEXT from previous conversations]:"]
        
        for memory in memories:
            prefix = self._get_prefix_for_type(memory.entity_type)
            lines.append(f"  {prefix} {memory.content}")
        
        lines.append("[END CONTEXT]\n")
        
        return "\n".join(lines)
    
    def _get_prefix_for_type(self, entity_type: EntityType) -> str:
        """Get emoji prefix for memory type"""
        prefixes = {
            EntityType.PREFERENCE: "💭",
            EntityType.FACT: "📌",
            EntityType.PROJECT: "📁",
            EntityType.CODE_STYLE: "💻",
            EntityType.DECISION: "✅",
            EntityType.TASK: "📋",
        }
        return prefixes.get(entity_type, "•")
    
    def create_system_prompt(
        self, 
        base_prompt: str, 
        memories: List[Memory],
    ) -> str:
        """Create system prompt with injected memories"""
        memory_section = self.format_memories(memories)
        
        if not memory_section:
            return base_prompt
        
        return f"{base_prompt}\n{memory_section}"
    
    def should_inject(
        self, 
        conversation: List[dict], 
        retrieved_memories: List[Memory],
        threshold: float = 0.6,
    ) -> bool:
        """Decide if memories should be injected"""
        if not retrieved_memories:
            return False
        
        # Always inject if high-importance memories exist
        if any(m.importance > 0.8 for m in retrieved_memories):
            return True
        
        # Check if conversation seems to need context
        last_message = ""
        for msg in reversed(conversation):
            if msg.get("role") == "user":
                last_message = msg.get("content", "").lower()
                break
        
        # Trigger words that suggest need for context
        trigger_words = [
            "remember", "上次", "之前", "我们", "我说过",
            "what did i say", "previously", "before", "we discussed",
        ]
        
        if any(word in last_message for word in trigger_words):
            return True
        
        # Check average relevance score
        avg_importance = sum(m.importance for m in retrieved_memories) / len(retrieved_memories)
        return avg_importance >= threshold
