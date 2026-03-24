# RAG System Requirements

## Project Overview
End-to-end Retrieval-Augmented Generation (RAG) pipeline for O-RAN (Open Radio Access Network) document analysis with support for both open-ended questions and multiple-choice questions (MCQ).

## System Architecture Requirements

### 1. Data Sources
- **Document Source**: 3GPP O-RAN specifications in markdown format
- **Storage Location**: `dataOran/3gpp-specifications-md/`
- **Processing**: Folder-based extraction of structured text (titles and paragraphs)

### 2. Embedding & Vector Storage
- **Embedding Model**: `nomic-embed-text` (fallback: `mxbai-embed-large:latest`)
- **Vector Dimension**: 1024-dimensional embeddings
- **Storage Format**: JSON files with pre-computed embeddings
  - `paragraph_title_vectors.json` (~992MB): ~23,501 paragraph titles
  - `section_title_vectors.json` (~7.5MB): Section titles

### 3. Graph Database
- **Type**: Neo4j
- **Connection**: `neo4j://localhost:7687`
- **Authentication**: Username/password (configurable)
- **Node Types**: Paragraph, Entity
- **Relationships**: Knowledge graph triplets (subject → verb → object)

### 4. Language Model
- **Primary Model**: `llama3:8b` (via Ollama)
- **Bigger Model**: `mistral-nemo`
- **Functions**:
  - Entity extraction from text
  - Final answer generation
  - MCQ fallback resolution

## Functional Requirements

### 4.1 Retrieval Pipeline
- **Multi-path retrieval**:
  - Path 1: Query → paragraph similarity search → neighbor expansion via Neo4j → section chunks
  - Path 2: Query → direct section search (fallback)
- **Relevance Filtering**: O-RAN-specific queries must retrieve O-RAN-relevant content
- **Configurable Parameters**:
  - `paragraph_top_k` (default: 5, tested: 8)
  - `neighbors_per_title` (default: 5, tested: 8)
  - `section_top_k` (default: 3, tested: 5)
  - `max_chunks` (default: 6, tested: 8)

### 4.2 Question Type Detection
- **MCQ Detection**: Automatically identify multiple-choice questions with options A-D
- **Format Support**: 
  - Questions with explicit option labels (A), B), C), D))
  - Spacing variations and formatting inconsistencies

### 4.3 Answer Generation

#### For Open-Ended Questions
- Output Mode: `full` (detailed response with context references)
- Behavior: Return "Insufficient context: retrieval returned no relevant chunks" if no contexts pass relevance gate
- Format: Multi-part response with answer and sources

#### For Multiple-Choice Questions
- Output Mode: `one_line` (concise option response)
- Two Execution Paths:
  1. **Retrieval-Based Scoring** (when contexts available):
     - Parse options from query
     - Score each option using semantic similarity:
       - 35% weight: query embedding × option embedding
       - 65% weight: option embedding × retrieved context embeddings
     - Return highest-scoring option
  2. **LLM Fallback** (when 0 contexts pass relevance gate):
     - Call LLM directly for MCQ resolution
     - Return model's selected option
     - Flag as knowledge-based (not retrieval-grounded)

### 4.4 Output Structure
```json
{
  "query": "string - original query",
  "model": "string - LLM model used",
  "embedding_model": "string - embedding model used",
  "answer": "string - generated answer",
  "contexts": "array - retrieved context chunks",
  "grouped_hits": "array - grouped retrieval results",
  "option_scores": "array - MCQ option scores (if applicable)"
}
```

## Quality Requirements

### 5.1 Precision Improvements
- **Goal**: Maximize correct answer generation for MCQs
- **Method**: Quality gates that enforce domain relevance before option scoring
- **Validation**: 
  - O-RAN queries must retrieve O-RAN content (contains "o-ran" or "oran")
  - Weak retrieval context (0 chunks) triggers fallback instead of poor-quality scoring

### 5.2 Context Quality
- **Minimum Standards**:
  - Retrieved chunks must be scored above relevance threshold
  - Title-only entries acceptable but full paragraph bodies preferred
  - Multi-section chunks grouped for better context coherence

