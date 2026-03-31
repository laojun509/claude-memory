"""LLM-based memory extractor."""
import json
import os
from typing import List, Dict, Any
from litellm import completion

from claude_memory.core.models import Memory, EntityType


EXTRACTION_PROMPT = """You are a memory extraction system. Analyze the conversation and extract important information worth remembering.

Extract memories that fall into these categories:
- preference: User likes/dislikes, preferences ("I hate...", "I prefer...")
- fact: Important facts about user or project ("We are building...", "The API uses...")
- project: Project-specific information
- code_style: Coding conventions and style preferences
- decision: Important decisions made
- task: Action items or todos

For each memory, assign importance (0.0-1.0):
- 0.9-1.0: Critical, core to user's identity or project
- 0.7-0.8: Important, frequently relevant
- 0.4-0.6: Moderately useful
- 0.1-0.3: Minor detail

Return JSON format:
{
    "memories": [
        {
            "content": "concise summary of what to remember",
            "entity_type": "preference|fact|project|code_style|decision|task",
            "importance": 0.8
        }
    ]
}

If nothing worth remembering, return {"memories": []}.
"""


class LLMMemoryExtractor:
    """Extract memories from conversations using LLM"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    
    def extract(self, conversation: List[Dict[str, str]], project_id: str = "default") -> List[Memory]:
        """Extract memories from conversation"""
        if not conversation:
            return []
        
        # Format conversation for LLM
        conv_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in conversation[-10:]  # Last 10 messages
        ])
        
        response = self._call_llm(conv_text)
        
        memories = []
        for mem_data in response.get("memories", []):
            try:
                memory = Memory(
                    content=mem_data["content"],
                    entity_type=EntityType(mem_data.get("entity_type", "fact")),
                    importance=mem_data.get("importance", 0.5),
                    project_id=project_id,
                )
                memories.append(memory)
            except (KeyError, ValueError) as e:
                # Skip invalid memories
                continue
        
        return memories
    
    def _call_llm(self, conversation_text: str) -> Dict[str, Any]:
        """Call LLM to extract memories"""
        try:
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": f"Extract memories from this conversation:\n\n{conversation_text}"},
                ],
                response_format={"type": "json_object"},
                api_key=self.api_key,
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            # Fallback: return empty on error
            return {"memories": []}
