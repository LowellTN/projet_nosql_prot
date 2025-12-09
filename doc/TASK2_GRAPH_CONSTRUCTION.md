# Task 2: Big Graph Construction - Protein-Protein Network

## Overview

This task implements domain-based protein-protein network (PPN) construction in Neo4j. The graph connects proteins that share similar domain compositions using the **Jaccard similarity coefficient** as the edge weight.

## Theoretical Background

### Domain-Based Similarity

Protein domains are functional and structural units that are conserved through evolution. Proteins with similar domain compositions often share functional relationships. The domain-based approach:

1. Represents each protein as a set of InterPro domain IDs
2. Calculates similarity between protein pairs based on shared domains
3. Creates weighted edges representing the strength of similarity

### Jaccard Similarity Coefficient

The Jaccard index measures similarity between two sets:

```
J(A,B) = |A ∩ B| / |A ∪ B|
```

Where:
- `A ∩ B` is the intersection (common elements)
- `A ∪ B` is the union (all unique elements)
- Result ranges from 0 (no similarity) to 1 (identical)

### Example Calculation

Given two proteins:
- **P1** with domains: `{d1, d2, d3, d4}`
- **P2** with domains: `{d1, d3, d5}`

**Raw count approach** (not used):
```
Common domains = {d1, d3}
Weight = |{d1, d3}| = 2
```

**Jaccard coefficient** (used):
```
Intersection = {d1, d3} → size = 2
Union = {d1, d2, d3, d4, d5} → size = 5
Jaccard = 2/5 = 0.4
```

The Jaccard coefficient is preferred because it normalizes for protein size differences.

## Implementation Details

### Script: `graph_builder.py`

The graph builder implements the following workflow:

```
1. Load Proteins (MongoDB) → Proteins with domains
2. Create Nodes (Neo4j) → Protein nodes with attributes
3. Calculate Similarities → Jaccard coefficient for all pairs
4. Create Edges (Neo4j) → Weighted SIMILAR_TO relationships
```

### Graph Structure

#### Node Properties

Each `Protein` node contains:

```cypher
(:Protein {
  id: "A0A087X1C5",              // Unique identifier
  entry_name: "CP2D7_HUMAN",     // Entry name
  name: "Putative cytochrome...", // Full protein name
  organism: "Homo sapiens",      // Species
  is_labeled: true,              // Has EC numbers?
  ec_numbers: ["1.14.14.1"],    // Enzyme classifications
  interpro_domains: ["IPR001128", "IPR017972", ...], // Domain IDs
  sequence_length: 497           // Sequence length
})
```

#### Edge Properties

Each `SIMILAR_TO` relationship contains:

```cypher
(:Protein)-[:SIMILAR_TO {weight: 0.4}]-(:Protein)
```

Where `weight` is the Jaccard coefficient (0.0 to 1.0).

### Key Features

1. **Similarity Threshold**: Only creates edges above a minimum similarity (default: 0.1)
2. **Batch Processing**: Efficient bulk creation of nodes and edges
3. **Undirected Graph**: Edges created in both directions for easier queries
4. **Labeled/Unlabeled Nodes**: Tracks annotation status for label propagation
5. **Progress Tracking**: Shows progress for long-running graph construction

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SIMILARITY_THRESHOLD` | 0.1 | Minimum Jaccard similarity to create edge |
| `PROTEIN_LIMIT` | None | Maximum proteins to process (for testing) |
| `CLEAR_GRAPH` | false | Delete existing graph before building |

## Usage

### Inside Docker Container

```bash
# Build and start containers
docker compose up -d

# Load data into MongoDB first
docker compose exec python python src/data_loader.py

# Build the graph with default settings
docker compose exec python python src/graph_builder.py

# Build with custom threshold (only edges with similarity >= 0.2)
docker compose exec python python -c "
import os
os.environ['SIMILARITY_THRESHOLD'] = '0.2'
exec(open('src/graph_builder.py').read())
"

# Build with limited proteins (for testing)
docker compose exec python python -c "
import os
os.environ['PROTEIN_LIMIT'] = '1000'
exec(open('src/graph_builder.py').read())
"
```

### Environment Variables

```bash
# MongoDB connection
MONGO_URI=mongodb://root:password123@mongodb:27017/
MONGO_DB_NAME=protein_db

# Neo4j connection
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

# Graph builder configuration
SIMILARITY_THRESHOLD=0.1
PROTEIN_LIMIT=  # Leave empty for all proteins
CLEAR_GRAPH=false
```

## Algorithm Complexity

### Time Complexity

For N proteins:
- **Node Creation**: O(N) - linear
- **Pairwise Comparison**: O(N²) - quadratic
- **Edge Creation**: O(E) where E is number of edges above threshold

**Total**: O(N²) dominated by similarity calculations

### Space Complexity

- **Nodes**: O(N)
- **Edges**: O(N²) in worst case (all pairs similar)
- **Typical**: O(N * k) where k is average number of similar neighbors

### Optimization Strategies

1. **Similarity Threshold**: Reduces edge count significantly
2. **Batch Processing**: Reduces database round-trips
3. **Domain Set Caching**: Fast intersection/union operations
4. **Index Creation**: Faster node lookups during edge creation

## Output Statistics

The builder provides detailed statistics:

```
GRAPH CONSTRUCTION STATISTICS
============================================================
Proteins loaded:        50,000
Nodes created:          50,000
  - Labeled:            12,500
  - Unlabeled:          37,500
