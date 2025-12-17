# Protein Analysis Platform (MongoDB + Neo4j)

End-to-end platform to store, query, analyze, and annotate protein data using a document store (MongoDB) and a graph database (Neo4j). It supports search, graph-based neighborhood exploration, and function prediction via weighted label propagation.

## Overview

- Document store for UniProt-like protein records with EC numbers and InterPro domains
- Graph representation of protein similarity using Jaccard coefficient over domains
- REST API (Flask) for search, stats, graph queries, and predictions
- Optional lightweight web UI (templates/index.html) for quick exploration

## Architecture

- Services (Docker Compose): MongoDB, Neo4j, Python API
- Data flow:
	- Load TSV proteins into MongoDB
	- Build graph in Neo4j from Mongo documents (domains → similarities)
	- Run label propagation to predict EC numbers for unlabeled proteins

```
TSV → MongoDB (proteins) → Neo4j (graph) → Predictions (Mongo + Neo4j)
```

## Repository Structure

```
projet_nosql_prot/
├── docker/
│   ├── mongodb/Dockerfile
│   ├── neo4j/Dockerfile
│   └── python/
│       ├── Dockerfile
│       └── requirements.txt
├── src/
│   ├── app.py                  # Flask REST API + simple UI
│   ├── data_loader.py          # Load TSV → MongoDB
│   ├── graph_builder.py        # Build Neo4j graph (Jaccard over InterPro)
│   ├── label_propagation.py    # Weighted label propagation
│   └── database/
│       ├── mongodb_client.py   # MongoDB helpers
│       └── neo4j_client.py     # Neo4j helpers
├── data/                       # Input TSV files
├── templates/
│   └── index.html              # Minimal UI
├── docker-compose.yml
└── README.md                   # Extended documentation
```

## Tech Stack

- MongoDB (document store)
- Neo4j 5.x (graph database)
- Python 3.11 + Flask 3.x (API)
- NetworkX/NumPy/Pandas (data utilities)

## Requirements

- Docker + Docker Compose
- ~8 GB RAM, 10+ GB disk recommended for larger datasets

## Setup & Run

1) Start services

```bash
docker compose up -d
```

2) Load data (TSV with columns: Entry, Entry Name, Protein names, Organism, Sequence, EC number, InterPro)

```bash
# Example: download a small, reviewed human subset (50 rows)
wget -O data/uniprot_data.tsv 'https://rest.uniprot.org/uniprotkb/stream?format=tsv&query=reviewed:true+AND+organism_id:9606&fields=accession,id,protein_name,organism_name,sequence,ec,xref_interpro&size=50'

# Import into MongoDB
docker compose exec python python src/data_loader.py
```

3) Build the protein graph in Neo4j

```bash
docker compose exec python python src/graph_builder.py
```

4) Predict EC numbers for unlabeled proteins

```bash
docker compose exec python python src/label_propagation.py
```

5) Open the UI / API

- UI: http://localhost:5000
- Neo4j Browser: http://localhost:7474 (neo4j / password123)

## Configuration

Environment variables (via `.env` or Compose):

```
# Databases
MONGO_URI=mongodb://root:password123@mongodb:27017/
MONGO_DB_NAME=protein_db
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

# Graph builder
SIMILARITY_THRESHOLD=0.1       # Min Jaccard for edges
PROTEIN_LIMIT=                 # Optional cap for testing
CLEAR_GRAPH=false              # true to rebuild from scratch

# Label propagation
CONFIDENCE_THRESHOLD=0.3
MIN_EDGE_WEIGHT=0.1
MAX_LABELS_PER_PROTEIN=5

# Data location
DATA_DIR=/app/data
```

## REST API (Implemented)

- Health
	- `GET /health` – service status and DB connectivity

- MongoDB
	- `GET /api/mongodb/search?q=term&limit=50`
	- `GET /api/mongodb/protein/<id>`
	- `GET /api/mongodb/statistics`

