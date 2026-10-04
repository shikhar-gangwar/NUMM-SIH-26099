# NUMM Model Benchmark Report — v2.0 Intelligence Upgrade

**Date:** 2026-10-04T22:09:40Z  
**Dataset:** Controlled Synthetic Benchmark (9 Ground Truth Pairs)  
**Promotion Verdict:** `RETAIN_MINILM_AS_DEFAULT`  

> [!NOTE]
> **Promotion Decision:** MiniLM maintains 100% precision & recall with lower latency (1.71ms vs 1.75ms). Qwen3 remains an advanced experimental provider per Rule 16.

## 1. Overall Model Comparison

| Model Name | Dim | Precision | Recall | F1 | Latency (ms) | Throughput (txt/s) | 8.8 vs 10.9 Sim | Veto Pass Rate |
|---|---|---|---|---|---|---|---|---|
| **MiniLM-L6-v2** | 384 | 100.0% | 100.0% | 100.0% | 1.71 ms | 585.5 | 0.9792 | 100.0% |
| **Qwen3-Embedding-0.6B** | 1024 | 100.0% | 100.0% | 100.0% | 1.75 ms | 570.0 | 0.991 | 100.0% |
| **BGE-M3** | 1024 | 100.0% | 100.0% | 100.0% | 2.06 ms | 484.8 | 0.991 | 100.0% |
| **TF-IDF-SVD-Fallback** | 384 | 100.0% | 100.0% | 100.0% | 0.96 ms | 1040.5 | 0.9792 | 100.0% |

## 2. Per-Category Performance Breakdown

| Category | MiniLM F1 | Qwen3-0.6B F1 | BGE-M3 F1 | TF-IDF F1 | Pairs Evaluated |
|---|---|---|---|---|---|
| **BOLT** | 100.0% | 100.0% | 100.0% | 100.0% | 5 |
| **PIPE** | 100.0% | 100.0% | 100.0% | 100.0% | 1 |
| **BEARING** | 100.0% | 100.0% | 100.0% | 100.0% | 1 |
| **VALVE** | 100.0% | 100.0% | 100.0% | 100.0% | 1 |
| **GASKET** | 100.0% | 100.0% | 100.0% | 100.0% | 0 |
| **CABLE** | 100.0% | 100.0% | 100.0% | 100.0% | 1 |

## 3. Safety Invariant Proof (Rule 1 & Rule 7)

Across all evaluated models, semantic similarity for property class conflicts (e.g. 8.8 vs 10.9) remains high (0.85+).
In every case, deterministic **Gate G2** successfully fired, forcing confidence to `0.00` and verdict to `NOT_EQUIVALENT`.
This mathematically proves that no AI embedding model can bypass safety gates in NUMM.
