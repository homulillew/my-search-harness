# Harness 目标与核心原则

## 1. 我们要做什么

本项目要构建一个面向 **Claude Code** 的论文调研 Harness。

它的目标不是单纯让 Claude：

> 搜更多论文、读更多内容、生成更长的报告。

真正要解决的是：

> **如何让一个开放式、长时间运行的论文调研过程变得可恢复、可验证、可控制、可积累。**

用户给出一个研究主题后，Claude Code 仍然按照研究最自然的方式工作：

```text
理解问题
→ 改写 Query
→ 搜索论文
→ 筛选论文
→ 阅读
→ 提取和分析 Evidence
→ 形成技术路线理解
→ 发现 Research Gap
→ 再搜索
→ 再验证
→ 最终综合
```

Harness 不应该把这个过程强行改造成一条复杂的固定 Pipeline。

它应该做的是：

> **给 Claude 的研究行为提供一个可靠的工程环境。**

---

# 2. 核心定位

整个系统最重要的分工是：

```text
Claude Code
=
Research Agent / Semantic Policy

Python Harness
=
Research Runtime / Deterministic Mechanism
```

Claude 负责：

```text
研究问题理解
Query Rewrite
论文相关性判断
阅读选择
Evidence Interpretation
技术路线分析
矛盾分析
Research Gap 发现
最终综合
```

Python 负责：

```text
Search / Read 的可靠执行
状态持久化
ID 与去重
Budget
Retry / Timeout
Schema Validation
Evidence Integrity
State Transition
Resume
Context Rendering
Review Gate 的机械约束
```

一句话：

> **Claude 决定下一步研究什么，Harness 保证这一步被可靠执行和记录。**

---

# 3. Simple Loop

研究循环本身应该保持简单。

我们不希望每出现一种能力，就增加一个 Lifecycle Phase。

例如：

```text
search
read
follow citation
compare
extract evidence
```

这些都是 Research Action。

它们不应该自动变成：

```text
SEARCH_PHASE
READ_PHASE
CITATION_PHASE
COMPARE_PHASE
...
```

因此一个重要原则是：

> **Phase 描述研究生命周期，Action 描述具体工作。**

研究行为可以丰富，但控制流应该克制。

---

# 4. Rich State

简单的 Loop 不代表简单的 Research State。

真正复杂的信息应该被保存为显式状态，例如：

```text
Research Questions
Query History
Paper Candidates
Selected Papers
Evidence
Technical Routes
Research Gaps
Contradictions
Budget
Review State
```

这些状态不能只存在于 Claude 当前 Conversation 中。

因为：

> **Conversation 可以消失，但 Research State 不能消失。**

Session 重启以后，我们恢复的不是 Claude 当时说过的所有话，而是：

> **恢复研究已经进行到了哪里。**

---

# 5. Context Is a View of State

State 外置以后，也不能每轮重新把整个 State 塞回 Claude Context。

正确关系应该是：

```text
Persistent Research State
        ↓
Context Renderer
        ↓
当前 Action 所需的 bounded slice
        ↓
Claude Code
```

例如：

搜索决策需要看到：

```text
当前 Research Gaps
过去 Query
搜索覆盖情况
Budget
```

Evidence 分析需要看到：

```text
当前 Paper
相关原文
已有 Evidence
相关 Claim / Gap
```

Review 又需要另一种 View。

因此：

> **State 可以丰富，Context 必须有选择。**

---

# 6. Paper Is Not Evidence

搜索到一篇相关论文，并不代表我们已经拥有 Evidence。

至少应该保持这样的语义边界：

```text
Paper discovered
      ↓
Paper selected
      ↓
Paper read
      ↓
Relevant source passage found
      ↓
Evidence interpreted
```

最终允许进入研究结论的，不应该只是：

> “这篇论文好像讲过这个。”

而应该能够追踪：

```text
Claim
↓
Evidence
↓
Paper
↓
Section / Locator
↓
Source Passage
```

因此：

> **论文是 Evidence 的来源，不是 Evidence 本身。**

---

# 7. Hard Evidence

Evidence 不应该只是 Claude 的摘要。

一条 Evidence 至少需要同时保留两个层次：

```text
Source
+
Interpretation
```

即：

```text
原论文在哪里说了什么
+
这段内容对当前研究问题意味着什么
```

这两个层次必须分开。

Harness 可以机械保证：

```text
Paper 存在
Evidence ID 存在
Locator 合法
Citation 可解析
Schema 合法
```

但：

```text
这段 Evidence 是否真的支持 Claim
```

仍然是语义判断。

因此：

> **Hard Evidence 不等于 Python 判断真理。**

而是：

> **Python 保证语义判断建立在真实、可追溯的 Evidence 上。**

---

# 8. Research Must Be Gap-Driven

Research Loop 继续运行，不应该只是因为：

> “感觉还可以再搜一些。”

每一轮新的搜索最好能回答：

```text
当前还有什么明确问题没有解决？
```

也就是说：

```text
Evidence
↓
Understanding
↓
Research Gap
↓
New Query / Read / Verification
```

Query 的具体措辞由 Claude 判断。

Harness 负责记录：

```text
这个 Query 为什么被发起
它服务于哪个 Gap
是否重复
是否还有 Budget
```

因此：

> **研究循环由 Gap 推进，而不是由惯性推进。**