### 5.3 Fallback Strategy
- **Graceful Degradation**: When retrieval fails, fallback to knowledge-based LLM response
- **Transparency**: Distinguish between retrieval-grounded and knowledge-based answers
- **Reliability**: Fallback should still produce correct answers for MCQs

## Test Cases

### Test Case 1: O-RAN Working Groups (MCQ)
```
Question: Which O-RAN Working Group focuses on the architecture description 
          of Open Radio Access Networks?
Options:
  A) O-RAN.WG3
  B) O-RAN.WG4
  C) O-RAN.WG1
  D) O-RAN.WG5
Expected Answer: (Correct answer to be validated)
Execution Parameters:
  - paragraph_top_k: 8
  - neighbors_per_title: 8
  - section_top_k: 5
  - max_chunks: 8
  - output_mode: one_line
  - use_mcq_option_scoring: true
```

### Test Case 2: O-RAN Core Principles (MCQ)
```
Question: What are the core principles of O-RAN?
Options:
  A) Intelligence and openness
  B) Speed and reliability
  C) Cost reduction and scalability
  D) Proprietary integration and security
Expected Answer: A) Intelligence and openness
Execution Parameters: Same as Test Case 1
Result: ✓ PASS (correctly generated A)
Execution Path: LLM fallback (0 retrieved contexts)
```

## Technical Specifications

### 6.1 Text Processing
- **Normalization**: Case-insensitive title matching with whitespace normalization
- **Signature Generation**: Canonical title keys for consistency across source files
- **Adaptive Embedding**: Truncate text if embedding dimension exceeded (fallback to first 512 tokens)

### 6.2 Similarity Computation
- **Title Similarity**: Cosine similarity over 1024-dim vectors from vector stores
- **Threshold**: Default relevance threshold for filtering (configurable)
- **Weighted Averaging**: For MCQ option scoring:
  - `total_score = 0.35 × query_similarity + 0.65 × context_similarity`

### 6.3 Error Handling
- **Model Fallback**: If primary embedding model unavailable, auto-select from installed models
- **Neo4j Failures**: Catch connection errors and continue with direct section search
- **Property Mismatches**: Handle title-property-missing errors gracefully (use name fallback)

## Performance Requirements

### 7.1 Response Time
- Target: < 30 seconds per query (current baseline: 25-28 seconds)
- Includes: Embedding computation, graph traversal, LLM inference

### 7.2 Scalability
- Handle ~23,500 paragraphs and ~7,500 sections
- Support concurrent queries via Ollama server
- Memory usage: Up to 1GB+ for vector stores in RAM

## Integration Requirements

### 8.1 Dependencies
- `neo4j` (Python driver): Graph database operations
- `ollama` (API via requests): LLM inference
- `json`: Vector store file I/O
- `re`: Regex for query parsing and option extraction
- `math`: Similarity computations

### 8.2 External Services
- **Ollama Server**: Running locally at default endpoint
- **Neo4j Instance**: Running at `neo4j://localhost:7687`
- Both services must be started before pipeline execution

## Success Criteria

1. ✓ MCQ answering with correct option selection
2. ✓ Relevance filtering preventing non-domain chunks in results
3. ✓ Graceful fallback when retrieval yields 0 contexts
4. ✓ Consistent 1024-dim embedding across all vector stores
5. ✓ Multi-choice question format parsing with option extraction
6. ✓ Semantic similarity-based option scoring
7. ✓ Full execution without Python errors
8. ✓ Configurable retrieval parameters for precision-recall tuning

## Known Issues & Future Work

### Current Known Issues
- Neo4j property "title" missing on some nodes (workaround: use name property)
- Graph connectivity sparse for some paragraphs (neighbor expansion yields small sets)
- Document corpus may lack comprehensive O-RAN coverage in some areas

### Future Enhancements
- Bulk MCQ test set evaluation
- Fine-tuned parameter optimization per document domain
- Confidence scoring to distinguish high-confidence vs fallback answers
- Schema alignment between Neo4j expected properties and actual node attributes
- Integration with semantic chunking for better context extraction
