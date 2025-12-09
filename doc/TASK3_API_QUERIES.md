# Task 3: Querying the Protein Databases

## Overview

This task implements a comprehensive REST API for querying both MongoDB (document store) and Neo4j (graph database). The API provides endpoints for searching proteins, viewing neighborhoods, computing statistics, and preparing data for visualization.

## API Architecture

### Technology Stack

- **Flask**: Lightweight Python web framework
- **Flask-CORS**: Cross-Origin Resource Sharing support
- **MongoDB Client**: Document queries
- **Neo4j Client**: Graph queries

### Endpoint Categories

1. **MongoDB Queries**: Document-based search and retrieval
2. **Neo4j Queries**: Graph-based navigation and neighborhood queries
3. **Statistics**: Comprehensive analytics from both databases
4. **Visualization**: Data formatted for graph visualization libraries

## MongoDB Endpoints (Task 3.1)

### 1. Search Proteins

**Endpoint**: `GET /api/mongodb/search`

**Description**: Search proteins by identifier, name, or description using regex matching.

**Query Parameters**:
- `q` (required): Search term
- `limit` (optional): Maximum results (default: 50)

**Example Request**:
```bash
curl "http://localhost:5000/api/mongodb/search?q=cytochrome&limit=10"
```

**Example Response**:
```json
{
  "query": "cytochrome",
  "count": 10,
  "limit": 10,
  "results": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "identifier": "A0A087X1C5",
      "entry_name": "CP2D7_HUMAN",
      "name": "Putative cytochrome P450 2D7",
      "organism": "Homo sapiens (Human)",
      "sequence": "MGLEALVPLAMIVAIFLLLVD...",
      "ec_numbers": ["1.14.14.1"],
      "interpro_domains": ["IPR001128", "IPR017972", "IPR002401"],
      "is_labeled": true,
      "sequence_length": 497
    }
  ]
}
```

### 2. Get Protein by ID

**Endpoint**: `GET /api/mongodb/protein/:id`

**Description**: Retrieve complete protein document by identifier.

**Path Parameters**:
- `id`: Protein identifier (e.g., A0A087X1C5)

**Example Request**:
```bash
curl "http://localhost:5000/api/mongodb/protein/A0A087X1C5"
```

