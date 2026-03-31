"""LLM-based memory extractor with multi-provider support."""
import json
import os
from typing import List, Dict, Any, Optional
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

# Provider configuration mapping
PROVIDER_CONFIG = {
    "openai": {
        "model_prefix": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "base_url": None,
    },
    "kimi": {
        "model_prefix": "kimi-coding/k2p5",
        "env_key": "KIMI_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
    },
    "glm": {
        "model_prefix": "glm-4-flash",
        "env_key": "GLM_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
    },
    "minimax": {
        "model_prefix": "minimax-text-01",
        "env_key": "MINIMAX_API_KEY",
        "base_url": "https://api.minimax.chat/v1",
    },
    "deepseek": {
        "model_prefix": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
    },
    "deepseek-v3": {
        "model_prefix": "deepseek/deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
    },
    "qwen": {
        "model_prefix": "qwen-turbo",
        "env_key": "QWEN_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    },
}


class LLMMemoryExtractor:
    """Extract memories from conversations using LLM (multi-provider support)"""
    
    def __init__(self, model: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize extractor.
        
        Args:
            model: Model name (e.g., "gpt-4o-mini", "glm-4-flash")
            provider: Provider name (e.g., "openai", "kimi", "glm", "minimax")
                   If not specified, auto-detected from model name or env var
        """
        # Auto-detect provider from env var or model name
        self.provider = provider or self._detect_provider(model)
        self.model = model or self._get_default_model(self.provider)
        self.api_key = self._get_api_key(self.provider)
        self.base_url = self._get_base_url(self.provider)
    
    def _detect_provider(self, model: Optional[str]) -> str:
        """Auto-detect provider from model name or environment"""
        # Check environment variable first
        env_provider = os.getenv("CLAUDE_MEMORY_LLM_PROVIDER", "").lower()
        if env_provider and env_provider in PROVIDER_CONFIG:
            return env_provider
        
        # Detect from model name
        if model:
            model_lower = model.lower()
            if "kimi" in model_lower:
                return "kimi"
            elif "glm" in model_lower or "chatglm" in model_lower:
                return "glm"
            elif "minimax" in model_lower:
                return "minimax"
            elif "deepseek" in model_lower:
                return "deepseek"
            elif "qwen" in model_lower or "qwen" in model_lower:
                return "qwen"
            elif "gpt" in model_lower:
                return "openai"
        
        # Default fallback - check which API key is available
        for provider, config in PROVIDER_CONFIG.items():
            if os.getenv(config["env_key"]):
                return provider
        
        # Final fallback
        return "openai"
    
    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider"""
        return PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG["openai"])["model_prefix"]
    
    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for provider"""
        config = PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG["openai"])
        
        # Try specific key first, then fallback to generic
        api_key = os.getenv(config["env_key"])
        if not api_key:
            api_key = os.getenv("LLM_API_KEY")  # Generic fallback
        
        return api_key
    
    def _get_base_url(self, provider: str) -> Optional[str]:
        """Get base URL for provider"""
        config = PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG["openai"])
        return config["base_url"]
    
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
            # Build completion kwargs
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": f"Extract memories from this conversation:\n\n{conversation_text}"},
                ],
                "api_key": self.api_key,
            }
            
            # Add base_url if specified
            if self.base_url:
                kwargs["base_url"] = self.base_url
            
            # Try to use JSON mode if supported
            try:
                response = completion(**kwargs, response_format={"type": "json_object"})
            except Exception:
                # Fallback without JSON mode for providers that don't support it
                response = completion(**kwargs)
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to extraction
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from text
                return self._extract_json_from_text(content)
                
        except Exception as e:
            print(f"[claude-memory] LLM error: {e}")
            # Fallback: return empty on error
            return {"memories": []}
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response (for models without JSON mode)"""
        import re
        
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try to extract memories from plain text
        memories = []
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and len(line) > 10:
                # Simple heuristic: treat lines as memories
                memories.append({
                    "content": line[:200],  # Limit length
                    "entity_type": "fact",
                    "importance": 0.5,
                })
        
        return {"memories": memories[:5]}  # Limit to 5 memories
    
    @classmethod
    def list_supported_providers(cls) -> List[str]:
        """List all supported providers"""
        return list(PROVIDER_CONFIG.keys())
    
    @classmethod
    def get_provider_info(cls, provider: str) -> Dict[str, str]:
        """Get information about a provider"""
        return PROVIDER_CONFIG.get(provider, {})
