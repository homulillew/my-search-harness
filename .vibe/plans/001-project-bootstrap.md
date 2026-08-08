# Repository Structure Design

## 1. 目的

当前仓库处于项目初始化阶段。

这一阶段暂时**不设计具体的 Search Harness、Research Loop、LLM Wiki、Evidence、Provider 等业务实现**，只先建立清晰、稳定的仓库边界，为后续开发提供统一的目录约定。

本次目录整理主要解决两个问题：

1. **正式项目文件**与**用于指导 AI/Vibe Coding 的开发文件**必须分离。
2. 仓库从一开始保持标准、易理解的工程结构，避免后续随着开发不断在根目录堆积脚本、Prompt、临时设计稿和运行产物。

本阶段原则：

> 先划分空间和职责，不提前设计尚未实现的业务模块。

---

# 2. 总体目录设计

整理后的仓库建议保持以下高层结构：

```text
my-search-harness/
│
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── .env.example
├── CLAUDE.md
│
├── src/
│
├── tests/
│
├── docs/
│
├── config/
│
├── scripts/
│
├── examples/
│
├── workspace/
│
└── .vibe/
```

现阶段不需要为了“目录完整”而在每个目录中创建大量占位文件。

如果 Git 无法追踪空目录，可以只在确实需要保留的空目录中添加 `.gitkeep` 或简短 `README.md`。

---

# 3. 四类文件必须明确分开

整个仓库中的文件原则上只能属于以下四类之一。

```text
                     Repository
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼

   Product Code      Project Docs      Vibe Guidance
        │                │                │
   src / tests          docs             .vibe
   config/scripts
        │
        ▼
 Runtime Artifacts
     workspace
```

判断一个文件应该放在哪里时，依次问：

### 这是产品运行所需要的文件吗？

放到：

```text
src/
config/
scripts/
```

### 这是测试或正式示例吗？

放到：

```text
tests/
examples/
```

### 这是长期解释项目本身的文档吗？

放到：

```text
docs/
```

### 这是为了指导 ChatGPT / Claude Code 开发这个项目吗？

放到：

```text
.vibe/
```

### 这是程序运行过程中生成的数据吗？

放到：

```text
workspace/
```

---

# 4. 根目录

根目录只保留项目级入口文件。

目标是让第一次打开 GitHub 仓库的人能够快速判断：

* 这是什么项目；
* 如何安装；
* 如何运行；
* 使用什么语言和依赖；
* 去哪里看文档；
* 去哪里看源码。

建议最终根目录保持：

```text
README.md
LICENSE
pyproject.toml
.gitignore
.env.example
CLAUDE.md
```

避免以后在根目录出现：

```text
plan_new.md
prompt_v2.md
todo-final.md
architecture-new-final.md
debug_notes.md
claude_task.md
test_script_tmp.py
...
```

这些文件必须根据性质进入对应目录。

---

# 5. `src/` —— 正式产品源码

```text
src/
└── my_search_harness/
    └── __init__.py
```

现阶段只创建 Python package 骨架即可。

暂时不要提前创建：

```text
agent/
planner/
retriever/
wiki/
loop/
evidence/
provider/
...
```

这些目录应该等对应架构真正确定并开始实现后再创建。

## 为什么这样设计

`src` layout 是标准 Python 项目结构，可以避免：

* 测试时意外 import 当前工作目录；
* 项目根目录和 Python package 混在一起；
* 后期 packaging 时重新调整目录。

原则：

> `src/` 中的每一个模块都应该对应已经真实存在的产品职责。

不要为了“看起来架构完整”提前创建空模块。

---

# 6. `tests/` —— 正式测试

```text
tests/
├── fixtures/
└── ...
```

这里未来存放：

* unit tests；
* integration tests；
* regression tests；
* 测试 fixture。

测试代码不进入 `src/`。

开发过程中的一次性验证脚本也不要随意扔进这里。

判断标准：

> 如果这个测试值得在未来 CI 中重复运行，它才属于 `tests/`。

---

# 7. `docs/` —— 正式项目文档

```text
docs/
├── architecture/
├── development/
└── evaluation/
```

现阶段可以只创建 `docs/`，子目录在实际有文档后再建立。

这里存放的是：

> 即使未来 `.vibe/` 整个删除，这些文档仍然值得随产品长期存在。

