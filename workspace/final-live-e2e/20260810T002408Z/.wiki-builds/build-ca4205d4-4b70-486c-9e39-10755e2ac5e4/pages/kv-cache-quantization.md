# KV Cache Quantization

KV cache quantization lowers bytes per retained key/value rather than deleting historical positions. The established design split is per-channel treatment for keys and per-token treatment for values, with recent residuals, outlier protection, calibration, or sink protection used to control error. KIVI is tuning-free and keeps a full-precision recent window; KVQuant uses calibrated non-uniform formats and sparse outliers. MiniKV shows that INT2 can be combined with token selection, but also that the selector changes the quantization-error distribution.

Use this page as a lead to the cited primary papers. Validate target tasks, attention architecture, bit width, residual budget, hardware kernels, and prompt/decode regime before transferring a result.
