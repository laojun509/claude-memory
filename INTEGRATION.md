# Claude Memory - OpenClaw 集成指南

将本地智能记忆系统集成到 Claude Code 中。

---

## 快速安装

```bash
cd /root/.openclaw/workspace/claude-memory
chmod +x openclaw-plugin/install.sh
./openclaw-plugin/install.sh
```

---

## 手动配置

### 1. 环境变量

在你的 shell 配置文件（`~/.bashrc`, `~/.zshrc` 等）中添加：

**Option A: 使用 OpenAI（默认）**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

**Option B: 使用国产模型（推荐国内用户）**
```bash
# GLM (智谱AI) - 免费/低价，速度快
export CLAUDE_MEMORY_LLM_PROVIDER="glm"
export GLM_API_KEY="your-glm-api-key"

# 或 Kimi (月之暗面)
# export CLAUDE_MEMORY_LLM_PROVIDER="kimi"
# export KIMI_API_KEY="your-kimi-api-key"

# 或 MiniMax
# export CLAUDE_MEMORY_LLM_PROVIDER="minimax"
# export MINIMAX_API_KEY="your-minimax-key"
```

**通用配置（所有提供商都适用）**
```bash
export CLAUDE_MEMORY_PROJECT="default"
export CLAUDE_MEMORY_PERSIST_DIR="~/.claude-memory"
export CLAUDE_MEMORY_AUTO_EXTRACT="true"
export CLAUDE_MEMORY_AUTO_INJECT="true"
export CLAUDE_MEMORY_MAX_INJECT="3"
```

**支持的提供商**: `openai`, `kimi`, `glm`, `minimax`, `deepseek`, `qwen`

详细配置参见 [MODEL_CONFIG.md](MODEL_CONFIG.md)

### 2. 安装 OpenClaw 插件

```bash
# 创建插件目录
mkdir -p ~/.openclaw/extensions/claude-memory

# 复制文件
cp openclaw-plugin/bridge.py ~/.openclaw/extensions/claude-memory/
cp openclaw-plugin/index.ts ~/.openclaw/extensions/claude-memory/
cp openclaw-plugin/plugin.json ~/.openclaw/extensions/claude-memory/openclaw.plugin.json
```

### 3. 重启 Claude Code

```bash
# 如果使用 OpenClaw
openclaw restart

# 如果使用 Claude Code directly
# 重启 Claude Code 应用
```

---

## 使用方法

### 自动功能

安装后，以下功能会自动工作：

| 功能 | 触发时机 | 效果 |
|------|----------|------|
| **自动提取** | 每次对话结束 | AI 自动分析并保存重要信息 |
| **自动注入** | 每次对话开始 | 自动在 prompt 中注入相关记忆 |
| **项目隔离** | 根据 project_id | 不同项目有独立记忆空间 |

### 手动工具

在 Claude Code 中使用以下命令：

```
# 搜索记忆
/memory_search "backend framework"

# 手动存储记忆
/memory_store "I prefer FastAPI over Flask"

# 列出所有记忆
/memory_list

# 切换项目（设置环境变量后重启）
export CLAUDE_MEMORY_PROJECT="my-new-project"
```

---

## 演示场景

### 场景 1: 记住偏好

**你**: "我讨厌写 CSS，更喜欢用 Tailwind"

→ **系统自动提取**: `[PREFERENCE] User prefers Tailwind CSS over plain CSS`

**3天后**:
**你**: "我应该用什么做样式？"

→ **系统自动注入**: `💭 User prefers Tailwind CSS over plain CSS`

**Claude**: "基于你之前的偏好，我建议使用 Tailwind CSS..."

---

### 场景 2: 项目记忆

**你**: "这个项目用 FastAPI + PostgreSQL"

→ **系统自动提取**: `[PROJECT] Project uses FastAPI and PostgreSQL`

**1周后**:
**你**: "怎么连接数据库？"

→ **系统自动注入**: `📁 Project uses FastAPI and PostgreSQL`

**Claude**: "因为你用 PostgreSQL，可以这样配置 SQLAlchemy..."

---

### 场景 3: 代码风格

**你**: "我所有的函数都要加类型注解"

→ **系统自动提取**: `[CODE_STYLE] User requires type annotations on all functions`

**后续代码生成**:
→ **系统自动注入**: `💻 User requires type annotations on all functions`

**Claude 生成的代码**: `def process(data: str) -> dict:` ✅

---

## 故障排除

### 问题: 插件没有加载

**检查**:
```bash
ls ~/.openclaw/extensions/claude-memory/
# 应该有: bridge.py, index.ts, openclaw.plugin.json
```

**解决**:
```bash
# 检查 OpenClaw 日志
openclaw logs

# 重新安装
./openclaw-plugin/install.sh
```

### 问题: 记忆没有保存

**检查**:
```bash
# 检查 API key
echo $OPENAI_API_KEY

# 检查存储目录
ls ~/.claude-memory/
```

**解决**:
```bash
# 设置 API key
export OPENAI_API_KEY="sk-..."

# 检查目录权限
chmod 755 ~/.claude-memory
```

### 问题: 记忆没有注入

**检查**:
- 确保 `CLAUDE_MEMORY_AUTO_INJECT=true`
- 检查是否有相关记忆: `/memory_search "关键词"`

**解决**:
```bash
# 手动触发搜索查看
claude-memory search "关键词"
```

---

## 高级配置

### 自定义记忆类型权重

编辑 `claude_memory/injectors/prompt_injector.py`:

```python
type_weights = {
    EntityType.DECISION: 0.2,      # 提高决策优先级
    EntityType.PREFERENCE: 0.15,
    EntityType.PROJECT: 0.1,
    # ...
}
```

### 多项目管理

```bash
# 项目 A
export CLAUDE_MEMORY_PROJECT="project-a"
claude-code

# 项目 B (新终端)
export CLAUDE_MEMORY_PROJECT="project-b"
claude-code
```

---

## 文件位置

| 文件 | 路径 |
|------|------|
| 记忆数据库 | `~/.claude-memory/` |
| 插件代码 | `~/.openclaw/extensions/claude-memory/` |
| 项目源码 | `/root/.openclaw/workspace/claude-memory/` |

---

## 卸载

```bash
# 删除插件
rm -rf ~/.openclaw/extensions/claude-memory

# 删除记忆数据（可选）
rm -rf ~/.claude-memory

# 重启 Claude Code
```

---

## 下一步

- 🎯 使用几天后观察效果
- 📝 根据需要调整 `max_memories_inject`
- 🔄 考虑分享给团队使用
- 🚀 贡献代码到项目