例如未来可能包括：

```text
docs/
├── ARCHITECTURE.md
├── DESIGN_DECISIONS.md
├── DEVELOPMENT.md
├── RESEARCH_METHODOLOGY.md
└── EVALUATION.md
```

但本阶段不要提前编写 Harness 相关内容。

## `docs/` 和 `.vibe/` 的区别

### `docs/`

解释：

> 产品为什么这样设计？

读者：

* 开源用户；
* 未来维护者；
* 面试官；
* 项目贡献者。

### `.vibe/`

解释：

> 我们现在应该怎样把这个产品开发出来？

读者：

* ChatGPT；
* Claude Code；
* 当前项目开发者。

这是两个不同层次。

---

# 8. `.vibe/` —— AI/Vibe Coding 开发工作区

这是当前最重要的目录划分。

```text
.vibe/
├── README.md
│
├── AI_WORKFLOW.md
├── LEARNING_RULES.md
│
├── context/
├── plans/
├── tasks/
├── reviews/
└── archive/
```

`.vibe/` 中的文件**不属于最终产品运行逻辑**。

它们的作用是：

* 给 Claude Code 提供开发约束；
* 保存 ChatGPT 与 Claude Code 的协作规则；
* 保存阶段计划；
* 保存单次开发任务；
* 保存 Review 结论；
* 保存阶段性背景；
* 防止这些临时开发知识污染正式代码和正式文档。

一个重要的判断标准是：

> 理论上未来删除整个 `.vibe/` 后，产品本身仍然应该能够正常安装、测试和运行。

---

# 9. 当前两个文件的迁移

当前仓库已有：

```text
AI_WORKFLOW.md
CLAUDE_learning_focused.md
```

建议移动并重命名为：

```text
.vibe/
├── AI_WORKFLOW.md
└── LEARNING_RULES.md
```

## `AI_WORKFLOW.md`

当前文件已经定义：

* ChatGPT Web 的职责；
* Claude Code 的职责；
* GitHub Source of Truth；
* branch / PR 规则；
* 开发循环；
* Review 标准；
* commit 原则。

这些属于：

> AI 协作开发流程

因此应该进入 `.vibe/`，而不是长期占据项目根目录。

内容暂时不需要大改。

---

## `LEARNING_RULES.md`

将：

```text
CLAUDE_learning_focused.md
```

重命名为：

```text
.vibe/LEARNING_RULES.md
```

它主要描述：

* 开发前先建立设计模型；
* 解释 Decision / Alternatives / Trade-offs；
* 一个模块一个模块开发；
* 完成模块后进行 Module Walkthrough；
* 帮助开发者建立 mental model；
* 记录重要 Debug 发现；
* 维护 Decision Log。

这些也是：

> Claude Code 如何帮助开发这个项目

而不是：

> 最终产品如何运行。

所以同样属于 `.vibe/`。

---

# 10. `.vibe/context/`

```text
.vibe/context/
```

以后存放跨 session 仍然需要保留的项目开发背景。

例如：

```text
PROJECT_CONTEXT.md
CURRENT_STATE.md
```

用途是解决：

> Claude Code 或 ChatGPT 开启新 session 后如何快速恢复开发上下文？

这里应该保存高层背景，而不是整个聊天记录。

典型内容：

```text
当前项目目标
当前阶段
已经确定的重要原则
当前已经实现的模块
明确暂缓的内容
最近的重要架构变化
```

---

# 11. `.vibe/plans/`

```text
.vibe/plans/
```

存放阶段性开发计划。

例如：

```text
001-project-bootstrap.md
002-core-architecture.md
003-search-loop.md
```

Plan 描述的是一个阶段。

它回答：

```text
这一阶段为什么做？
↓
准备完成哪些事情？
↓
大致按什么顺序？
↓
完成以后系统应该达到什么状态？
```

Plan 不应该包含大量具体代码修改指令。

---

# 12. `.vibe/tasks/`

```text
.vibe/tasks/
```

存放可以直接交给 Claude Code 执行的有限任务。

建议命名：

```text
001-bootstrap-repository.md
002-setup-python-project.md
003-xxx.md
```

每个 Task 应尽量包含：

```text
Goal

Why

Scope

Non-goals

Files allowed to change

Acceptance criteria

Required validation
```

