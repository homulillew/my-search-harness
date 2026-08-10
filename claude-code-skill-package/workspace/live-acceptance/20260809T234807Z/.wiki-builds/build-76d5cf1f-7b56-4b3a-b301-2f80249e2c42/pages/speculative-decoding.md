# Speculative Decoding

Speculative decoding 是以低成本 proposal 换取昂贵模型并行验证的一组推理机制。后续研究首先要区分生成目标：vanilla draft-and-verify 保持原 target distribution；speculative contrastive decoding 使用 contrastive expert/amateur distribution；collaborative speculation 则精确采样预先定义的多模型 combined distribution。

## 可复用的研究地图

- **Lossless draft-and-verify**：适合要求不改变 target sampling semantics 的场景。其收益来自减少串行 target invocations，但受 acceptance、draft cost、proposal length 与可用并行资源共同限制。
- **Speculative contrastive decoding**：把困难 token 的 contrastive 修正与简单 token 的快速接受结合。它可能改善任务指标，但改变了生成目标，且不同实现、任务和超参数并非一致占优。
- **Collaborative decoding via speculation**：面向本来就需要多个模型的 ensemble/contrastive collaboration。alternate proposer 可利用 bonus token；实验 speedup 必须相对 collaborative baseline 解读，不能直接与单模型自回归混为一谈。

## 冲突与条件

“保持原模型输出”和“通过组合分布改善质量”是不同目标，不应压成同一结论。已报告的速度区间依赖模型对、任务、硬件和基线；更长 proposal 既增加潜在提交量，也增加拒绝后的浪费。

## Future research leads

1. 用实时 acceptance、成本比与硬件负载动态选择 proposal model 和 proposal length，同时显式保留输出分布语义。
2. 为 distribution-changing speculation 建立同时报告质量、wall-time、额外 FLOPs、显存和硬件条件的可复现实验协议。

## Primary-paper leads

- Fast Inference from Transformers via Speculative Decoding（arXiv:2211.17192）
- Speculative Contrastive Decoding（arXiv:2311.08981）
- Fast Large Language Model Collaborative Decoding via Speculation（arXiv:2502.01662）

这些条目是 future-run 的研究线索，不替代重新 Retain、读取 Primary Paper 和建立当前 Run State。
