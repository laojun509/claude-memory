# Claude Memory

Intelligent memory layer for Claude Code - now with multi-model support (OpenAI, Kimi, GLM, MiniMax, DeepSeek, Qwen).

## Features

- 🧠 **Automatic Memory Extraction** - LLM-powered analysis of conversations
- 💾 **Local Vector Storage** - ChromaDB-based, fully offline
- 🎯 **Smart Retrieval** - Context-aware memory recall
- 💉 **Prompt Injection** - Automatic memory enhancement
- 📁 **Project Isolation** - Separate memory spaces per project
- 🔧 **CLI Tools** - Manage memories from command line
- 🌐 **Multi-Model Support** - OpenAI, Kimi, GLM, MiniMax, DeepSeek, Qwen

## Quick Start

### 1. Install

```bash
pip install -e ".[dev]"
```

### 2. Configure (Choose your provider)

**Option A: OpenAI (Default)**
```bash
export OPENAI_API_KEY="your-openai-key"
```

**Option B: GLM (智谱AI) - 推荐国内用户**
```bash
export CLAUDE_MEMORY_LLM_PROVIDER="glm"
export GLM_API_KEY="your-glm-key"
```

**Option C: Kimi (月之暗面)**
```bash
export CLAUDE_MEMORY_LLM_PROVIDER="kimi"
export KIMI_API_KEY="your-kimi-key"
```

**Option D: MiniMax, DeepSeek, Qwen...**
```bash
export CLAUDE_MEMORY_LLM_PROVIDER="minimax"  # or "deepseek", "qwen"
export MINIMAX_API_KEY="your-key"
```

### 3. Use in Python

```python
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

## Supported Models

| Provider | Environment Variable | Default Model |
|----------|---------------------|---------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` |
| Kimi | `KIMI_API_KEY` | `kimi-coding/k2p5` |
| GLM | `GLM_API_KEY` | `glm-4-flash` |
| MiniMax | `MINIMAX_API_KEY` | `minimax-text-01` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-chat` |
| Qwen | `QWEN_API_KEY` | `qwen-turbo` |

## Documentation

- [Architecture Design](docs/plans/2026-03-31-ai-memory-design.md)
- [Model Configuration](MODEL_CONFIG.md) - Detailed multi-model setup guide
- [OpenClaw Integration](INTEGRATION.md) - Install as Claude Code plugin

## License

MIT
