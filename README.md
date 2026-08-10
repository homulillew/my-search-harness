# my-search-harness

Search harness for controlled, recoverable academic research loops.

> **当前状态：V1 runtime implemented**

V1 已实现 Frozen Architecture / Domain Model 所定义的核心能力：权威
`ResearchRun`、DeepXiv 论文搜索与来源读取、生命周期感知 Context、fresh
Completion Checker、Report / citation pipeline、append-only audit，以及可重建
Local Wiki。语义研究、完成判断和写作仍由注入的 semantic actor 负责；Python
runtime 只执行权限、引用、持久化、资源、provenance 和确定性验证。

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
└── .vibe/        # AI 开发规则、Review 记录与项目记忆
```

## 安装

```bash
python -m pip install -e .
```

生产外部 I/O 只从环境变量读取 DeepXiv credential：

```bash
export DEEPXIV_TOKEN=...
```

最小本地 composition root：

```python
from my_search_harness.runtime import LocalV1Runtime

runtime = LocalV1Runtime.from_deepxiv_env("workspace")
researcher = runtime.researcher
completion = runtime.completion
delivery = runtime.delivery
```

`researcher`、`completion_checker` 和 `delivery` 是分离的 capability surface。
底层 Repository、ArtifactStore 与任意 JSON mutation 不通过该入口公开。Report
和 Wiki 的语义阶段通过对应 Protocol 注入，确定性完整示例见
[`tests/test_end_to_end.py`](tests/test_end_to_end.py)。

正式 Report Pipeline 由调用方显式指定权威写作指南路径：

```python
pipeline = runtime.report_pipeline(
    planner=planner,
    composer=composer,
    integrator=integrator,
    editor_factory=editor_factory,
    reviser=reviser,
    integrity_reviewer=integrity_reviewer,
    writing_guideline_path=".vibe/REPORT_WRITING_GUIDE.md",
)
```

Runtime 以 UTF-8 原样加载该文件，不依赖当前工作目录自动发现，也不复制指南内容。

## 验证

```bash
PYTHONPATH=src python -m unittest discover -s tests
python -m mypy src tests
python -m black --check src tests
git diff --check
```

## 开发协作

项目 AI 协作与学习规则见 [`.vibe/AI_WORKFLOW.md`](.vibe/AI_WORKFLOW.md) 与
[`.vibe/LEARNING_RULES.md`](.vibe/LEARNING_RULES.md)。Frozen authority 位于
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)、
[`docs/DOMAIN_MODEL.md`](docs/DOMAIN_MODEL.md) 与 `docs/adr/`。