**Example Response**:
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "identifier": "A0A087X1C5",
  "entry_name": "CP2D7_HUMAN",
  "name": "Putative cytochrome P450 2D7",
  "organism": "Homo sapiens (Human)",
  "sequence": "MGLEALVPLAMIVAIFLLLVD...",
  "ec_numbers": ["1.14.14.1"],
  "interpro_domains": ["IPR001128", "IPR017972"],
  "is_labeled": true,
  "sequence_length": 497
}
```

### 3. MongoDB Statistics

**Endpoint**: `GET /api/mongodb/statistics`

**Description**: Get comprehensive MongoDB database statistics.

**Example Request**:
```bash
curl "http://localhost:5000/api/mongodb/statistics"
```

**Example Response**:
```json
{
  "total_proteins": 50000,
  "labeled_proteins": 12500,
  "unlabeled_proteins": 37500,
  "labeled_percentage": 25.0,
  "average_sequence_length": 485.67,
  "top_ec_numbers": [
    {"ec_number": "1.14.14.1", "count": 250},
    {"ec_number": "2.7.11.1", "count": 180}
  ],
  "top_domains": [
    {"domain": "IPR001128", "count": 1500},
    {"domain": "IPR017972", "count": 1200}
  ]
}
```

## Neo4j Endpoints (Task 3.2)

### 1. Get Protein Node

**Endpoint**: `GET /api/neo4j/protein/:id`

**Description**: Retrieve protein node from graph database.

**Path Parameters**:
- `id`: Protein identifier

**Example Request**:
```bash
curl "http://localhost:5000/api/neo4j/protein/A0A087X1C5"
```

**Example Response**:
```json
{
  "id": "A0A087X1C5",
  "entry_name": "CP2D7_HUMAN",
  "name": "Putative cytochrome P450 2D7",
  "organism": "Homo sapiens (Human)",
  "is_labeled": true,
  "ec_numbers": ["1.14.14.1"],
  "interpro_domains": ["IPR001128", "IPR017972"],
  "sequence_length": 497
}
```

### 2. Get Neighbors

**Endpoint**: `GET /api/neo4j/neighbors/:id`

**Description**: Get protein neighbors in the graph (direct neighbors and neighbors of neighbors).

**Path Parameters**:
- `id`: Protein identifier

**Query Parameters**:
- `depth` (optional): Neighborhood depth (1 or 2, default: 1)
- `min_weight` (optional): Minimum edge weight (default: 0.0)
- `limit` (optional): Maximum neighbors (default: 50)

**Example Request**:
```bash
curl "http://localhost:5000/api/neo4j/neighbors/A0A087X1C5?depth=2&min_weight=0.2&limit=20"
```

**Example Response**:
```json
{
  "protein": {
    "id": "A0A087X1C5",
    "name": "Putative cytochrome P450 2D7",
    "is_labeled": true
  },
  "neighbors": [
    {
      "protein": {
        "id": "A0A0B4J2F0",
        "name": "Protein PIGBOS1",
        "is_labeled": false
      },
      "weight": 0.45,
      "distance": 1
    },
    {
      "protein": {
        "id": "A0A0B4J2F2",
        "name": "Putative serine/threonine-protein kinase SIK1B",
        "is_labeled": true
      },
      "weight": 0.32,
      "distance": 2
    }
  ],
  "depth": 2,
  "count": 20
}
```

### 3. Get Neighborhood (Visualization)

**Endpoint**: `GET /api/neo4j/neighborhood/:id`

**Description**: Get full neighborhood data formatted for graph visualization libraries (nodes and edges).

**Path Parameters**:
- `id`: Protein identifier

**Query Parameters**:
- `depth` (optional): Neighborhood depth (default: 2)
- `min_weight` (optional): Minimum edge weight (default: 0.1)
- `limit` (optional): Maximum nodes (default: 100)

**Example Request**:
```bash
curl "http://localhost:5000/api/neo4j/neighborhood/A0A087X1C5?depth=2&min_weight=0.2"
```

**Example Response**:
```json
{
  "nodes": [
    {
      "id": "A0A087X1C5",
      "name": "Putative cytochrome P450 2D7",
      "is_labeled": true,
      "is_center": true,
      "label_type": "labeled"
    },
    {
      "id": "A0A0B4J2F0",
      "name": "Protein PIGBOS1",
      "is_labeled": false,
      "is_center": false,
      "label_type": "unlabeled"
    }
  ],
  "edges": [
    {
      "source": "A0A087X1C5",
      "target": "A0A0B4J2F0",
      "weight": 0.45
    }
  ],
  "center_id": "A0A087X1C5",
  "node_count": 25,
  "edge_count": 38
}
```

### 4. Search in Graph

**Endpoint**: `GET /api/neo4j/search`

**Description**: Search proteins in Neo4j by identifier or name.

**Query Parameters**:
- `q` (required): Search term
- `limit` (optional): Maximum results (default: 50)

**Example Request**:
```bash
curl "http://localhost:5000/api/neo4j/search?q=cytochrome&limit=10"
```

### 5. Graph Statistics (Task 3.3)

**Endpoint**: `GET /api/neo4j/statistics`

**Description**: Get comprehensive graph statistics including isolated proteins.

**Example Request**:
```bash
curl "http://localhost:5000/api/neo4j/statistics"
```

**Example Response**:
```json
{
  "total_proteins": 50000,
  "labeled_proteins": 12500,
  "unlabeled_proteins": 37500,
  "labeled_percentage": 25.0,
  "total_edges": 250000,
  "isolated_proteins": 150,
  "isolated_percentage": 0.3,
  "average_degree": 10.0,
  "top_connected_proteins": [
    {
      "protein_id": "P12345",
      "protein_name": "Highly connected protein",
      "degree": 250
    }
  ]
}
```

## Combined Statistics Endpoint (Task 3.3)

### Overview Statistics

**Endpoint**: `GET /api/statistics/overview`

**Description**: Get comprehensive statistics from both MongoDB and Neo4j.

**Example Request**:
```bash
curl "http://localhost:5000/api/statistics/overview"
```

**Example Response**:
```json
{
  "mongodb": {
    "total_proteins": 50000,
    "labeled_proteins": 12500,
    "unlabeled_proteins": 37500,
    "labeled_percentage": 25.0,
    "average_sequence_length": 485.67,
    "top_ec_numbers": [...],
    "top_domains": [...]
  },
  "neo4j": {
    "total_proteins": 48500,
    "labeled_proteins": 12500,
    "unlabeled_proteins": 36000,
    "labeled_percentage": 25.77,
    "total_edges": 250000,
    "isolated_proteins": 150,
    "isolated_percentage": 0.31,
    "average_degree": 10.31,
    "top_connected_proteins": [...]
  },
  "system": {
    "status": "operational",
    "mongodb_connected": true,
    "neo4j_connected": true
  }
}
```

## Health Check

**Endpoint**: `GET /health`

**Description**: Check database connectivity.

**Example Request**:
```bash
curl "http://localhost:5000/health"
```

**Example Response**:
```json
{
  "status": "running",
  "mongodb": true,
  "neo4j": true
}
```

## Usage Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:5000"

# Search for proteins
response = requests.get(f"{BASE_URL}/api/mongodb/search", params={"q": "cytochrome", "limit": 10})
proteins = response.json()

# Get protein details
protein_id = proteins['results'][0]['identifier']
response = requests.get(f"{BASE_URL}/api/mongodb/protein/{protein_id}")
protein = response.json()

# Get protein neighbors
response = requests.get(f"{BASE_URL}/api/neo4j/neighbors/{protein_id}", 
                       params={"depth": 2, "min_weight": 0.2})
neighbors = response.json()

# Get visualization data
response = requests.get(f"{BASE_URL}/api/neo4j/neighborhood/{protein_id}",
                       params={"depth": 2, "min_weight": 0.1, "limit": 100})
viz_data = response.json()

# Get statistics
response = requests.get(f"{BASE_URL}/api/statistics/overview")
stats = response.json()
```

