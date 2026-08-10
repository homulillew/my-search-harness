# KV Cache Offloading and Memory Hierarchy

KV cache offloading belongs to a serving route that preserves or transports cached state instead of necessarily compressing its semantic content. PagedAttention reduces GPU allocation waste and shares prefixes exactly. LMCache reuses exact KV across GPU, CPU, disk, remote, and disaggregated tiers. CacheGen encodes KV for bandwidth-limited cross-machine transfer and may trade a bounded amount of quality for fewer bytes.

The controlling comparison is load versus recomputation. Cache hits, context length, network and host bandwidth, concurrency, prefetch, and TTFT targets determine whether lower-tier reuse helps. A result from a memory-bound or high-reuse service should not be generalized to a cold, compute-bound workload.
