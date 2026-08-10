# Architectural KV Head and Layer Sharing

Architectural KV sharing reduces how many independent KV tensors a model creates. CLA reuses KV activations across adjacent layers, while MLKV shares heads within and across layer groups. This route requires training or uptraining and therefore differs from inference-only eviction and quantization.

Lower cache capacity does not by itself imply lower decode latency: shared KV may still be fetched at every consuming layer. Existing evidence is concentrated in smaller or specially trained models, so modern long-context models, optimized kernels, and combinations with inference-time compression remain research leads.
