#!/usr/bin/env python3
"""
OpenClaw plugin bridge for Claude Memory.

This script acts as a bridge between OpenClaw/Claude Code and the claude-memory system.
It reads JSON commands from stdin and writes results to stdout.
"""
import sys
import json
import os
from pathlib import Path

# Add parent directory to path to import claude_memory
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_memory.integrations.acp_adapter import ACPMemoryAdapter


class MemoryPluginBridge:
    """Bridge between OpenClaw and claude-memory"""
    
    def __init__(self):
        self.config = self._load_config()
        persist_dir = self.config.get("persist_dir", "~/.claude-memory")
        persist_dir = os.path.expanduser(persist_dir)
        
        self.adapter = ACPMemoryAdapter(
            project_id=self.config.get("project_id", "default"),
            persist_dir=persist_dir,
        )
    
    def _load_config(self) -> dict:
        """Load configuration from environment or default"""
        return {
            "persist_dir": os.getenv("CLAUDE_MEMORY_PERSIST_DIR", "~/.claude-memory"),
            "project_id": os.getenv("CLAUDE_MEMORY_PROJECT", "default"),
            "auto_extract": os.getenv("CLAUDE_MEMORY_AUTO_EXTRACT", "true").lower() == "true",
            "auto_inject": os.getenv("CLAUDE_MEMORY_AUTO_INJECT", "true").lower() == "true",
            "max_memories_inject": int(os.getenv("CLAUDE_MEMORY_MAX_INJECT", "3")),
            "llm_model": os.getenv("CLAUDE_MEMORY_LLM_MODEL", "gpt-4o-mini"),
        }
    
    def handle_command(self, command: dict) -> dict:
        """Handle a command from OpenClaw"""
        cmd_type = command.get("type")
        
        handlers = {
            "search": self._handle_search,
            "store": self._handle_store,
            "recall": self._handle_recall,
            "enhance_prompt": self._handle_enhance_prompt,
            "extract": self._handle_extract,
            "list": self._handle_list,
            "delete": self._handle_delete,
        }
        
        handler = handlers.get(cmd_type)
        if handler:
            return handler(command)
        
        return {"error": f"Unknown command: {cmd_type}"}
    
    def _handle_search(self, command: dict) -> dict:
        """Search memories"""
        query = command.get("query", "")
        limit = command.get("limit", 5)
        
        memories = self.adapter.search(query, limit=limit)
        
        return {
            "type": "search_results",
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "type": m.entity_type.value,
                    "importance": m.importance,
                    "project_id": m.project_id,
                }
                for m in memories
            ],
            "count": len(memories),
        }
    
    def _handle_store(self, command: dict) -> dict:
        """Store a memory manually"""
        content = command.get("content", "")
        memory_type = command.get("memory_type", "fact")
        
        memory_id = self.adapter.add_manual_memory(content, memory_type)
        
        return {
            "type": "stored",
            "memory_id": memory_id,
            "content": content[:50] + "..." if len(content) > 50 else content,
        }
    
    def _handle_recall(self, command: dict) -> dict:
        """Get relevant memories for context"""
        conversation = command.get("conversation", [])
        max_memories = command.get("max_memories", self.config["max_memories_inject"])
        
        memories = self.adapter.get_memory_context(conversation, max_memories=max_memories)
        
        return {
            "type": "context",
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "type": m.entity_type.value,
                    "importance": m.importance,
                }
                for m in memories
            ],
            "should_inject": len(memories) > 0,
        }
    
    def _handle_enhance_prompt(self, command: dict) -> dict:
        """Enhance system prompt with memories"""
        base_prompt = command.get("prompt", "")
        conversation = command.get("conversation", [])
        
        enhanced = self.adapter.enhance_system_prompt(base_prompt, conversation)
        
        return {
            "type": "enhanced_prompt",
            "original": base_prompt,
            "enhanced": enhanced,
            "injected": enhanced != base_prompt,
        }
    
    def _handle_extract(self, command: dict) -> dict:
        """Extract memories from conversation"""
        conversation = command.get("conversation", [])
        
        memories = self.adapter.on_conversation_end(conversation)
        
        return {
            "type": "extracted",
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "type": m.entity_type.value,
                    "importance": m.importance,
                }
                for m in memories
            ],
            "count": len(memories),
        }
    
    def _handle_list(self, command: dict) -> dict:
        """List all memories for project"""
        memories = self.adapter.engine.get_project_memories(self.adapter.project_id)
        
        return {
            "type": "memory_list",
            "project": self.adapter.project_id,
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "type": m.entity_type.value,
                    "importance": m.importance,
                }
                for m in memories
            ],
            "count": len(memories),
        }
    
    def _handle_delete(self, command: dict) -> dict:
        """Delete a memory"""
        memory_id = command.get("memory_id", "")
        
        success = self.adapter.engine.delete_memory(memory_id)
        
        return {
            "type": "deleted",
            "memory_id": memory_id,
            "success": success,
        }


def main():
    """Main entry point - JSON-RPC style communication"""
    bridge = MemoryPluginBridge()
    
    print("Claude Memory Plugin Bridge started", file=sys.stderr)
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            command = json.loads(line)
            result = bridge.handle_command(command)
            print(json.dumps(result), flush=True)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid JSON: {str(e)}"}), flush=True)
        except Exception as e:
            print(json.dumps({"error": f"Error: {str(e)}"}), flush=True)


if __name__ == "__main__":
    main()
