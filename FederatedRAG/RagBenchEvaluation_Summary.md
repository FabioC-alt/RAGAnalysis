# RAG Evaluation: Semantic vs Fixed-Size Chunking
## RagBench TechQA Dataset Analysis

**Date:** March 3, 2026  
**Metric:** BERTScore (Zhang et al., 2019)

---

## Overview

This evaluation compares two chunking strategies for Retrieval-Augmented Generation (RAG):

| Strategy | Description |
|----------|-------------|
| **Semantic Chunking** | Detects breakpoints using cosine distance between sentence embeddings; configurable percentile threshold |
| **Fixed-Size Chunking** | Divides text into uniform 500-character segments |

---

## Dataset

| Split | Samples | Size |
|-------|---------|------|
| Training | 1,192 | ~23 MB |
| Test | 314 | ~6 MB |

---

## Percentile Sensitivity Results

Evaluation on 50 test samples across 5 percentile thresholds:

### BERTScore F1 Comparison

| Percentile | Semantic F1 | Fixed F1 | Δ F1 |
|------------|-------------|----------|------|
| 75 | 0.5164 | 0.5237 | -0.0073 |
| 80 | 0.5156 | 0.5237 | -0.0081 |
| 85 | 0.5095 | 0.5237 | -0.0142 |
| 90 | 0.5051 | 0.5237 | -0.0186 |
| 95 | 0.5038 | 0.5237 | -0.0199 |

### Chunk Count & Memory Comparison

| Percentile | Semantic Chunks | Fixed Chunks | Chunk Reduction | Memory Reduction |
|------------|-----------------|--------------|-----------------|------------------|
| 75 | 68,686 | 46,134 | -48.9% | -48.9% |
| 80 | 54,951 | 46,134 | -19.1% | -19.1% |
| 85 | 41,213 | 46,134 | +10.7% | +10.7% |
| 90 | 27,477 | 46,134 | +40.4% | +40.4% |
| 95 | ~14,000 | 46,134 | ~70% | ~70% |

### Average Chunk Size

| Percentile | Semantic Avg (chars) | Fixed Avg (chars) | Size Ratio |
|------------|---------------------|-------------------|------------|
| 75 | ~340 | 500 | 0.68x |
| 80 | ~420 | 500 | 0.84x |
| 85 | ~560 | 500 | 1.12x |
| 90 | ~840 | 500 | 1.68x |
| 95 | ~1,650 | 500 | 3.30x |

---

## Key Findings

### Fixed-Size Chunking Wins on This Dataset

- **F1 Score:** Fixed-size outperforms semantic at all percentile levels
- **Margin:** ~2-4% higher F1 depending on threshold
- **Consistency:** Fixed-size provides stable, predictable results

### Semantic Chunking Trade-offs

| Percentile | F1 Degradation | Storage Savings |
|------------|----------------|-----------------|
| 85 | -2.7% | +10.7% |
| 90 | -3.5% | +40.4% |
| 95 | -3.8% | ~70% |

**Best Trade-off:** Percentile 90-95 offers 40-70% chunk/memory reduction with only ~4% F1 loss.

---

## Recommendations

### Use Semantic Chunking When:
- ✓ Storage/cost optimization is a priority
- ✓ Processing structured technical documentation
- ✓ Larger, coherent chunks improve downstream LLM generation
- ✓ ~4% F1 difference is acceptable

### Use Fixed-Size Chunking When:
- ✓ Working with fragmented Q&A data (RagBench-like)
- ✓ Maximum retrieval accuracy is critical
- ✓ Simplicity and predictability are preferred
- ✓ Real-time processing speed matters

---

## Technical Details

### Embedding Model
- `all-MiniLM-L6-v2` (sentence-transformers)

### Semantic Chunking Algorithm
1. Split text into sentences
2. Embed sentences using transformer
3. Calculate cosine distance between consecutive sentences
4. Create breakpoints where distance > percentile threshold

### RAG Pipeline
- Chunk documents using selected strategy
- Embed chunks with same model
- Retrieve top-3 most similar chunks via cosine similarity
- Concatenate retrieved chunks (first 300 chars) as response

### Evaluation
- BERTScore (bert-base-uncased)
- Metrics: Precision, Recall, F1

---

## Conclusion

For the **RagBench TechQA dataset** (fragmented Q&A format), **fixed-size chunking performs marginally better** (~2-4% F1 improvement). However, the difference is relatively small, and **semantic chunking at higher percentiles (90-95) offers significant storage savings (40-70%) with acceptable F1 trade-off**.

The choice between strategies should be context-dependent:
- **Accuracy-critical applications:** Fixed-size
- **Cost/storage-sensitive applications:** Semantic (percentile 90+)

---

*Generated from RagBenchEvaluation.ipynb analysis*
