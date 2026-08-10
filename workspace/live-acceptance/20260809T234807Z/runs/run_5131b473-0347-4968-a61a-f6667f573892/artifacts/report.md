# Speculative Decoding：LLM 推理加速的方法与边界

## 背景与基本机制

自回归语言模型一次通常只确定一个新 token，模型权重读取与串行依赖使低 batch、memory-bandwidth-bound 推理难以充分利用并行硬件。Speculative decoding 的基本做法是让低成本 draft model 顺序提出一段候选 token，再让昂贵 target model 在一次并行 forward 中同时评分这些候选。候选从左到右接受；首次拒绝时丢弃后续候选，并从 target 与 draft 的 residual distribution 重新采样。全部接受时还可从 target 分布追加一个 bonus token。这个接受—拒绝构造保证输出仍服从原 target model 的采样分布，而不是近似替换模型输出。[1, section: Speculative Decoding]

速度取决于一次验证平均提交多少 token，以及 draft 相对 target 的成本。Leviathan 等在 T5-XXL、单 TPU、batch size 1 的翻译与摘要实验中报告约 2.3×–3.4× wall-time speedup；较大的 draft 虽可能提高 acceptance，却可能因自身成本更高而更慢。[1, section: Experiments]

## 三条主要路线

### 1. 保持目标分布的 draft-and-verify

这是最严格的 lossless 路线：draft 只改变执行计划，不改变 target distribution。它无需修改 target 架构或重新训练，并保证最坏情况下每轮至少提交一个 target token。然而，低 acceptance 会浪费后部 proposal，额外并行算力不足时也可能无法换来 latency 收益。论文明确把 beam search、定制 draft、层级 speculation、动态 draft/γ 与其他模态列为后续方向。[1, section: Discussion]

### 2. Speculative Contrastive Decoding

SCD 不再把原 expert distribution 作为唯一验证目标，而是结合 amateur/expert logits 构造 contrastive distribution，再以 speculative acceptance 加速该新目标。其价值在于 rejected 的困难 token 可接受 contrastive 修正，accepted 的简单 token 则快速通过；因此它联合讨论生成质量和效率，而不是仅复现 expert。[2, section: Speculative Contrastive Decoding]

在 Llama-2 7B/70B 与 WikiText、GSM8K、HumanEval、AlpacaEval 设置中，original SCD 的 HumanEval Pass@1 为 37.20，对照 70B 为 28.66；improved SCD 在 WikiText 获得 15.20 perplexity。但 improved 版本在 HumanEval 与 AlpacaEval 明显弱于 original，说明不同任务不存在统一占优的 contrastive 实现。[2, section: Experiments] 其速度主要由 acceptance、amateur/expert cost ratio 和超参数共同决定；全部 proposal 被接受时还需要一次额外 amateur forward。[2, section: Analysis]

### 3. Collaborative Decoding via Speculation

CoS 面向 ensemble 或 contrastive 等多模型协作。它先定义 combined distribution，再用 proposal distribution 对其执行可证明正确的接受与 residual resampling；alternate proposal framework 进一步把 verifier 产生的 bonus token 交给下一轮反向验证，使两个模型交替担任 proposer，并可推广到多模型。[3, section: Collaborative Decoding via Speculation]

相对标准 collaborative decoding，论文的 weighted-ensemble CoS 设置约为 1.27×–1.85×，contrastive-decoding CoS 约为 1.11×–2.23×。这些数字不能直接当作单 target 自回归基线上的加速：基线是原本就要调用多个模型的协作解码。实验还显示，简单把 vanilla SD 套到协作场景并不保证收益，若 acceptance 低可降到 0.92×–0.98×。[3, section: Experiments]

## 比较与工程 trade-off

| 路线 | 生成目标 | 主要收益 | 关键限制 |
|---|---|---|---|
| Lossless draft-and-verify | 原 target distribution | 减少串行 target invocations | 需要廉价且匹配的 draft 与并行资源 |
| SCD | contrastive expert/amateur distribution | 联合质量修正与 speculative efficiency | 改变目标分布，结果和速度对任务、超参数敏感 |
| CoS | 明确定义的多模型 combined distribution | 加速已有 ensemble/contrastive collaboration | 收益基线、模型成本与组合函数决定可比性 |

三者共同的控制量是 acceptance rate、proposal cost 和 proposal length γ。增大 γ 提高每轮潜在提交量，但后部 token 依赖未验证前缀，拒绝后会扩大无效计算；最优值必须结合模型对、任务与硬件测量。吞吐、单请求 latency、额外 FLOPs、显存和并发余量也不能用单一 speedup 数字替代。

## Open Problems

第一，能否根据输入难度、实时 acceptance、draft/target 成本和硬件负载动态选择 proposal model 与 γ，同时仍清楚声明输出究竟服从原 target、contrastive 还是 combined distribution？foundation 的动态与层级 proposal 建议，以及 CoS 的 γ 敏感性，都说明静态配置不是最终答案。

第二，当 relaxed acceptance、contrastive 或 ensemble 主动改变输出分布时，需要怎样的跨任务评测，才能同时报告质量、wall-time、额外计算与硬件条件，并避免把特定 benchmark 上的收益泛化为普遍结论？当前三篇工作的实验基线、设备和任务差异很大，这一问题尚未解决。

## 结论

Speculative decoding 不是单一算法，而是一组用便宜 proposal 换取昂贵验证并行度的机制。选择路线前应先固定目标分布语义和比较基线，再围绕 acceptance、成本比、γ 与部署硬件优化；否则“更快”可能来自改变生成目标或更换基线，而不是同一推理任务的无损加速。

## References

1. Yaniv Leviathan, Matan Kalman, Yossi Matias “Fast Inference from Transformers via Speculative Decoding.” 2022 arXiv 2211.17192; https://arxiv.org/abs/2211.17192
2. Hongyi Yuan, Keming Lu, Fei Huang, Zheng Yuan, Chang Zhou “Speculative Contrastive Decoding.” 2023 arXiv 2311.08981; https://arxiv.org/abs/2311.08981
3. Jiale Fu, Yuchu Jiang, Junkai Chen, Jiaming Fan, Xin Geng, Xu Yang “Fast Large Language Model Collaborative Decoding via Speculation.” 2025 arXiv 2502.01662; https://arxiv.org/abs/2502.01662