原则：

> 一个 task 应该能够在完成后被独立 Review。

避免一次 Task 同时要求：

```text
设计架构
实现搜索
实现 Wiki
实现报告
写测试
改 README
做优化
```

---

# 13. `.vibe/reviews/`

```text
.vibe/reviews/
```

存放 ChatGPT 对已完成阶段的重要 Review 结论。

例如：

```text
001-bootstrap-review.md
002-state-model-review.md
```

不是每一个小 commit 都必须创建 review 文件。

只记录值得长期保留到本次开发过程结束的重要 Review：

* 实现是否符合原设计；
* 是否出现架构膨胀；
* 是否发现错误假设；
* 是否需要返工；
* 是否需要修改后续计划。

---

# 14. `.vibe/archive/`

```text
.vibe/archive/
```

用于保存已经失效、但暂时不想删除的：

* old plan；
* old task；
* migration notes；
* 已完成阶段的临时材料。

原则：

> 当前有效指导不要和历史指导混在一起。

Claude Code 默认不应该读取 `archive/` 来决定当前应该怎么实现。

---

# 15. `.vibe/README.md`

需要创建一个很短的入口文件，说明：

```text
.vibe/ 是本项目的 AI-assisted development workspace。

这里的文件用于指导 ChatGPT / Claude Code 开发项目，
不属于产品 runtime。

目录：

AI_WORKFLOW.md
    AI 协作和 GitHub 工作流。

LEARNING_RULES.md
    Claude Code 的学习型开发与模块讲解规则。

context/
    当前项目开发背景。

plans/
    阶段计划。

tasks/
    可以直接执行的有限开发任务。

reviews/
    重要阶段 Review。

archive/
    已失效的开发材料。
```

---

# 16. 根目录 `CLAUDE.md`

建议创建一个非常短的：

```text
CLAUDE.md
```

但它只作为 **Router**。

不要把现有 `LEARNING_RULES.md` 的全部内容复制进来。

建议内容类似：

```markdown
# Claude Code Development Entry

Before making repository changes, read:

1. `.vibe/AI_WORKFLOW.md`
2. `.vibe/LEARNING_RULES.md`

If a task file is provided, read the relevant file under:

`.vibe/tasks/`

For current project context, read only the relevant files under:

`.vibe/context/`

Do not treat `.vibe/archive/` as active instructions.

Keep product code, project documentation, runtime artifacts,
and AI-development guidance separated according to the repository structure.
```

## 为什么只做 Router

因为 Claude Code 会自动读取根目录 `CLAUDE.md`。

如果以后不断把规则追加进去，很容易再次发展成：

```text
一个几百行甚至上千行的超级 Prompt
```

因此：

> 根 `CLAUDE.md` 负责告诉 Claude “应该去哪读”，而不是保存所有规则。

---

# 17. `config/`

```text
config/
```

未来保存正式产品的静态配置。

例如：

```text
default.yaml
```

但当前阶段可以保持为空，暂时不要设计 Harness 配置项。

开发 AI 自身的指导配置不能放这里。

---

# 18. `scripts/`

```text
scripts/
```

未来保存正式开发和运行辅助脚本，例如：

```text
bootstrap.sh
bootstrap.ps1
```

判断标准：

> 一个新开发者 clone 项目后，是否可能合理地执行这个脚本？

如果答案是“只是 Claude Code 今天临时需要”，则不应进入 `scripts/`。

---

# 19. `examples/`

```text
examples/
```

未来用于保存可以公开展示的正式产品示例。

它不是：

```text
tests/fixtures/
```

也不是：

```text
workspace/
```

区别：

### tests/fixtures

机器测试数据。

### examples

给人看的完整使用示例。

### workspace

真实运行生成的数据。

---

# 20. `workspace/`

```text
workspace/
```

统一存放未来程序运行生成的本地数据。

现阶段只建立边界，不设计内部 Harness 目录。

它未来可能产生：

```text
runs/
wiki/
reports/
cache/
```

但现在不要提前创建。

建议：

```text
workspace/*
```

默认加入 `.gitignore`。

如需要保留目录，可以提交：

```text
workspace/.gitkeep
```

或者：

```text
workspace/README.md
```

---

