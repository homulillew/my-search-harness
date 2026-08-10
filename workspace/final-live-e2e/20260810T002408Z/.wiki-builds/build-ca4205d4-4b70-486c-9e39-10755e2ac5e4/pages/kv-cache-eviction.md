# KV Cache Eviction and Token Selection

KV cache eviction shortens the retained sequence and can reduce both memory and attention work, but removed evidence cannot be recovered. H2O updates heavy-hitter scores during decoding; SnapKV selects prompt clusters before generation; StreamingLLM keeps attention sinks plus recent tokens; XKV allocates application-specific budgets across layers. These are different policies with different assumptions, not interchangeable names for one algorithm.

Quality thresholds vary by task, model, prompt, budget, and generation length. Long reasoning can degrade sharply or fail to terminate under aggressive budgets, so evaluation should include output length and termination behavior as well as accuracy.
