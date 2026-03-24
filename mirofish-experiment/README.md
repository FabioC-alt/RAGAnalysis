# MiroFish Experiment

Experimental exploration and integration of MiroFish with existing RAG/GraphRAG systems.

## Directory Structure

```
mirofish-experiment/
├── backend/           # Backend customization and graph storage experiments
├── frontend/          # Frontend UI experiments and extensions
├── configs/           # Configuration files (.env, docker-compose variations)
├── scripts/           # Deployment and setup scripts
├── notebooks/         # Jupyter notebooks for testing and integration
└── README.md          # This file
```

## Reference

- **MiroFish GitHub**: https://github.com/nikmcfly/MiroFish-Offline
- **Uses**: Neo4j 5.15+ CE + Ollama (fully offline)
- **Original Purpose**: Multi-agent simulation engine for social dynamics simulation
- **Potential Integration**: Graph storage abstraction layer with RAGAnalysis projects

## Next Steps

1. Clone MiroFish repository as a submodule or reference
2. Explore Neo4j GraphStorage abstraction interface
3. Test integration with existing RAG pipelines
4. Experiment with custom agent personalities for O-RAN domain
5. Benchmark graph storage performance vs. current setup

## Prerequisites

- Docker & Docker Compose
- Neo4j 5.15+ Community Edition
- Ollama with qwen2.5 and nomic-embed-text models
- Python 3.11+
- Node.js 18+ (for frontend)

## Quick Start

```bash
# Copy example configuration
cp configs/.env.example .env

# Launch services (see scripts/)
docker compose -f configs/docker-compose.yml up -d

# Verify Neo4j and Ollama are running
docker ps
```

## Notes

- Keep this as a clean experiment space separate from production RAG systems
- Document findings and integration patterns
- Test custom GraphStorage implementations here first