# 21. `workspace/` 为什么必须独立

不要让未来生成的数据散落到：

```text
src/
docs/
项目根目录
```

否则很快会出现：

```text
report-final.md
run-002.json
papers-cache.json
wiki-test/
debug-output/
...
```

并逐渐无法区分：

* 哪些是代码；
* 哪些是测试资源；
* 哪些是用户数据；
* 哪些应该提交 Git。

因此从第一天开始规定：

> Runtime output only goes to `workspace/`.

---

# 22. 推荐的初始整理结果

本轮 Claude Code 完成后，仓库建议至少达到：

```text
my-search-harness/
│
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── .env.example
├── CLAUDE.md
│
├── src/
│   └── my_search_harness/
│       └── __init__.py
│
├── tests/
│   └── fixtures/
│
├── docs/
│
├── config/
│
├── scripts/
│
├── examples/
│
├── workspace/
│
└── .vibe/
    ├── README.md
    ├── AI_WORKFLOW.md
    ├── LEARNING_RULES.md
    │
    ├── context/
    ├── plans/
    ├── tasks/
    ├── reviews/
    └── archive/
```

如果某些空目录没有实际内容，可以不提交。

**目录本身不是目标，清晰的职责边界才是目标。**

---

# 23. 本轮明确不做

这次仓库整理不要开始设计或实现：

```text
Research Loop
Agent Search
Planner
Retriever
Evidence
Research State
Loop Engineering
LLM Wiki
Report Pipeline
DeepXiv Provider
Citation Graph
Multi-Agent
```

不要因为知道后续大概率需要这些模块，就提前创建对应 Python package。

这些内容应该在后续架构设计正式落地时再逐步加入。

---

# 24. 本轮允许做的事情

本轮 Claude Code 只需要：

1. 创建标准项目顶层结构。
2. 将现有 AI 开发指导文件迁移进 `.vibe/`。
3. 将 `CLAUDE_learning_focused.md` 重命名为 `.vibe/LEARNING_RULES.md`。
4. 创建简洁的 `.vibe/README.md`。
5. 创建简洁的根目录 `CLAUDE.md` Router。
6. 建立最小 Python `src` layout。
7. 创建基础 `pyproject.toml`。
8. 创建合理的 `.gitignore`。
9. 创建 `.env.example`，暂时不写具体服务密钥。
10. 创建最小 `README.md`，只描述项目当前仍处于初始化阶段。
11. 不实现任何 Harness 业务逻辑。
12. 不添加未经需求证明的第三方依赖。

---

# 25. 本轮 Acceptance Criteria

整理完成后应满足：

### Repository boundary

根目录没有散落的 Vibe Coding 指导文档。

### AI guidance

所有开发指导主要集中在：

```text
.vibe/
```

根 `CLAUDE.md` 只是入口，不是大型规则文件。

### Python project

存在标准：

```text
src/my_search_harness/
tests/
pyproject.toml
```

结构。

### Runtime boundary

存在明确的：

```text
workspace/
```

运行产物边界，并默认不提交其内容。

### No premature architecture

不存在为了未来 Harness 实现提前创建的大量空业务模块。

### No unnecessary dependencies

项目初始化阶段不引入 Agent Framework、数据库、Web Framework 等依赖。

---

# 26. 当前阶段最重要的原则

这次整理只建立：

> **Repository Architecture**

不是：

> **Application Architecture**

当前我们需要稳定的只是这些边界：

```text
Product
    src / config / scripts

Tests
    tests

Long-lived Documentation
    docs

AI-assisted Development
    .vibe

Runtime Data
    workspace

Public Demonstrations
    examples
```

业务内部如何拆分，应由后续正式架构设计决定。

---

# 27. 最终设计原则

## Rule 1

**根目录保持克制。**

## Rule 2

**正式产品和开发 AI 指导彻底分离。**

## Rule 3

**长期设计文档和临时施工计划彻底分离。**

## Rule 4

**运行产物永远不污染源码目录。**

## Rule 5

**不存在的业务抽象，不提前创建目录。**

## Rule 6

**目录数量不是工程质量，明确的 Ownership 才是。**

这一轮完成后的理想状态不是“仓库看起来很大”，而是：

> 每当产生一个新文件时，我们都能非常明确地回答它为什么属于这个位置。
