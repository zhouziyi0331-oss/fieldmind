# LLM 提供商配置指南

## 🎯 快速开始

FieldMind 现在支持 4 个主流 LLM 提供商，您可以根据需求自主选择配置：

- **OpenAI (GPT)** - 国际领先，功能强大
- **Anthropic (Claude)** - 长文本处理，推理能力强
- **DeepSeek（深度求索）** - 国产，性价比极高
- **Kimi（月之暗面）** - 国产，超长上下文

> **提示**：您不需要配置所有提供商，只配置您想用的即可！

---

## 📋 配置步骤

### 1. 复制配置模板

```bash
cd /Users/alwan/FieldMind/backend
cp .env.llm.example .env.llm
```

### 2. 编辑配置文件

```bash
vim .env.llm
# 或使用您喜欢的编辑器
```

### 3. 将配置合并到主 .env 文件

```bash
cat .env.llm >> .env
```

---

## 🔑 获取 API Keys

### OpenAI

**官网**: https://platform.openai.com/

**步骤**:
1. 注册/登录 OpenAI 账号
2. 访问 https://platform.openai.com/api-keys
3. 点击 "Create new secret key"
4. 复制 API Key（格式：`sk-proj-...`）

**配置**:
```bash
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_DEFAULT_MODEL=gpt-4o-mini
```

**推荐模型**:
- `gpt-4o-mini` - 性价比最高 ⭐
- `gpt-4o` - 最新最强
- `gpt-3.5-turbo` - 快速便宜

**成本参考**:
- GPT-4o-mini: $0.15 / 1M input tokens
- GPT-4o: $5 / 1M input tokens

---

### Anthropic (Claude)

**官网**: https://console.anthropic.com/

**步骤**:
1. 访问 https://console.anthropic.com/
2. 注册账号并完成验证
3. 进入 API Keys 页面
4. 创建新的 API Key（格式：`sk-ant-...`）

**配置**:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_DEFAULT_MODEL=claude-3-5-sonnet-20241022
```

**推荐模型**:
- `claude-3-5-sonnet-20241022` - 最新最强 ⭐
- `claude-3-haiku-20240307` - 快速便宜
- `claude-3-opus-20240229` - 最高性能

**成本参考**:
- Claude 3.5 Sonnet: $3 / 1M input tokens
- Claude 3 Haiku: $0.25 / 1M input tokens

**特点**:
- 支持 200K 超长上下文
- 推理能力强
- 适合复杂任务

---

### DeepSeek（深度求索）⭐ 推荐国产

**官网**: https://platform.deepseek.com/

**步骤**:
1. 访问 https://platform.deepseek.com/
2. 微信扫码注册（支持手机号）
3. 进入控制台 -> API Keys
4. 创建新的 API Key

**配置**:
```bash
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_DEFAULT_MODEL=deepseek-chat
```

**推荐模型**:
- `deepseek-chat` - 通用对话 ⭐
- `deepseek-coder` - 代码专家

**成本参考**:
- DeepSeek Chat: $0.1 / 1M tokens（输入输出同价）
- **比 GPT-4o-mini 便宜 15 倍！**

**特点**:
- 🇨🇳 国产大模型，中文友好
- 💰 性价比极高
- ⚡ 响应速度快
- 🔧 代码能力出色

**推荐理由**:
- 日常使用首选
- 成本几乎可以忽略
- 质量接近 GPT-3.5-turbo

---

### Kimi（月之暗面）⭐ 推荐国产

**官网**: https://platform.moonshot.cn/

**步骤**:
1. 访问 https://platform.moonshot.cn/
2. 注册账号（支持手机号）
3. 进入 https://platform.moonshot.cn/console/api-keys
4. 创建新的 API Key

**配置**:
```bash
KIMI_API_KEY=sk-your-key-here
KIMI_DEFAULT_MODEL=moonshot-v1-8k
```

**推荐模型**:
- `moonshot-v1-8k` - 标准版 ⭐
- `moonshot-v1-32k` - 长文本
- `moonshot-v1-128k` - 超长文本

**成本参考**:
- 8K: $1.2 / 1M tokens
- 32K: $2.4 / 1M tokens
- 128K: $6 / 1M tokens

**特点**:
- 🇨🇳 国产大模型
- 📚 支持最长 128K 上下文
- 🎯 中文优化
- 📖 适合长文本分析

**推荐理由**:
- 处理长文档首选
- 价格合理
- 中文理解深刻

---

## 🎨 配置示例

### 最小配置（只用 DeepSeek）

```bash
# 只配置 DeepSeek，成本最低
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_DEFAULT_MODEL=deepseek-chat
P3_ROUTING_STRATEGY=cost_optimized
```

### 推荐配置（国产 + 进口）

```bash
# DeepSeek 处理日常任务
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_DEFAULT_MODEL=deepseek-chat

