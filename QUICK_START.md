# Quick Start Guide - Protein Analysis Platform

## 🚀 Getting Started in 5 Minutes

### 1. Start the System

```bash
cd projet_nosql_prot
docker compose up -d
```

Wait for all services to be healthy (~30 seconds).

### 2. Load Sample Data

```bash
# Download 50 human proteins (small test dataset)
wget -O data/uniprot_data.tsv 'https://rest.uniprot.org/uniprotkb/stream?format=tsv&query=reviewed:true+AND+organism_id:9606&fields=accession,id,protein_name,organism_name,sequence,ec,xref_interpro&size=50'

# Load into MongoDB
docker compose exec python python src/data_loader.py
```

### 3. Build the Graph

```bash
# Build protein similarity network
docker compose exec python python src/graph_builder.py
```

When prompted, select option **1** to clear existing graph and rebuild.

### 4. Run Predictions

```bash
# Predict EC numbers for unlabeled proteins
docker compose exec python python src/label_propagation.py
```

### 5. Open the Web Interface

🌐 **http://localhost:5000**

## 🎯 What to Explore

### Dashboard
- View overall statistics
- See top connected proteins
- Explore domain and EC number distributions

### Search
Try searching for:
- `kinase` - Find kinase proteins
- `cytochrome` - Find cytochrome proteins
- Protein IDs from your dataset

### Graph Explorer
1. Enter a protein ID (use IDs from "Top Connected Proteins" on dashboard)
2. Select depth (1-2 for small datasets)
3. Click "Load" to visualize the network
4. Click on nodes to explore neighbors

## 📊 Example Queries

### Using the Web Interface
1. Go to **Search** tab
2. Search for `kinase`
3. Click on any result to see details
4. Click "View in Graph" to visualize

### Using the API

```bash
# Get statistics
curl http://localhost:5000/api/statistics/overview

# Search proteins
curl "http://localhost:5000/api/mongodb/search?q=kinase"

# Get protein details
curl http://localhost:5000/api/mongodb/protein/YOUR_PROTEIN_ID

# Get neighbors
curl "http://localhost:5000/api/neo4j/neighbors/YOUR_PROTEIN_ID?depth=1"
```

### Using Neo4j Browser

1. Open http://localhost:7474
2. Login: `neo4j` / `password123`
3. Try these queries:

```cypher
// Count proteins
MATCH (p:Protein) RETURN count(p);

// Find most connected
MATCH (p:Protein)-[r]-()
WITH p, count(r) as degree
RETURN p.id, p.name, degree
ORDER BY degree DESC
LIMIT 10;

// Visualize a neighborhood
MATCH path = (p:Protein {id: "YOUR_ID"})-[:SIMILAR_TO*1..2]-(n)
RETURN path LIMIT 50;
```

## 🎨 Interface Features

### Color Coding
- 🟢 **Green** = Labeled proteins (have EC numbers)
- ⚪ **Gray** = Unlabeled proteins (predictions available)

### Graph Visualization
- **Node size** = Proportional to connections
- **Edge thickness** = Similarity strength (Jaccard coefficient)
- **Interactive** = Click nodes to view details

## 💡 Tips

1. **Start Small**: Use 50-100 proteins for testing
2. **Use Filters**: Set `min_weight=0.2` to see only strong connections
3. **Explore Predictions**: Check prediction confidence scores
4. **Check Neighbors**: Most proteins have 10-100 neighbors

## 🔧 Troubleshooting

### Services not starting?
```bash
docker compose down -v
docker compose up -d
```

### No data showing?
Check logs:
```bash
docker compose logs python
```

### Graph too large?
Reduce depth or increase min_weight filter.

## 📚 Next Steps

- Read [README.md](README.md) for detailed documentation
- Check [TASK3_API_QUERIES.md](doc/TASK3_API_QUERIES.md) for API reference
- Explore [TASK4_LABEL_PROPAGATION.md](doc/TASK4_LABEL_PROPAGATION.md) for ML details

---

**Need Help?** Check the logs: `docker compose logs -f python`