- Neo4j
	- `GET /api/neo4j/protein/<id>`
	- `GET /api/neo4j/neighbors/<id>?depth=1|2&min_weight=0.1&limit=50`
	- `GET /api/neo4j/neighborhood/<id>?depth=2&min_weight=0.1&limit=100` (viz payload)
	- `GET /api/neo4j/search?q=term&limit=50`
	- `GET /api/neo4j/statistics`
	- `GET /api/neo4j/adaptive-threshold/<id>?target_neighbors=10` – calculate optimal threshold
	- `GET /api/neo4j/neighbors-adaptive/<id>?target_neighbors=10` – auto-adjust threshold per protein

- Combined
	- `GET /api/statistics/overview` – MongoDB + Neo4j summary

- Predictions
	- `GET /api/predictions` – paginated list
	- `GET /api/predictions/<id>` – prediction for a protein

## Data Workflow

1) Run `src/data_loader.py` to populate MongoDB with proteins, EC numbers, and InterPro domains
2) Run `src/graph_builder.py` to create `Protein` nodes and `SIMILAR_TO` edges using Jaccard over domains
3) Run `src/label_propagation.py` to assign predicted EC numbers to unlabeled proteins (stored in MongoDB and Neo4j)

## Adaptive Similarity Thresholds

The platform implements **adaptive thresholds** to handle proteins with varying neighbor counts:

**Problem**: Fixed threshold (0.1) causes:
- High-degree proteins: 200+ neighbors (overwhelming)
- Low-degree proteins: 2-3 neighbors (insufficient)

**Solution**: Automatically adjust threshold per protein to target ~10 neighbors.

### Usage

```bash
# Get recommended threshold for a protein
curl http://localhost:5000/api/neo4j/adaptive-threshold/A0A087X1C5?target_neighbors=10

# Get neighbors with adaptive threshold
curl http://localhost:5000/api/neo4j/neighbors-adaptive/A0A087X1C5?target_neighbors=15
```

### Algorithm

1. Retrieve all edge weights for protein (sorted descending)
2. If total ≤ target: use minimum weight (keep all)
3. If total > target: use weight at position `target` (keep top N)

### Cypher Implementation

```cypher
// Get adaptive threshold for protein
MATCH (p:Protein {id: 'A0A087X1C5'})-[r:SIMILAR_TO]-()
WITH p, r
ORDER BY r.weight DESC
WITH p, collect(r.weight) as weights, count(r) as total
RETURN 
  p.id,
  total as total_neighbors,
  weights[9] as threshold_for_10_neighbors,
  weights[0] as max_weight,
  weights[size(weights)-1] as min_weight
```

## Neo4j Queries (Examples)

```cypher
// Count proteins
MATCH (p:Protein) RETURN count(p);

// Most connected proteins
MATCH (p:Protein)-[r]-()
WITH p, count(r) AS degree
RETURN p.id, p.name, degree
ORDER BY degree DESC
LIMIT 10;

// Neighborhood visualization
MATCH path = (p:Protein {id: "YOUR_ID"})-[:SIMILAR_TO*1..2]-(n)
RETURN path LIMIT 50;

// Analyze neighbor distribution
MATCH (p:Protein)-[r:SIMILAR_TO]-()
RETURN p.id, count(r) as neighbor_count
ORDER BY neighbor_count DESC
LIMIT 20;
```

## Tips

- Start small (50–100 proteins) to validate the pipeline
- Use higher `min_weight` to reduce dense neighborhoods
- Use `PROTEIN_LIMIT` during development to control graph size

## Troubleshooting

```bash
# Check service status and logs
docker compose ps
docker compose logs -f python
docker compose logs -f neo4j
docker compose logs -f mongodb

# Recreate everything
docker compose down -v
docker compose up -d
```

## Contributing & Development

- API code: `src/app.py`
- DB helpers: `src/database/`
- Algorithms: `src/graph_builder.py`, `src/label_propagation.py`
- Documentation: see `README.md` and `doc/`

Suggested flow for new features:

1) Implement/extend logic in `src/` modules
2) Add endpoints in `src/app.py`
3) Document usage in `doc/` and update this README

---

For a deeper dive (benchmarks, extended docs, endpoint catalog), see the main [README.md](README.md) and the docs in `doc/`.