# GPT-4o-mini 处理复杂任务
OPENAI_API_KEY=sk-proj-...
OPENAI_DEFAULT_MODEL=gpt-4o-mini

# 路由策略
P3_ROUTING_STRATEGY=balanced
P3_PROVIDER_PRIORITY=deepseek,openai
```

### 完整配置（所有提供商）

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_DEFAULT_MODEL=gpt-4o-mini

# Claude
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_DEFAULT_MODEL=claude-3-5-sonnet-20241022

# DeepSeek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_DEFAULT_MODEL=deepseek-chat

# Kimi
KIMI_API_KEY=sk-...
KIMI_DEFAULT_MODEL=moonshot-v1-8k

# 路由策略
P3_ROUTING_STRATEGY=balanced
P3_PROVIDER_PRIORITY=deepseek,kimi,openai,anthropic
P3_AUTO_ROUTING=true
P3_MONTHLY_BUDGET=100
```

---

## 🚀 启动 FieldMind

配置完成后，重启 FieldMind：

```bash
cd /Users/alwan/FieldMind/backend/src
pkill -f "uvicorn.*8013"
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8013 --reload
```

---

## ✅ 验证配置

### 方法 1: 命令行测试

```bash
# 查看可用提供商
curl http://localhost:8013/api/llm-providers/

# 测试 DeepSeek
curl -X POST http://localhost:8013/api/llm-providers/test/deepseek

# 测试 OpenAI
curl -X POST http://localhost:8013/api/llm-providers/test/openai
```

### 方法 2: API 文档测试

访问: http://localhost:8013/docs

找到 `/llm-providers/` 接口，查看配置的提供商列表

---

## 📊 路由策略说明

### cost_optimized（成本优化）

- 简单任务 → DeepSeek/Kimi
- 中等任务 → GPT-4o-mini
- 复杂任务 → Claude Sonnet

**适合**: 日常使用，控制成本

### performance_optimized（性能优先）

- 简单任务 → GPT-4o-mini
- 中等任务 → Claude Sonnet
- 复杂任务 → GPT-4/Claude Opus

**适合**: 追求质量，不在意成本

### balanced（平衡）⭐ 推荐

- 简单任务 → DeepSeek
- 中等任务 → GPT-4o-mini/Kimi
- 复杂任务 → Claude Sonnet/GPT-4o

**适合**: 大多数场景

---

## 💡 使用建议

### 成本最优组合

```
DeepSeek (日常) + GPT-4o-mini (备用)
月成本: < $5
```

### 质量最优组合

```
Claude 3.5 Sonnet (主力) + GPT-4o (备用)
月成本: $20-50
```

### 均衡组合 ⭐

```
DeepSeek (简单) + Kimi (长文本) + Claude Sonnet (复杂)
月成本: $10-20
```

---

## 🔒 安全提示

1. **不要提交 API Keys 到 Git**
   ```bash
   # .gitignore 中已包含
   .env
   .env.llm
   ```

2. **定期更换 API Keys**
   - 建议每 3-6 个月更换一次

3. **设置使用限额**
   ```bash
   P3_MONTHLY_BUDGET=100  # 美元
   ```

4. **监控使用情况**
   - 访问各提供商的控制台查看用量
   - 使用 FieldMind 的统计 API

---

## ❓ 常见问题

### Q: 必须配置所有提供商吗？

**A**: 不需要！只配置您想用的即可。推荐至少配置 DeepSeek（成本最低）。

### Q: 哪个提供商最便宜？

**A**: DeepSeek，比 GPT-4o-mini 便宜 15 倍，比 GPT-4 便宜 300 倍。

### Q: 哪个提供商中文最好？

**A**: DeepSeek 和 Kimi 都是国产模型，中文理解都很好。Claude 的中文也不错。

### Q: 如何切换默认提供商？

**A**: 修改 `P3_PROVIDER_PRIORITY` 的顺序即可。

### Q: API Key 安全吗？

**A**: 本地存储在 `.env` 文件中，不会上传到服务器。但请确保不要提交到 Git。

### Q: 如何估算成本？

**A**: 
- 日常聊天（50K tokens/月）: DeepSeek < $0.01
- 代码分析（200K tokens/月）: GPT-4o-mini ~$0.15
- 长文本处理（500K tokens/月）: Kimi ~$0.6

---

## 📞 获取帮助

- DeepSeek 文档: https://platform.deepseek.com/docs
- Kimi 文档: https://platform.moonshot.cn/docs
- OpenAI 文档: https://platform.openai.com/docs
- Anthropic 文档: https://docs.anthropic.com/

---

**享受智能 LLM 路由带来的高效体验！** 🚀
