# AI 协作开发工作流

本项目采用 **ChatGPT Web + Claude Code + GitHub** 的协作开发方式。

## 项目信息

- GitHub 仓库：`homulillew/my-search-harness`
- 仓库地址：`https://github.com/homulillew/my-search-harness.git`
- 主分支：`main`
- GitHub 是 ChatGPT 与 Claude Code 之间的 **唯一事实源（Source of Truth）**

Claude Code 在服务器上的本地修改，只有在 **commit + push 到 GitHub** 后，才视为已经正式交接给 ChatGPT。

---

## 角色分工

### ChatGPT Web：规划 + Review

ChatGPT 负责：

- 始终读取 `homulillew/my-search-harness` 的最新 GitHub 状态
- 理解当前代码、最近 commits、branch 和 PR
- 制定下一阶段开发计划
- Review Claude Code 的实际实现
- 检查 Bug、架构、安全、兼容性、测试和遗漏
- 给 Claude Code 生成下一轮明确、有限、可验证的任务

ChatGPT 原则：

1. 以 GitHub 最新代码为准，不假设服务器上未 push 的代码。
2. Review 时优先检查实际 diff / commit / PR，而不是只相信 Claude Code 的文字总结。
3. 一次只安排一个清晰阶段，避免同时扩大到大量无关任务。
4. 没有确认代码和测试情况前，不直接判断任务已经完成。
5. 默认不直接修改仓库代码，主要承担规划和审查角色。

---

### Claude Code：执行 + 测试

Claude Code 在服务器负责：

- 拉取 `homulillew/my-search-harness`
- 按 ChatGPT 的任务修改代码
- 运行测试、build、lint 和必要验证
- 修复执行过程中发现的问题
- commit 修改
- push 到 GitHub
- 创建或更新 feature branch / PR
- 报告本轮修改和测试结果

Claude Code 原则：

1. 开始任务前先确认当前 branch，并同步 GitHub 最新代码。
2. 不擅自扩大 ChatGPT 给出的任务范围。
3. 修改完成后必须运行相关测试。
4. 测试失败不能标记任务完成。
5. 完成后必须 commit + push，才能交给 ChatGPT Review。

---

## GitHub 分支规则

非常小、低风险的修改可以直接提交 `main`。

以下任务优先使用独立 branch：

- 新功能
- 重构
- 多文件 Bug 修复
- 数据库修改
- 登录 / 权限 / 安全
- 支付
- API 大改
- 较大的依赖升级
- Claude Code 需要连续完成多个修改步骤

分支命名示例：

```text
feature/search-ranking
feature/new-provider
fix/search-timeout
fix/parser-error
refactor/search-pipeline
```

Claude Code 创建分支示例：

```bash
git checkout main
git pull origin main
git checkout -b feature/xxx
```

完成后：

```bash
git add .
git commit -m "feat: ..."
git push -u origin feature/xxx
```

然后创建 PR：

```text
feature/xxx
    ↓
Pull Request
    ↓
main
```

---

## 标准开发循环

```text
ChatGPT
读取 my-search-harness 最新 GitHub
        ↓
分析现状 + 制定下一阶段任务
        ↓
Claude Code
同步 main / 创建 feature branch
        ↓
修改代码
        ↓
测试 / build / lint
        ↓
commit + push
        ↓
创建或更新 PR
        ↓
ChatGPT
读取最新 PR / commits / diff
        ↓
Review
   ↙         ↘
有问题       通过
  ↓           ↓
Claude修复    Merge PR
  ↓           ↓
再次 push    main 更新
  ↓           ↓
ChatGPT 再读取最新 GitHub
        ↓
规划下一轮
```

核心循环：

> **规划 → 执行 → 测试 → Push → Review → 修复/合并 → 下一轮规划**

---

## 给 ChatGPT 的标准指令

### 开始规划

> 读取 GitHub 仓库 `homulillew/my-search-harness` 的最新状态，包括 main、最近 commits，以及相关 branch / PR。  
> 先确认项目当前实际状态，再制定下一阶段计划。  
> 计划必须明确、有限、可验证，并能够直接交给 Claude Code 执行。  
> 不要一次安排大量无关任务。

### Claude Code 完成一轮后

> Claude Code 已完成本轮任务并 push 到 GitHub。  
> 请读取 `homulillew/my-search-harness` 的最新 branch / PR / commits，并与 main 对比。  
> Review 实际代码修改，重点检查：
> - 是否真正完成目标
> - Bug 和边界条件
> - 架构
> - 安全
> - API / 数据兼容性
> - 测试覆盖
> - 重复实现
> - 是否混入无关修改
>
> 如果有问题，生成一份可直接交给 Claude Code 的修复任务。  
> 如果没有明显问题，说明是否可以 merge，并规划下一步。

---

## 给 Claude Code 的标准指令

### 开始执行

> 当前项目 GitHub 仓库：
> `https://github.com/homulillew/my-search-harness.git`
>
> 先确认当前 branch，并同步 GitHub 最新代码。  
> 阅读 ChatGPT 给出的本轮任务，只完成任务要求的范围，不擅自扩大修改。
>
> 完成后：
> 1. 运行相关测试
> 2. 运行必要的 build / lint
> 3. 修复发现的问题
> 4. commit
> 5. push 到 GitHub
> 6. 如果使用 feature branch，创建或更新 PR
>
> 最后报告：
> - 修改了什么
> - 修改了哪些关键文件
> - 测试结果
> - branch
> - commit SHA
> - PR（如果有）
> - 尚未解决的问题

### 使用 feature branch 时

> 不要直接修改 main。  
> 基于最新 main 创建或更新当前 feature / fix / refactor branch。  
> 完成、测试并 push 后等待 ChatGPT Review。  
> Review 发现问题时，继续在同一个 branch 修复并再次 push。

---

## ChatGPT PR Review 标准

每次 Review 至少检查：

1. 是否真正完成本轮目标
2. 是否存在明显 Bug
3. 是否遗漏边界条件
4. 是否破坏已有功能
5. 架构是否合理
6. 是否产生不必要复杂度
7. 是否存在重复实现
8. 是否存在安全风险
9. API / 数据库是否兼容
10. 测试是否覆盖关键路径
11. 是否包含与本任务无关的大量修改
12. 是否适合 merge 到 `main`

---

## Commit 原则

一个 commit 尽量对应一个清晰逻辑变化。

推荐：

```text
feat(search): add result ranking
fix(search): handle provider timeout
test(search): add ranking integration tests
refactor(search): extract provider adapter
```

避免：

```text
update
fix
changes
test
final
```

---

## 最终原则

> **ChatGPT 负责想清楚、检查清楚、安排下一步。**

> **Claude Code 负责实际修改、运行验证、提交结果。**

> **GitHub `homulillew/my-search-harness` 保存双方共同认可的真实项目状态。**

任何需要 ChatGPT 正式 Review 的修改，都应先由 Claude Code：

**测试 → commit → push → PR（适用时）**

之后再交给 ChatGPT。
