# Task 1: Document Store for Protein Data

## Overview

This task implements a MongoDB-based document store for protein data from UniProt. MongoDB was chosen as the document database because it provides excellent support for complex querying and flexible schema design, which is essential for protein data with varying attributes.

## Implementation Details

### Data Structure

Each protein document in MongoDB contains the following fields:

```javascript
{
  identifier: "A0A087X1C5",           // UniProt entry ID (indexed, unique)
  entry_name: "CP2D7_HUMAN",          // Entry name (indexed)
  name: "Putative cytochrome P450...", // Full protein name
  organism: "Homo sapiens (Human)",   // Species
  sequence: "MGLEALVPLAMIVAIFLLLV...", // Amino acid sequence
  ec_numbers: ["1.14.14.1"],         // EC enzyme classification (indexed)
  interpro_domains: [                 // Protein domains/signatures (indexed)
    "IPR001128",
    "IPR017972",
    "IPR002401"
  ],
  is_labeled: true,                   // Has EC numbers? (indexed)
  sequence_length: 497                // Length of sequence
}
```

### Key Features

1. **Flexible Document Structure**: Each protein can have varying numbers of EC numbers and InterPro domains
2. **Searchable Fields**: Indexed fields for fast queries on identifier, name, and domains
3. **Labeled/Unlabeled Tracking**: Boolean flag to quickly identify annotated vs. unannotated proteins
4. **Batch Processing**: Efficient loading with batch inserts (1000 documents at a time)

### Database Indexes

The following indexes are created for optimal query performance:

- `identifier` (unique): Primary key for protein lookup
- `entry_name`: Secondary identifier lookup
- `is_labeled`: Fast filtering of labeled/unlabeled proteins
- `ec_numbers`: Search by enzyme classification
- `interpro_domains`: Search by protein domains

## Data Loading Process

### Script: `data_loader.py`

The data loader script processes UniProt TSV files and populates MongoDB:

1. **Connection**: Establishes connection to MongoDB
2. **Index Creation**: Creates necessary indexes before loading
3. **File Processing**: Reads TSV files with tab-separated values
4. **Document Creation**: Parses each row and creates structured documents
5. **Batch Insertion**: Inserts documents in batches for efficiency
6. **Statistics**: Reports loading progress and final statistics

### Usage

```bash
# Run inside the Python container
docker-compose exec python python src/data_loader.py
```

### Output Statistics

The loader provides detailed statistics:
- Total rows processed
- Total proteins inserted
- Proteins with EC numbers (labeled)
- Proteins with InterPro domains
- Errors encountered
- Percentage breakdowns

## Query Capabilities

The MongoDB document store supports complex queries:

### 1. Search by Identifier
```python
db.proteins.find({ "identifier": "A0A087X1C5" })
```

### 2. Search by Name (partial match)
```python
db.proteins.find({ 
  "name": { "$regex": "cytochrome", "$options": "i" }
})
```

### 3. Find Labeled Proteins
```python
db.proteins.find({ "is_labeled": true })
```

### 4. Search by EC Number
```python
db.proteins.find({ "ec_numbers": "1.14.14.1" })
```

### 5. Search by Domain
```python
db.proteins.find({ "interpro_domains": "IPR001128" })
```

### 6. Combined Search (identifier OR name OR description)
```python
db.proteins.find({
  "$or": [
    { "identifier": { "$regex": "search_term", "$options": "i" }},
    { "name": { "$regex": "search_term", "$options": "i" }},
    { "entry_name": { "$regex": "search_term", "$options": "i" }}
  ]
})
```

## Data Files

The project uses two UniProt TSV files:

1. **Human proteins**: `uniprot-compressed_true_download_true_fields_accession_2Cid_2Cprotei-2022.11.14-07.52.02.48.tsv`
2. **Mouse proteins**: `uniprotkb_AND_model_organism_10090_2025_11_14.tsv`

### File Structure

Each TSV file contains columns:
- Entry: Protein identifier
- Entry Name: Entry name
- Protein names: Full protein name/description
- Organism: Species information
- Sequence: Amino acid sequence
- EC number: Enzyme classification (semicolon-separated)
- InterPro: Domain identifiers (semicolon-separated)

## Design Decisions

### Why MongoDB?

1. **Flexible Schema**: Proteins have varying numbers of domains and EC numbers
2. **Rich Queries**: Support for complex search patterns with regex and array queries
3. **Document Model**: Natural fit for hierarchical protein data
4. **Indexing**: Efficient multi-field indexing for fast lookups
5. **Scalability**: Handles large datasets efficiently

### Data Normalization

The loader normalizes the data by:
- Splitting semicolon-separated values into arrays
- Creating a boolean `is_labeled` flag for quick filtering
- Computing sequence length for analytics
- Trimming whitespace from all fields

## Verification

After loading, the database can be verified:

```bash
# Connect to MongoDB
docker-compose exec mongodb mongosh -u root -p password123

# Switch to protein database
use protein_db

# Count total proteins
db.proteins.countDocuments({})

# Count labeled proteins
db.proteins.countDocuments({ is_labeled: true })

# Sample a protein
db.proteins.findOne()
```

## Performance Considerations

- **Batch Inserts**: Uses batch size of 1000 for optimal performance
- **Unordered Inserts**: Continues on duplicate key errors
- **Progress Updates**: Shows progress every 5000 proteins
- **Memory Efficient**: Processes files line-by-line

## Next Steps

Task 1 enables:
- Task 2: Extract domains for graph construction
- Task 3: Query API implementation
- Task 4: Label propagation using labeled/unlabeled distinction

## Testing

To test the MongoDB setup:

```bash
# Start services
docker-compose up -d

# Run data loader
docker-compose exec python python src/data_loader.py

# Query the database
docker-compose exec python python -c "
from database.mongodb_client import MongoDBClient
import os
client = MongoDBClient(os.getenv('MONGO_URI'), os.getenv('MONGO_DB_NAME'))
print('Total proteins:', client.proteins.count_documents({}))
client.close()
"
```
