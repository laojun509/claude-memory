# Claude Memory

Intelligent memory layer for Claude Code.

## Features

- 🧠 **Automatic Memory Extraction** - LLM-powered analysis of conversations
- 💾 **Local Vector Storage** - ChromaDB-based, fully offline
- 🎯 **Smart Retrieval** - Context-aware memory recall
- 💉 **Prompt Injection** - Automatic memory enhancement
- 📁 **Project Isolation** - Separate memory spaces per project
- 🔧 **CLI Tools** - Manage memories from command line

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Set API key for extraction
export OPENAI_API_KEY="your-key"

# Use in Python
from claude_memory.integrations.acp_adapter import ACPMemoryAdapter

adapter = ACPMemoryAdapter(project_id="my_project")

# After conversation
memories = adapter.on_conversation_end(conversation)

# Enhance prompt with memories
enhanced_prompt = adapter.enhance_system_prompt(base_prompt, conversation)
```

## CLI Usage

```bash
# Search memories
claude-memory search "backend"

# List all memories for project
claude-memory list-memories --project my_project

# Show stats
claude-memory stats
```

## Architecture

See `docs/plans/2026-03-31-ai-memory-design.md`
