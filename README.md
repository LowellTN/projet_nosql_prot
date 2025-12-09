# Projet NoSQL Protein Annotation

## Overview

This project implements a complete NoSQL-based system for querying and analyzing protein data using **MongoDB** (document store) and **Neo4j** (graph database). The system enables efficient protein search, graph-based analysis, and automated function annotation using machine learning.

### Key Features

🔍 **Search & Query**: Search proteins by identifier, name, or description  
🕸️ **Graph Analysis**: Explore protein-protein similarity networks  
🤖 **Function Prediction**: Automated EC number annotation using label propagation  
📊 **Statistics**: Comprehensive database analytics  
🌐 **REST API**: 15+ endpoints for complete data access  
📚 **Documentation**: Extensive technical documentation

## Project Structure

```
projet_nosql_prot/
├── docker/                      # Docker configurations
│   ├── mongodb/Dockerfile       # MongoDB container setup
│   ├── neo4j/Dockerfile         # Neo4j container setup
│   └── python/                  # Python application container
│       ├── Dockerfile
│       └── requirements.txt
├── src/                         # Source code
│   ├── app.py                   # Flask REST API
│   ├── data_loader.py           # Load data into MongoDB
│   ├── graph_builder.py         # Build protein network in Neo4j
│   ├── label_propagation.py    # ML function annotation
│   └── database/                # Database clients
│       ├── mongodb_client.py
│       └── neo4j_client.py
├── data/                        # Data files (*.tsv)
├── doc/                         # Detailed documentation
│   ├── TASK1_MONGODB.md         # MongoDB implementation
│   ├── TASK2_GRAPH_CONSTRUCTION.md  # Graph building
│   ├── TASK3_API_QUERIES.md     # API documentation
│   ├── TASK4_LABEL_PROPAGATION.md   # ML algorithm
│   └── PROJECT_SUMMARY.md       # Complete project summary
├── docker-compose.yml           # Service orchestration
├── .env.example                 # Environment template
└── README.md                    # This file
```

## Technologies Used

| Technology | Purpose | Version |
|------------|---------|---------|
| **MongoDB** | Document database for protein data | latest |
| **Neo4j** | Graph database for protein networks | 5.13.0 |
| **Python** | Application logic and ML | 3.11 |
| **Flask** | REST API framework | 3.0.0 |
| **Docker** | Containerization | Compose v2 |

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- 8GB RAM minimum
- 10GB disk space
- Data files in `data/` folder (*.tsv)

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd projet_nosql_prot

# Create environment file (optional - uses defaults)
cp .env.example .env
```

### 2. Start Services

```bash
# Build and start all containers
docker compose up -d

# Check services are running
docker compose ps

# Expected output:
# NAME                STATUS              PORTS
# protein_mongodb     Up (healthy)        27017:27017
# protein_neo4j       Up (healthy)        7474:7474, 7687:7687
# protein_python_app  Up                  5000:5000
```

### 3. Load Data

```bash
# Load protein data into MongoDB
docker compose exec python python src/data_loader.py

# Expected: ~50,000 proteins loaded in 5 minutes
```

### 4. Build Graph

```bash
# Build protein-protein network in Neo4j
docker compose exec python python src/graph_builder.py

# Expected: ~48,500 nodes, ~250,000 edges in 2 hours
# For testing, set PROTEIN_LIMIT=1000 (takes ~5 minutes)
```

### 5. Run Label Propagation

```bash
# Predict EC numbers for unlabeled proteins
docker compose exec python python src/label_propagation.py

# Expected: ~25,000 proteins annotated in 10 minutes
```

### 6. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **API Documentation** | http://localhost:5000 | - |
| **MongoDB** | mongodb://localhost:27017 | root / password123 |
| **Neo4j Browser** | http://localhost:7474 | neo4j / password123 |

## Usage Examples

### API Queries

```bash
# Search for proteins
curl "http://localhost:5000/api/mongodb/search?q=cytochrome&limit=5"

# Get protein details
curl "http://localhost:5000/api/mongodb/protein/A0A087X1C5"

