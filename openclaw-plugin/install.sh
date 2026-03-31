#!/bin/bash
# Installation script for Claude Memory OpenClaw Plugin

set -e

echo "🧠 Installing Claude Memory for OpenClaw..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.11+ required, found $python_version"
    exit 1
fi

# Install the package
echo "📦 Installing claude-memory package..."
cd "$PROJECT_DIR"
pip install -e "." -q

# Create plugin directory in OpenClaw
PLUGIN_DIR="$HOME/.openclaw/extensions/claude-memory"
mkdir -p "$PLUGIN_DIR"

# Copy plugin files
echo "🔌 Setting up OpenClaw plugin..."
cp "$PROJECT_DIR/openclaw-plugin/bridge.py" "$PLUGIN_DIR/"
cp "$PROJECT_DIR/openclaw-plugin/plugin.json" "$PLUGIN_DIR/openclaw.plugin.json"

# Create wrapper script
cat > "$PLUGIN_DIR/run.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}/../../:$PYTHONPATH"
python3 "${SCRIPT_DIR}/bridge.py"
EOF

chmod +x "$PLUGIN_DIR/run.sh"

# Create TypeScript wrapper
cat > "$PLUGIN_DIR/index.ts" << 'EOF'
import type { OpenClawPluginApi } from "openclaw/plugin-sdk"

export default {
  id: "claude-memory",
  name: "Claude Memory",
  description: "Local intelligent memory system for Claude Code",
  kind: "memory" as const,

  register(api: OpenClawPluginApi) {
    api.logger.info("claude-memory: plugin loaded")
    
    // Register memory tools
    api.registerTool({
      name: "memory_search",
      label: "Search Memories",
      description: "Search through stored memories",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string", description: "Search query" },
          limit: { type: "number", default: 5 },
        },
        required: ["query"],
      },
      async execute(_id: string, params: { query: string; limit?: number }) {
        const result = await callBridge({ type: "search", query: params.query, limit: params.limit || 5 })
        return {
          content: [{ type: "text", text: formatSearchResults(result) }],
        }
      },
    }, { name: "memory_search" })

    api.registerTool({
      name: "memory_store",
      label: "Store Memory",
      description: "Manually store a memory",
      parameters: {
        type: "object",
        properties: {
          content: { type: "string", description: "Content to remember" },
          memory_type: { type: "string", enum: ["preference", "fact", "project", "code_style", "decision", "task"], default: "fact" },
        },
        required: ["content"],
      },
      async execute(_id: string, params: { content: string; memory_type?: string }) {
        const result = await callBridge({ type: "store", content: params.content, memory_type: params.memory_type || "fact" })
        return {
          content: [{ type: "text", text: `✅ Stored: ${result.content}` }],
        }
      },
    }, { name: "memory_store" })

    api.registerTool({
      name: "memory_list",
      label: "List Memories",
      description: "List all memories for current project",
      parameters: { type: "object", properties: {} },
      async execute() {
        const result = await callBridge({ type: "list" })
        return {
          content: [{ type: "text", text: formatMemoryList(result) }],
        }
      },
    }, { name: "memory_list" })

    // Hook into conversation lifecycle
    api.on("before_agent_start", async (event: any, ctx: any) => {
      if (!event.messages || event.messages.length === 0) return
      
      // Get relevant memories and inject into system prompt
      const result = await callBridge({
        type: "enhance_prompt",
        prompt: event.systemPrompt || "",
        conversation: event.messages.slice(-5), // Last 5 messages
      })
      
      if (result.injected) {
        event.systemPrompt = result.enhanced
        api.logger.debug("claude-memory: injected relevant memories")
      }
    })

    api.on("agent_end", async (event: any, ctx: any) => {
      if (!event.messages || event.messages.length < 2) return
      
      // Extract memories from conversation
      const result = await callBridge({
        type: "extract",
        conversation: event.messages,
      })
      
      if (result.count > 0) {
        api.logger.info(`claude-memory: extracted ${result.count} memories`)
      }
    })

    api.logger.info("claude-memory: plugin ready")
  },
}

// Helper to call Python bridge
async function callBridge(command: any): Promise<any> {
  const { execSync } = require("child_process")
  const scriptDir = __dirname
  const bridgePath = `${scriptDir}/bridge.py`
  
  try {
    const result = execSync(`echo '${JSON.stringify(command)}' | python3 "${bridgePath}"`, {
      encoding: "utf-8",
      timeout: 10000,
    })
    return JSON.parse(result.trim().split("\n").pop() || "{}")
  } catch (e) {
    return { error: String(e) }
  }
}

function formatSearchResults(result: any): string {
  if (!result.memories || result.memories.length === 0) {
    return "No memories found."
  }
  return result.memories.map((m: any) => `• [${m.type}] ${m.content}`).join("\n")
}

function formatMemoryList(result: any): string {
  if (!result.memories || result.memories.length === 0) {
    return `No memories for project '${result.project}'.`
  }
  const lines = [`Project: ${result.project} (${result.count} memories)\n`]
  lines.push(...result.memories.map((m: any) => `• [${m.type}] ${m.content} (importance: ${m.importance})`))
  return lines.join("\n")
}
EOF

echo ""
echo "✅ Claude Memory plugin installed successfully!"
echo ""
echo "📍 Plugin location: $PLUGIN_DIR"
echo ""
echo "📝 Configuration:"
echo "   Set environment variables in your shell profile:"
echo "   export OPENAI_API_KEY='your-api-key'"
echo "   export CLAUDE_MEMORY_PROJECT='default'"
echo ""
echo "🔧 Usage:"
echo "   Restart OpenClaw/Claude Code to load the plugin"
echo "   The plugin will automatically:"
echo "   • Extract memories from conversations"
echo "   • Inject relevant memories into prompts"
echo ""
echo "🛠️  Available tools:"
echo "   • memory_search - Search stored memories"
echo "   • memory_store - Manually store a memory"
echo "   • memory_list - List all project memories"
echo ""