---

# 9. Researcher Cannot Self-Declare DONE

做研究的人不应该同时拥有最终宣布：

```text
DONE
```

的权限。

Researcher 最多应该说：

```text
ready_for_review
```

然后由一个新的 Review Context 检查：

```text
Research Questions 是否覆盖
关键 Evidence 是否成立
Contradictions 是否被处理
Critical Gaps 是否仍存在
```

因此：

```text
Researcher
      ↓
ready_for_review
      ↓
Independent Review
      ↓
PASS / CONTINUE / UNCERTAIN
```

核心思想：

> **完成不是 Agent 的一句话，而是一个经过 Evidence 检查后的状态。**

---

# 10. Criteria Over Magic Scores

研究质量不应该最终压成：

```text
sufficiency_score = 0.83
```

然后因为：

```text
0.83 > 0.80
```

就宣布完成。

因为不同问题不能简单互相补偿。

例如一个 Critical Research Question 完全没有证据，不能因为其他几个问题覆盖很好而被平均掉。

所以：

```text
Numbers
→ bound resources

Typed Criteria
→ judge semantic quality
```

数字适合控制：

```text
最大搜索次数
最大论文数
最大迭代
Context Size
Retry
```

语义质量则使用：

```text
covered
partial
missing

supporting
contradicting
qualifying

PASS
CONTINUE
UNCERTAIN
PARTIAL
```

一句话：

> **用数字限制成本，用 Evidence 和 Criteria 判断是否完成。**

---

# 11. Budget Does Not Mean Completion

Budget 用来控制自主研究的边界。

如果 Budget 耗尽：

```text
Research must stop spending resources
```

但这不意味着：

```text
Research is complete
```

更合理的是：

```text
Budget exhausted
      ↓
Review
      ↓
PASS / PARTIAL / needs more research
```

因此：

> **Budget 决定还能不能继续做，Evidence 决定是否已经做够。**

---

# 12. Contradictions Are Valuable State

论文调研的目标不是把所有论文强行总结成一个统一答案。

真实研究中经常存在：

```text
supporting evidence
contradicting evidence
scope-dependent results
insufficient evidence
```

这些不应该在最终综合时被悄悄抹平。

因此：

> **Contradiction 是研究结果，不是需要清理掉的噪音。**

它应该被显式记录，并进入 Review、Report 和未来知识积累。

---

# 13. Evidence First, Synthesis Second

我们不希望：

```text
Claude 先形成一个漂亮结论
      ↓
最后再寻找 Citation
```

而应该：

```text
Search / Read
      ↓
Accepted Evidence
      ↓
Analysis
      ↓
Synthesis
```

最终 Report 的核心 Claim 应该能够回到 Evidence。

因此：

> **报告是 Evidence 的综合，不是 Conversation Memory 的文学化重写。**

---

# 14. Wiki Is Memory, Not Truth

一次 Research Run 中有价值的成果不应该随着 Report 完成而消失。

Accepted Evidence 应该能够进一步形成长期知识：

```text
Accepted Evidence
        │
        ├──→ Survey Report
        │
        └──→ Local Wiki
```

但是 Wiki 不应该成为第二个事实源。

未来研究可以从 Wiki 获得：

```text
已知技术路线
代表论文
已有结论
历史矛盾
Open Questions
```

作为 Research Prior。

但真正需要重新声称一个事实时，仍然应该回到：

```text
Evidence / Paper
```

因此：

> **Wiki 帮助我们决定下一步调查什么；论文决定我们被允许声称什么。**

---

# 15. Wiki and Report Are Projections

长期知识和最终报告都不应该拥有自己的独立 Truth。

关系应保持：

```text
             Accepted Evidence
                    │
           ┌────────┴────────┐
           ▼                 ▼
          Wiki             Report
```

这意味着：

> Report 和 Wiki 都应该尽可能可以从 Evidence State 重新生成。

尤其 Wiki 不应该通过：

```text
旧页面
+
新页面
+
反复 LLM 重写
```

逐渐形成一个无法追溯的第二事实源。

---

# 16. Complexity Must Earn Its Place

我们已经有过一个功能丰富但控制面过度复杂的旧实现。

因此新版每增加一个：

```text
Module
State
Dependency
Workflow
Agent
Phase
Database
Graph
Score
```

都应该回答：

```text
它解决什么真实问题？

没有它会发生什么？

有没有更简单的方法？
```

如果回答不了：

> 不进入 Core。

因此 V1 不追求：

```text
Multi-Agent Swarm
Graph Database
Vector Database
Generic Agent Framework
Second Python Agent Runtime
Complex Citation Graph
Self-Modifying Harness
```

除非后续真实运行证明这些复杂度有必要。

---

# 17. 总结

这个 Harness 最终想做到的不是：

> 让 Claude 更聪明。

而是：

> **让 Claude 的论文调研过程更可靠。**

整个系统可以压缩成四句话：

```text
Simple Loop
Rich State
Hard Evidence
Independent Review
```

再加两条长期约束：

```text
Claude owns semantic research.
Python owns deterministic reliability.

Evidence is truth-bearing state.
Report and Wiki are projections.
```

最终希望得到的是：

> **一个 Claude Code 可以自然地做研究，而工程系统可以持续记住、检查、恢复和约束研究过程的 Literature Research Harness。**
