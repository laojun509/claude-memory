# 多模型配置指南

Claude Memory 支持多种大语言模型，包括国产模型。

---

## 支持的模型提供商

| 提供商 | 环境变量 | 默认模型 | 备注 |
|--------|----------|----------|------|
| **OpenAI** | `OPENAI_API_KEY` | `gpt-4o-mini` | 国外，速度快 |
| **Kimi** | `KIMI_API_KEY` | `kimi-coding/k2p5` | 月之暗面，支持长上下文 |
| **GLM** | `GLM_API_KEY` | `glm-4-flash` | 智谱AI，性价比高 |
| **MiniMax** | `MINIMAX_API_KEY` | `minimax-text-01` | 稀宇科技 |
| **DeepSeek** | `DEEPSEEK_API_KEY` | `deepseek-chat` | 深度求索 |
| **通义千问** | `QWEN_API_KEY` | `qwen-turbo` | 阿里云 |

---

## 快速配置

### 方法一：指定提供商（推荐）

```bash
# 使用 GLM
export CLAUDE_MEMORY_LLM_PROVIDER="glm"
export GLM_API_KEY="your-glm-api-key"

# 使用 Kimi
export CLAUDE_MEMORY_LLM_PROVIDER="kimi"
export KIMI_API_KEY="your-kimi-api-key"

# 使用 MiniMax
export CLAUDE_MEMORY_LLM_PROVIDER="minimax"
export MINIMAX_API_KEY="your-minimax-api-key"
```

### 方法二：指定具体模型

```bash
# 自动检测提供商
export GLM_API_KEY="your-glm-api-key"
export CLAUDE_MEMORY_LLM_MODEL="glm-4-flash"  # 自动识别为 GLM
```

### 方法三：完整配置

```bash
# 提供商 + 模型 + 项目
export CLAUDE_MEMORY_LLM_PROVIDER="glm"
export CLAUDE_MEMORY_LLM_MODEL="glm-4-flash"
export GLM_API_KEY="your-glm-api-key"
export CLAUDE_MEMORY_PROJECT="my-project"
```

---

## 各平台 API Key 获取

### GLM (智谱AI)
1. 访问 https://open.bigmodel.cn/
2. 注册账号 → 创建 API Key
3. 复制 Key 到环境变量

### Kimi (月之暗面)
1. 访问 https://platform.moonshot.cn/
2. 注册账号 → 创建 API Key
3. 复制 Key 到环境变量

### MiniMax
1. 访问 https://www.minimaxi.com/
2. 注册账号 → 获取 API Key

### DeepSeek
1. 访问 https://platform.deepseek.com/
2. 注册账号 → 创建 API Key

### 通义千问
1. 访问 https://dashscope.aliyun.com/
2. 阿里云账号 → 创建 API Key

---

## 推荐模型

### 性价比之选
- **GLM-4-Flash**: 免费/低价，速度快，适合提取任务
- **DeepSeek-Chat**: 价格便宜，效果好

### 质量之选
- **Kimi k2.5**: 支持超长上下文，理解能力强
- **GLM-4**: 综合能力最强

### 速度之选
- **GPT-4o-mini**: 国外，速度最快
- **GLM-4-Flash**: 国内，速度也很快

---

## 配置示例

### .bashrc / .zshrc

```bash
# Claude Memory 配置
export CLAUDE_MEMORY_PROJECT="default"
export CLAUDE_MEMORY_PERSIST_DIR="~/.claude-memory"

# 选择提供商（ Uncomment 你想用的 ）
# export CLAUDE_MEMORY_LLM_PROVIDER="openai"
# export OPENAI_API_KEY="sk-..."

export CLAUDE_MEMORY_LLM_PROVIDER="glm"
export GLM_API_KEY="your-glm-key"

# export CLAUDE_MEMORY_LLM_PROVIDER="kimi"
# export KIMI_API_KEY="your-kimi-key"
```

### 临时切换（单次会话）

```bash
# 默认用 GLM
export CLAUDE_MEMORY_LLM_PROVIDER="glm"
export GLM_API_KEY="xxx"
claude-code

# 另一个终端用 Kimi
export CLAUDE_MEMORY_LLM_PROVIDER="kimi"
export KIMI_API_KEY="yyy"
claude-code
```

---

## 故障排除

### 问题: "API Key not found"

**检查**:
```bash
echo $GLM_API_KEY  # 或其他对应 key
echo $CLAUDE_MEMORY_LLM_PROVIDER
```

**解决**:
```bash
export CLAUDE_MEMORY_LLM_PROVIDER="glm"
export GLM_API_KEY="your-actual-key"
```

### 问题: "Model not found"

**检查模型名称**:
```bash
# GLM
glm-4-flash      ✅
glm-4            ✅
chatglm-3        ❌ (旧版不支持)

# Kimi
kimi-coding/k2p5 ✅
kimi-k2.5        ✅

# MiniMax
minimax-text-01  ✅
```

### 问题: API 调用超时

**原因**: 某些国产模型响应较慢

**解决**:
- 换更快的模型（如 GLM-4-Flash）
- 检查网络连接
- 或减少 `max_memories_inject` 降低调用频率

---

## 高级：自定义模型

如果你有自己的模型 API：

```bash
# 通过 LiteLLM 代理
export OPENAI_API_KEY="your-key"
export OPENAI_API_BASE="https://your-custom-api.com/v1"
export CLAUDE_MEMORY_LLM_MODEL="gpt-4"  # 实际会路由到你的 API
```

---

## 模型对比

| 模型 | 价格 | 速度 | 中文 | 推荐度 |
|------|------|------|------|--------|
| GPT-4o-mini | $ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| GLM-4-Flash | ¥/免费 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Kimi k2.5 | ¥ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| DeepSeek-Chat | ¥ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| MiniMax | ¥ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

**推荐**: 国内用户首选 **GLM-4-Flash**（免费/低价 + 速度快 + 中文好）
