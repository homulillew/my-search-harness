# my-search-harness

Search harness for automated research loops。

> **当前状态：初始化阶段（bootstrap）**

本项目正处于仓库初始化阶段。当前只建立了标准项目顶层结构，
**尚未实现任何 Harness 业务逻辑**（Research Loop、Retriever、Evidence、LLM Wiki 等均未开始设计）。

## 结构概览

```text
my-search-harness/
│
├── src/          # 正式产品源码
├── tests/        # 正式测试（含 fixtures）
├── docs/         # 长期项目文档
├── config/       # 正式产品静态配置
├── scripts/      # 开发与运行辅助脚本
├── examples/     # 可公开展示的正式示例
├── workspace/    # 程序运行生成的数据（默认不提交 Git）
└── .vibe/        # AI 辅助开发工作区（指导 ChatGPT / Claude Code）
```

## 安装与使用

暂时不可用 —— 项目仍处于初始化阶段，`pyproject.toml` 仅提供基础项目骨架。

## 开发协作

本项目采用 **ChatGPT Web + Claude Code + GitHub** 的协作开发方式，
具体流程见 [`.vibe/AI_WORKFLOW.md`](.vibe/AI_WORKFLOW.md) 与 [`.vibe/LEARNING_RULES.md`](.vibe/LEARNING_RULES.md)。
