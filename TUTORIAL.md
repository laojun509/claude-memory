# Claude Memory 使用教程

> 让 Claude Code 记住你的一切

---

## 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [日常使用](#日常使用)
4. [实际场景示例](#实际场景示例)
5. [高级配置](#高级配置)
6. [故障排除](#故障排除)

---

## 快速开始

### 安装（5分钟）

```bash
# 1. 克隆项目
cd /root/.openclaw/workspace/claude-memory

# 2. 安装依赖
pip install -e ".[dev]"

# 3. 配置模型（以 GLM 为例）
export CLAUDE_MEMORY_LLM_PROVIDER="glm"
export GLM_API_KEY="your-glm-api-key"

# 4. 验证安装
claude-memory --help
```

### 首次使用

```bash
# 查看当前记忆
claude-memory list-memories

# 手动添加一条记忆
claude-memory store "我喜欢用 FastAPI 而不是 Flask"

# 搜索记忆
claude-memory search "backend"
```

---

## 核心概念

### 记忆类型

Claude Memory 会自动识别并分类以下信息：

| 类型 | 图标 | 示例 |
|------|------|------|
| **Preference** | 💭 | 用户偏好、喜好/厌恶 |
| **Fact** | 📌 | 项目事实、技术栈 |
| **Project** | 📁 | 项目配置、架构决策 |
| **Code Style** | 💻 | 代码规范、风格偏好 |
| **Decision** | ✅ | 重要决策、方案选择 |
| **Task** | 📋 | 待办事项、行动计划 |

### 记忆生命周期

```
对话发生
    ↓
自动提取（LLM 分析）
    ↓
向量存储（ChromaDB）
    ↓
语义索引
    ↓
智能检索（相关时）
    ↓
Prompt 注入
    ↓
Claude 基于记忆回复
```

### 项目隔离

不同项目完全隔离记忆：

```bash
# 项目 A
export CLAUDE_MEMORY_PROJECT="project-a"
claude-code  # 启动 Claude Code

# 项目 B（另一个终端）
export CLAUDE_MEMORY_PROJECT="project-b"
claude-code  # 完全不同的记忆空间
```

---

## 日常使用

### CLI 命令

```bash
# 搜索记忆
claude-memory search "关键词"
claude-memory search "backend" --limit 10

# 列出项目所有记忆
claude-memory list-memories
claude-memory list-memories --project my-project

# 手动存储记忆
claude-memory store "内容"
claude-memory store "我喜欢 TypeScript" --type preference

# 查看统计
claude-memory stats
```

### Python API

```python
from claude_memory.integrations.acp_adapter import ACPMemoryAdapter

# 初始化
adapter = ACPMemoryAdapter(project_id="my-project")

# 场景 1: 对话结束后提取记忆
conversation = [
    {"role": "user", "content": "我讨厌写 CSS"},
    {"role": "assistant", "content": "明白，你更喜欢后端"},
]
memories = adapter.on_conversation_end(conversation)
print(f"提取了 {len(memories)} 条记忆")

# 场景 2: 获取记忆上下文
new_conversation = [{"role": "user", "content": "推荐个样式方案"}]
context = adapter.get_memory_context(new_conversation)
for m in context:
    print(f"💭 {m.content}")

# 场景 3: 增强 Prompt
base_prompt = "You are a helpful assistant."
enhanced = adapter.enhance_system_prompt(base_prompt, new_conversation)
print(enhanced)  # 包含相关记忆

# 场景 4: 搜索记忆
results = adapter.search("backend framework", limit=5)

# 场景 5: 手动添加
adapter.add_manual_memory("项目用 PostgreSQL", memory_type="fact")
```

---

## 实际场景示例

### 场景 1: 记住技术偏好

**对话 1**:
```
你: 我讨厌写 CSS，Tailwind 稍微好点
Claude: 了解了，你偏好 Tailwind
```

➡️ **自动提取**: `[PREFERENCE] 用户偏好 Tailwind CSS，讨厌原生 CSS`

**3天后对话 2**:
```
你: 这个页面怎么布局？

Claude (内心): 💭 用户偏好 Tailwind CSS，讨厌原生 CSS

Claude: 因为你偏好 Tailwind，我建议这样写：
<div class="flex flex-col gap-4">
  ...
</div>
```

---

### 场景 2: 项目技术栈

**对话 1**:
```
你: 这个项目用 FastAPI + PostgreSQL + Redis
Claude: 好的，技术栈已记录
```

➡️ **自动提取**: `[PROJECT] 项目使用 FastAPI, PostgreSQL, Redis`

**1周后**:
```
你: 怎么设计数据库？

Claude (内心): 📁 项目使用 FastAPI, PostgreSQL, Redis

Claude: 因为你用 PostgreSQL，可以这样设计表结构：
- 使用 SQLAlchemy 2.0 语法
- 利用 PostgreSQL 的 JSONB 字段
- 连接池配置...
```

---

### 场景 3: 代码风格

**对话 1**:
```
你: 所有函数必须加类型注解，不要用 Any
Claude: 好的，代码风格已记录
```

➡️ **自动提取**: `[CODE_STYLE] 函数必须加类型注解，禁止使用 Any`

**后续代码生成**:
```
你: 写个处理数据的函数

Claude (内心): 💻 函数必须加类型注解，禁止使用 Any

Claude: 
def process_data(data: dict[str, int]) -> list[str]:
    # 没有使用 Any ✅
    ...
```

---

### 场景 4: 架构决策

**对话 1**:
```
你: 我们决定用微服务架构，服务间用 gRPC 通信
Claude: 重要决策已记录
```

➡️ **自动提取**: `[DECISION] 采用微服务架构，服务间通信使用 gRPC`

**2个月后**:
```
你: 新模块怎么设计？

Claude (内心): ✅ 采用微服务架构，服务间通信使用 gRPC

Claude: 根据之前的架构决策，新模块应该：
1. 作为独立微服务部署
2. 对外暴露 gRPC 接口
3. ...
```

---

### 场景 5: 待办任务

**对话 1**:
```
你: 记得下周重构 auth 模块
Claude: 任务已记录
```

➡️ **自动提取**: `[TASK] 下周重构 auth 模块`

**几天后**:
```
你: 我有什么要做的？

Claude (内心): 📋 下周重构 auth 模块

Claude: 你有待办任务：
1. 重构 auth 模块（上周提到的）
```

---

## 高级配置

### 自定义记忆权重

编辑 `~/.claude-memory/config.json`（可选）:

```json
{
  "type_weights": {
    "decision": 0.3,
    "preference": 0.25,
    "project": 0.2,
    "code_style": 0.15,
    "fact": 0.05,
    "task": 0.05
  },
  "recency_decay": 7,
  "max_inject": 3
}
```

### 调整提取敏感度

在代码中修改:

```python
from claude_memory.extractors.llm_extractor import LLMMemoryExtractor

# 更敏感的提取（更多记忆）
extractor = LLMMemoryExtractor()
# 修改 prompt 中的 importance 阈值...
```

### 记忆压缩

定期运行压缩（合并相似记忆）:

```bash
# 手动触发压缩
python -m claude_memory.scripts.compress --project my-project
```

---

## 故障排除

### 问题 1: 记忆没有自动提取

**检查**:
```bash
echo $CLAUDE_MEMORY_AUTO_EXTRACT  # 应为 true
echo $CLAUDE_MEMORY_LLM_PROVIDER   # 应为 glm/kimi/etc
echo $GLM_API_KEY                  # 或对应 key
```

**解决**:
```bash
export CLAUDE_MEMORY_AUTO_EXTRACT="true"
export CLAUDE_MEMORY_LLM_PROVIDER="glm"
export GLM_API_KEY="your-key"
```

### 问题 2: 记忆没有注入

**可能原因**:
- 检索阈值太高
- 没有相关记忆
- 自动注入被关闭

**解决**:
```bash
# 检查是否有记忆
claude-memory search "关键词"

# 手动测试注入
python -c "
from claude_memory import ACPMemoryAdapter
adapter = ACPMemoryAdapter()
memories = adapter.get_memory_context([{'role': 'user', 'content': '测试'}])
print(f'找到 {len(memories)} 条记忆')
"
```

### 问题 3: 不同项目记忆混淆

**检查项目 ID**:
```bash
echo $CLAUDE_MEMORY_PROJECT  # 当前项目
```

**解决**:
```bash
# 确保每个项目有唯一 ID
export CLAUDE_MEMORY_PROJECT="project-a-unique-id"
```

### 问题 4: 存储占用太大

**清理旧记忆**:
```bash
# 删除特定项目的记忆
rm -rf ~/.claude-memory/project-old-project

# 或全部重置
rm -rf ~/.claude-memory/
```

---

## 最佳实践

### 1. 项目命名

```bash
# 好的命名
export CLAUDE_MEMORY_PROJECT="company-crm-system"
export CLAUDE_MEMORY_PROJECT="personal-blog-2024"

# 避免
export CLAUDE_MEMORY_PROJECT="project"  # 太泛
export CLAUDE_MEMORY_PROJECT="test"     # 易冲突
```

### 2. 定期整理

```bash
# 每周查看一次记忆
claude-memory list-memories | head -20

# 删除过时记忆
claude-memory delete --id mem_old_id
```

### 3. 敏感信息

**注意**: 记忆会持久化存储，避免记录：
- 密码/API Key
- 个人隐私信息
- 机密商业信息

### 4. 多模型切换

```bash
# 创建 alias 快速切换
alias cm-glm='export CLAUDE_MEMORY_LLM_PROVIDER=glm && claude-code'
alias cm-kimi='export CLAUDE_MEMORY_LLM_PROVIDER=kimi && claude-code'
```

---

## 总结

Claude Memory 让 AI 真正"认识"你：

- ✅ 自动记住你的偏好和习惯
- ✅ 跨会话保持上下文
- ✅ 项目间完全隔离
- ✅ 支持国产大模型
- ✅ 100% 本地存储

**开始使用**: 配置好 API Key，和 Claude 对话，它会自动学习！