# Get protein neighbors in graph
curl "http://localhost:5000/api/neo4j/neighbors/A0A087X1C5?depth=1"

# Get neighborhood for visualization
curl "http://localhost:5000/api/neo4j/neighborhood/A0A087X1C5?depth=2&min_weight=0.2"

# Get database statistics
curl "http://localhost:5000/api/statistics/overview"

# Get prediction for protein
curl "http://localhost:5000/api/predictions/A0A0B4J2F0"
```

### MongoDB Queries

```bash
# Connect to MongoDB
docker compose exec mongodb mongosh -u root -p password123

# Use protein database
use protein_db

# Count proteins
db.proteins.countDocuments({})

# Find protein by ID
db.proteins.findOne({identifier: "A0A087X1C5"})

# Search by name
db.proteins.find({name: {$regex: "cytochrome", $options: "i"}}).limit(5)

# Count labeled vs unlabeled
db.proteins.countDocuments({is_labeled: true})
db.proteins.countDocuments({is_labeled: false})

# View predictions
db.predictions.find().limit(5)
```

### Neo4j Queries

```bash
# Open Neo4j Browser at http://localhost:7474
# Or use cypher-shell:
docker compose exec neo4j cypher-shell -u neo4j -p password123

# Count proteins
MATCH (p:Protein) RETURN count(p);

# Find protein by ID
MATCH (p:Protein {id: "A0A087X1C5"}) RETURN p;

# Get protein and neighbors
MATCH (p:Protein {id: "A0A087X1C5"})-[r:SIMILAR_TO]-(n)
RETURN p, r, n
LIMIT 50;

# Find most connected proteins
MATCH (p:Protein)-[r]-()
WITH p, count(r) as degree
RETURN p.id, p.name, degree
ORDER BY degree DESC
LIMIT 10;

# Count isolated proteins
MATCH (p:Protein)
WHERE NOT (p)-[:SIMILAR_TO]-()
RETURN count(p);
```

## Configuration

### Environment Variables

Create a `.env` file or set these in `docker-compose.yml`:

```bash
# MongoDB Configuration
MONGO_URI=mongodb://root:password123@mongodb:27017/
MONGO_DB_NAME=protein_db

# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

# Graph Builder Parameters
SIMILARITY_THRESHOLD=0.1      # Minimum Jaccard similarity for edges
PROTEIN_LIMIT=                # Leave empty for all proteins
CLEAR_GRAPH=false            # Set to 'true' to rebuild from scratch

# Label Propagation Parameters
CONFIDENCE_THRESHOLD=0.3      # Minimum confidence for predictions
MIN_EDGE_WEIGHT=0.1          # Minimum edge weight to consider
MAX_LABELS_PER_PROTEIN=5     # Maximum EC numbers to assign

# Data Directory
DATA_DIR=/app/data           # Path to TSV files
```

### Testing with Small Dataset

For testing, limit the number of proteins:

```bash
# Build graph with only 1000 proteins (much faster)
docker compose exec python python -c "
import os
os.environ['PROTEIN_LIMIT'] = '1000'
os.environ['SIMILARITY_THRESHOLD'] = '0.2'
exec(open('src/graph_builder.py').read())
"