### JavaScript/Frontend

```javascript
// Search proteins
const searchProteins = async (query) => {
  const response = await fetch(
    `http://localhost:5000/api/mongodb/search?q=${query}&limit=10`
  );
  return await response.json();
};

// Get neighborhood for visualization
const getNeighborhood = async (proteinId) => {
  const response = await fetch(
    `http://localhost:5000/api/neo4j/neighborhood/${proteinId}?depth=2&min_weight=0.1`
  );
  return await response.json();
};

// Get statistics
const getStatistics = async () => {
  const response = await fetch('http://localhost:5000/api/statistics/overview');
  return await response.json();
};
```

### cURL Examples

```bash
# Search in MongoDB
curl "http://localhost:5000/api/mongodb/search?q=kinase&limit=5"

# Get protein by ID
curl "http://localhost:5000/api/mongodb/protein/A0A087X1C5"

# Get neighbors in graph
curl "http://localhost:5000/api/neo4j/neighbors/A0A087X1C5?depth=1&min_weight=0.3"

# Get visualization data
curl "http://localhost:5000/api/neo4j/neighborhood/A0A087X1C5?depth=2&min_weight=0.2&limit=50"

# Get combined statistics
curl "http://localhost:5000/api/statistics/overview"

# Search in graph
curl "http://localhost:5000/api/neo4j/search?q=cytochrome"
```

## Running the API

### Start the Flask Server

```bash
# Using Docker
docker compose up -d

# The API will be available at http://localhost:5000
```

### Access the API Documentation

Open in browser: `http://localhost:5000`

This displays an interactive HTML page with all available endpoints.

## Implementation Details

### MongoDB Queries

The MongoDB client uses:
- **Regex searches**: Case-insensitive pattern matching
- **Aggregation pipelines**: For statistics and distributions
- **Indexes**: On identifier, entry_name, is_labeled for fast queries

### Neo4j Queries

The Neo4j client uses:
- **Cypher queries**: Graph pattern matching
- **Variable-length paths**: For depth-based navigation
- **Aggregations**: For statistics and degree calculations
- **Indexes**: On protein ID and labeled status

### Error Handling

All endpoints include:
- Input validation
- Try-catch error handling
- Appropriate HTTP status codes (200, 400, 404, 500)
- JSON error responses

### CORS Support

The API includes CORS headers, allowing frontend applications on different domains to access the API.

## Performance Considerations

### Optimization Strategies

1. **Limit Results**: Default limits prevent overwhelming responses
2. **Indexed Queries**: All searchable fields are indexed
3. **Batch Processing**: Efficient data retrieval
4. **Caching**: Can add Redis for frequently accessed data

### Query Complexity

- **Simple queries** (by ID): < 10ms
- **Search queries**: 10-100ms depending on result size
- **Neighborhood queries** (depth 1): 50-200ms
- **Neighborhood queries** (depth 2): 200-1000ms
- **Statistics**: 100-500ms (includes aggregations)

## Next Steps

Task 3 enables:
- **Task 4**: Use neighbor data for label propagation
- **Visualization**: Display protein networks in frontend
- **Analytics**: Build dashboards with statistics
- **Advanced Queries**: Add more specialized endpoints

## Testing

```bash
# Start services
docker compose up -d

# Wait for services to be ready
sleep 10

# Test health
curl http://localhost:5000/health

# Test MongoDB search
curl "http://localhost:5000/api/mongodb/search?q=protein&limit=5"

# Test Neo4j query
curl "http://localhost:5000/api/neo4j/statistics"

# Test combined statistics
curl "http://localhost:5000/api/statistics/overview"
```

## Troubleshooting

### Connection Issues

```bash
# Check if containers are running
docker ps

# Check MongoDB connection
docker exec -it protein_mongodb mongosh -u root -p password123

# Check Neo4j connection
docker exec -it protein_neo4j cypher-shell -u neo4j -p password123
```

### API Not Responding

```bash
# Check container logs
docker logs protein_python_app

# Restart the Python container
docker compose restart python
```