Edges created:          250,000
Comparisons made:       1,249,975,000
Similarity threshold:   0.1
Average node degree:    10.0
============================================================
```

### Metrics Explained

- **Proteins loaded**: Proteins with at least one domain
- **Nodes created**: Protein nodes in Neo4j
- **Labeled/Unlabeled**: Proteins with/without EC numbers
- **Edges created**: Similarity relationships above threshold
- **Comparisons made**: Total protein pairs compared
- **Average node degree**: Mean number of neighbors per protein

## Neo4j Queries

### Basic Graph Queries

```cypher
// Count all proteins
MATCH (p:Protein)
RETURN count(p)

// Count labeled vs unlabeled
MATCH (p:Protein)
RETURN p.is_labeled, count(p)

// Find protein and neighbors
MATCH (p:Protein {id: "A0A087X1C5"})-[r:SIMILAR_TO]-(neighbor)
RETURN p, r, neighbor

// Find proteins with highest connectivity
MATCH (p:Protein)-[r:SIMILAR_TO]-()
RETURN p.id, p.name, count(r) as degree
ORDER BY degree DESC
LIMIT 10

// Find isolated proteins (no neighbors)
MATCH (p:Protein)
WHERE NOT (p)-[:SIMILAR_TO]-()
RETURN count(p)

// Find proteins similar to a specific protein
MATCH (p:Protein {id: "A0A087X1C5"})-[r:SIMILAR_TO]-(neighbor)
WHERE r.weight >= 0.3
RETURN neighbor.id, neighbor.name, r.weight
ORDER BY r.weight DESC
LIMIT 20
```

### Advanced Queries

```cypher
// Find common neighbors (proteins similar to both)
MATCH (p1:Protein {id: "A0A087X1C5"})-[:SIMILAR_TO]-(common)
MATCH (p2:Protein {id: "A0A0B4J2F0"})-[:SIMILAR_TO]-(common)
RETURN common

// Find shortest path between two proteins
MATCH path = shortestPath(
  (p1:Protein {id: "A0A087X1C5"})-[:SIMILAR_TO*]-(p2:Protein {id: "A0A0B4J2F0"})
)
RETURN path

// Community detection - find densely connected proteins
CALL gds.louvain.stream('myGraph')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).id AS proteinId, communityId
ORDER BY communityId
```

## Graph Properties

### Undirected Weighted Graph

- **Undirected**: If A is similar to B, then B is similar to A
- **Weighted**: Edge weights represent degree of similarity
- **Connected Components**: May have multiple disconnected subgraphs
- **Labeled/Unlabeled**: Mixed node types for label propagation

### Expected Characteristics

- **Power-law degree distribution**: Few highly connected hub proteins
- **Small-world property**: Short paths between most protein pairs
- **Community structure**: Clusters of functionally related proteins
- **Sparse connectivity**: Most protein pairs are not directly connected

## Design Decisions

### Why Neo4j?

1. **Native Graph Storage**: Optimized for relationship queries
2. **Cypher Query Language**: Expressive graph pattern matching
3. **Graph Algorithms**: Built-in algorithms for analysis
4. **Scalability**: Handles large graphs efficiently
5. **Visualization**: Integration with visualization tools (Neovis, etc.)

### Similarity Threshold Choice

The default threshold of 0.1 (10% Jaccard similarity) is chosen to:
- Balance graph connectivity vs sparsity
- Keep only meaningful relationships
- Reduce computational and storage requirements
- Can be adjusted based on specific requirements

### Domain-Based vs Sequence-Based

**Domain-based approach** (used):
- ✓ Faster computation
- ✓ Captures functional similarity
- ✓ Robust to sequence variations
- ✓ Natural building blocks of proteins

**Sequence-based approach** (not used):
- ✗ Computationally expensive (sequence alignment)
- ✗ May miss functional similarity due to sequence divergence
- ✓ More granular similarity measure

## Verification

### Check Graph in Neo4j Browser

1. Open Neo4j Browser: http://localhost:7474
2. Login with credentials (neo4j / password123)
3. Run queries:

```cypher
// Overview
CALL db.schema.visualization()

// Sample proteins
MATCH (p:Protein)
RETURN p
LIMIT 25

// Sample network
MATCH path = (p:Protein)-[r:SIMILAR_TO]-(neighbor)
WHERE p.id = "A0A087X1C5"
RETURN path
LIMIT 50
```

## Performance Considerations

### For Large Datasets

With 50,000 proteins:
- **Comparisons**: 1.25 billion pairs
- **Time**: Several hours depending on hardware
- **Memory**: Requires adequate RAM for domain set operations

### Optimization Tips

1. **Start Small**: Test with `PROTEIN_LIMIT=1000`
2. **Adjust Threshold**: Higher threshold = fewer edges = faster
3. **Batch Size**: Larger batches = fewer transactions
4. **Hardware**: Use machine with good CPU and RAM

## Next Steps

Task 2 enables:
- Task 3: Query the graph for protein neighborhoods
- Task 4: Label propagation using graph structure
- Visualization: Display protein networks
- Analysis: Community detection, centrality measures

## Testing

```bash
# Start services
docker compose up -d

# Quick test with 100 proteins
docker compose exec python python -c "
import os
os.environ['PROTEIN_LIMIT'] = '100'
os.environ['SIMILARITY_THRESHOLD'] = '0.2'
os.environ['CLEAR_GRAPH'] = 'true'
exec(open('src/graph_builder.py').read())
"

# Verify in Neo4j
docker compose exec python python -c "
from database.neo4j_client import Neo4jClient
import os
client = Neo4jClient(
    os.getenv('NEO4J_URI'), 
    os.getenv('NEO4J_USERNAME'), 
    os.getenv('NEO4J_PASSWORD')
)
with client.driver.session() as session:
    result = session.run('MATCH (p:Protein) RETURN count(p) as count')
    print('Total proteins:', result.single()['count'])
client.close()
"
```