# Run label propagation on small graph
docker compose exec python python -c "
import os
os.environ['CONFIDENCE_THRESHOLD'] = '0.4'
exec(open('src/label_propagation.py').read())
"
```

## Project Tasks

### Task 1: MongoDB Document Store ✅

**Implementation**: `src/data_loader.py`  
**Documentation**: `doc/TASK1_MONGODB.md`

- Loads protein data from TSV files
- Creates structured documents with searchable fields
- Supports complex queries across protein attributes
- Indexed for fast lookups

### Task 2: Graph Construction ✅

**Implementation**: `src/graph_builder.py`  
**Documentation**: `doc/TASK2_GRAPH_CONSTRUCTION.md`

- Builds domain-based protein-protein network
- Uses Jaccard similarity coefficient
- Creates weighted undirected graph
- Efficient batch processing

### Task 3: Query APIs ✅

**Implementation**: `src/app.py`  
**Documentation**: `doc/TASK3_API_QUERIES.md`

- REST API with 15+ endpoints
- MongoDB search and retrieval
- Neo4j graph queries
- Statistics computation
- Visualization data

### Task 4: Label Propagation ✅

**Implementation**: `src/label_propagation.py`  
**Documentation**: `doc/TASK4_LABEL_PROPAGATION.md`

- Weighted label propagation algorithm
- Multi-label classification
- Confidence scores
- Predicts EC numbers for unlabeled proteins

## Documentation

Comprehensive documentation available in the `doc/` folder:

| Document | Description |
|----------|-------------|
| `TASK1_MONGODB.md` | MongoDB implementation details |
| `TASK2_GRAPH_CONSTRUCTION.md` | Graph building algorithm |
| `TASK3_API_QUERIES.md` | Complete API reference |
| `TASK4_LABEL_PROPAGATION.md` | Label propagation algorithm |
| `PROJECT_SUMMARY.md` | Complete project overview |

## API Endpoints

### MongoDB Endpoints

- `GET /api/mongodb/search?q=term` - Search proteins
- `GET /api/mongodb/protein/:id` - Get protein by ID
- `GET /api/mongodb/statistics` - Database statistics

### Neo4j Endpoints

- `GET /api/neo4j/protein/:id` - Get protein node
- `GET /api/neo4j/neighbors/:id` - Get neighbors
- `GET /api/neo4j/neighborhood/:id` - Get visualization data
- `GET /api/neo4j/search?q=term` - Search in graph
- `GET /api/neo4j/statistics` - Graph statistics

### Combined Endpoints

- `GET /health` - System health check
- `GET /api/statistics/overview` - Combined statistics
- `GET /api/predictions/:id` - Get prediction for protein
- `GET /api/predictions/statistics` - Prediction statistics

## Troubleshooting

### Services not starting

```bash
# Check Docker is running
docker ps

# Check service logs
docker compose logs mongodb
docker compose logs neo4j
docker compose logs python

# Restart services
docker compose restart
```

### Connection errors

```bash
# Test MongoDB connection
docker compose exec mongodb mongosh -u root -p password123

# Test Neo4j connection
docker compose exec neo4j cypher-shell -u neo4j -p password123

# Test API
curl http://localhost:5000/health
```

### Out of memory

```bash
# Reduce dataset size
export PROTEIN_LIMIT=1000

# Or increase Docker memory in Docker Desktop settings
# Recommended: 8GB RAM minimum
```

### Python package errors

```bash
# Rebuild Python container
docker compose build --no-cache python
docker compose up -d python
```

## Performance Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| Data Loading | ~5 min | 50,000 proteins |
| Graph Building | ~2 hours | 48,500 nodes, 250K edges |
| Label Propagation | ~10 min | 25,000 predictions |
| API Query (simple) | <50 ms | By ID |
| API Query (neighborhood) | 100-500 ms | Depth 1-2 |

## Development

### Adding new features

1. Create new Python module in `src/`
2. Update database clients if needed
3. Add API endpoints in `app.py`
4. Document in `doc/` folder

### Testing

```bash
# Run full workflow with small dataset
./test.sh

# Or manually:
docker compose exec python python -c "
import os
os.environ['PROTEIN_LIMIT'] = '100'
# ... run scripts
"
```

## License

This project is for educational purposes as part of the NoSQL course.

## Support

For questions:
1. Check documentation in `doc/` folder
2. Review code comments
3. Test with small datasets
4. Check Docker logs

## Acknowledgments

- UniProt for protein data
- MongoDB and Neo4j communities
- Flask framework
- Docker for containerization

---

**Last Updated**: December 2025  
**Version**: 1.0  
**Status**: Complete ✅

4. **Access the services**:
   - MongoDB: Accessible at `mongodb://localhost:27017`
   - Neo4j: Accessible at `http://localhost:7474`
   - Python application: Accessible as defined in the `docker-compose.yml`

## Environment Variables

Refer to the `.env.example` file for the required environment variables. Copy this file to `.env` and fill in the necessary values.

## Additional Information

For more details on the project objectives and requirements, please refer to `subject.md` and `task.md`.