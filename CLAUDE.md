# Codex 开发入口

本文件只作为 Router，告诉 Codex **应该去哪读**，不保存具体规则。

在修改仓库前，请先阅读：

1. `.vibe/AI_WORKFLOW.md` — AI 协作与 GitHub 工作流
2. `.vibe/LEARNING_RULES.md` — 学习型开发与模块讲解规则

如果提供了任务文件，请阅读 `.vibe/tasks/` 下对应文件。

当前项目背景，请按需阅读 `.vibe/context/` 下对应文件。

不要将 `.vibe/archive/` 视为有效指令。

保持产品代码、项目文档、运行产物与 AI 开发指导相互分离，符合仓库结构约定。

## 推送要求（强制）

所有更改都必须推送到 GitHub 仓库，不得只留在本地。

- 任何代码、文档、运行产物、验收快照的修改，完成后必须 `commit` + `push` 到 `origin`。
- GitHub 是唯一事实源（Source of Truth）：本地未 push 的修改视为未完成，不计入交接。
- 推送前必须检查 diff，确认不包含密钥、token、凭据等敏感信息（参见 `.vibe/AI_WORKFLOW.md` 的安全要求）。
- 运行产物（如 `workspace_e2e_rc/`、`live-acceptance/`）同样需要推送，确保协作者拉取后可审阅完整状态。
- 若发现推送内容含敏感信息，必须立即从仓库历史中清除并轮换泄露的凭据。

执行流程：**修改 → 检查 diff（无敏感信息）→ commit → push → 报告 commit SHA**
