# Task 4: Protein Function Annotation - Label Propagation

## Overview

This task implements a weighted label propagation algorithm to predict EC numbers (enzyme classifications) for unlabeled proteins based on the graph structure and labeled neighbors. This is a **multi-label classification problem** where each protein can have multiple functional annotations.

## Problem Definition

### Multi-Label Classification

- **Input**: Protein-protein network with labeled and unlabeled nodes
- **Labels**: EC numbers (enzyme classifications) like "1.14.14.1", "2.7.11.1"
- **Multi-label**: Each protein can have 0, 1, or multiple EC numbers
- **Goal**: Predict EC numbers for unlabeled proteins

### Graph-Based Approach

The algorithm leverages the **homophily principle**: similar proteins (connected in the graph) tend to have similar functions. Proteins with high domain similarity are likely to share EC numbers.

## Algorithm Description

### Weighted Label Propagation

The algorithm propagates labels from labeled neighbors to unlabeled proteins using weighted voting:

```
For each unlabeled protein p:
    For each labeled neighbor n with edge weight w:
        For each EC number ec in n:
            vote(ec) += w
    
    confidence(ec) = vote(ec) / sum(all_weights)
    
    Assign EC numbers with confidence >= threshold
```

### Mathematical Formulation

For an unlabeled protein $u$ with labeled neighbors $N(u)$:

**Confidence score** for EC number $ec$:

$$
\text{conf}(u, ec) = \frac{\sum_{v \in N(u), ec \in L(v)} W_{u,v}}{\sum_{v \in N(u)} W_{u,v}}
$$

Where:
- $N(u)$ = set of labeled neighbors
- $L(v)$ = set of EC numbers for neighbor $v$
- $W_{u,v}$ = Jaccard similarity (edge weight)

**Assignment rule**:

$$
\text{predicted}(u) = \{ec : \text{conf}(u, ec) \geq \theta\}
$$

Where $\theta$ is the confidence threshold (default: 0.3).

### Example

Consider an unlabeled protein **P1** with three labeled neighbors:

| Neighbor | EC Numbers | Edge Weight |
|----------|------------|-------------|
| P2 | [1.14.14.1, 2.7.11.1] | 0.6 |
| P3 | [1.14.14.1] | 0.4 |
| P4 | [3.1.3.16] | 0.2 |

**Calculation**:

Total weight = 0.6 + 0.4 + 0.2 = 1.2

- EC 1.14.14.1: vote = 0.6 + 0.4 = 1.0, confidence = 1.0/1.2 = **0.833**
- EC 2.7.11.1: vote = 0.6, confidence = 0.6/1.2 = **0.500**
- EC 3.1.3.16: vote = 0.2, confidence = 0.2/1.2 = **0.167**

With threshold = 0.3:
- **Assigned**: [1.14.14.1, 2.7.11.1]
- **Rejected**: [3.1.3.16] (below threshold)

## Implementation Details

### Script: `label_propagation.py`

The implementation includes:

1. **Label Collection**: Get EC numbers from labeled neighbors
2. **Weighted Voting**: Calculate confidence scores
3. **Threshold Filtering**: Keep labels above confidence threshold
4. **Ranking**: Select top N labels by confidence
5. **Storage**: Save predictions to MongoDB and Neo4j

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CONFIDENCE_THRESHOLD` | 0.3 | Minimum confidence to assign label |
| `MIN_EDGE_WEIGHT` | 0.1 | Minimum edge weight to consider |
| `MAX_LABELS_PER_PROTEIN` | 5 | Maximum EC numbers to assign |

### Algorithm Steps

```python
# 1. Find unlabeled proteins with labeled neighbors
unlabeled_proteins = get_unlabeled_with_labeled_neighbors()

# 2. For each unlabeled protein
for protein in unlabeled_proteins:
    # 3. Collect EC numbers from neighbors
    ec_votes = collect_weighted_votes(protein)
    
    # 4. Calculate confidence scores
    ec_confidence = normalize_votes(ec_votes)
    
    # 5. Filter by threshold
    filtered = filter_by_confidence(ec_confidence, threshold)
    
    # 6. Rank and select top N
    predictions = select_top_n(filtered, max_labels)
    
    # 7. Store predictions
    save_predictions(protein, predictions)
```

## Usage

### Run Label Propagation

```bash
# Inside Docker container
docker compose exec python python src/label_propagation.py

# With custom parameters
docker compose exec python python -c "
import os
os.environ['CONFIDENCE_THRESHOLD'] = '0.4'
os.environ['MIN_EDGE_WEIGHT'] = '0.2'
os.environ['MAX_LABELS_PER_PROTEIN'] = '3'
exec(open('src/label_propagation.py').read())
"
```

### Environment Variables

```bash
# Database connections
MONGO_URI=mongodb://root:password123@mongodb:27017/
MONGO_DB_NAME=protein_db
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

# Algorithm parameters
CONFIDENCE_THRESHOLD=0.3    # Minimum confidence (0.0 to 1.0)
MIN_EDGE_WEIGHT=0.1         # Minimum similarity to consider
MAX_LABELS_PER_PROTEIN=5    # Maximum EC numbers to assign
```

## Output

### Predictions Collection (MongoDB)

The algorithm creates a `predictions` collection in MongoDB:

```javascript
{
  "_id": ObjectId("..."),
  "protein_id": "A0A0B4J2F0",
  "predicted_ec_numbers": ["1.14.14.1", "2.7.11.1"],
  "confidence_scores": {
    "1.14.14.1": 0.833,
    "2.7.11.1": 0.500
  },
  "average_confidence": 0.667
}
```

### Neo4j Property Updates

Predictions are added to protein nodes:

```cypher
(:Protein {
  id: "A0A0B4J2F0",
  is_labeled: false,
  ec_numbers: [],  // Original (empty)
  predicted_ec_numbers: ["1.14.14.1", "2.7.11.1"],  // Predicted
  prediction_confidence: {
    "1.14.14.1": 0.833,
    "2.7.11.1": 0.500
  }
})
```

### Statistics Output

```
============================================================
LABEL PROPAGATION STATISTICS
============================================================
Proteins annotated:         25,000
Total labels propagated:    45,000
Avg labels per protein:     1.80
Average confidence:         0.567
============================================================
```

## Confidence Interpretation

### Confidence Scores

- **0.8 - 1.0**: High confidence - strong consensus among neighbors
- **0.5 - 0.8**: Medium confidence - majority of neighbors agree
- **0.3 - 0.5**: Low confidence - weak consensus
- **< 0.3**: Very low confidence - rejected by threshold

### Factors Affecting Confidence

1. **Number of neighbors**: More neighbors = more reliable
2. **Edge weights**: Higher similarity = stronger evidence
3. **Label consistency**: All neighbors with same EC = high confidence
4. **Label diversity**: Neighbors with different ECs = lower confidence

## Algorithm Variants

### Basic Label Propagation

Current implementation (weighted voting):
- ✓ Uses edge weights
- ✓ Supports multi-label
- ✓ One-shot propagation

### Iterative Label Propagation

Possible extension (not implemented):
- Propagate labels in multiple iterations
- Newly labeled proteins can propagate to their neighbors
- Continue until convergence

### Semi-Supervised Learning

Alternative approach:
- Use initial labels as training data
- Apply graph neural networks (GNN)
- Learn label patterns from graph structure

## Evaluation Metrics

### For Testing (Cross-Validation)

If we hide labels from known proteins:

**Precision**: 
$$
P = \frac{\text{Correct Predictions}}{\text{Total Predictions}}
$$

**Recall**:
$$
R = \frac{\text{Correct Predictions}}{\text{Total Actual Labels}}
$$

**F1 Score**:
$$
F_1 = 2 \cdot \frac{P \cdot R}{P + R}
$$

### Example Evaluation

```python
# Hide labels from 20% of proteins
test_proteins = sample_labeled_proteins(0.2)

# Remove their labels temporarily
remove_labels(test_proteins)

# Run label propagation
predictions = propagate_labels()

# Compare with actual labels
precision, recall, f1 = evaluate(predictions, test_proteins)
```

## Query Predictions

### MongoDB Queries

```javascript
// Get all predictions
db.predictions.find()

// Get predictions for specific protein
db.predictions.findOne({protein_id: "A0A0B4J2F0"})

// Get high-confidence predictions
db.predictions.find({average_confidence: {$gte: 0.7}})

// Get proteins with specific predicted EC
db.predictions.find({predicted_ec_numbers: "1.14.14.1"})

// Count predictions by confidence
db.predictions.aggregate([
  {$bucket: {
    groupBy: "$average_confidence",
    boundaries: [0, 0.3, 0.5, 0.7, 0.9, 1.0],
    default: "Other",
    output: {count: {$sum: 1}}
  }}
])
```

### Neo4j Queries

```cypher
// Find proteins with predictions
MATCH (p:Protein)
WHERE exists(p.predicted_ec_numbers)
RETURN p

// Find proteins with high-confidence predictions
MATCH (p:Protein)
WHERE exists(p.predicted_ec_numbers)
  AND any(ec IN keys(p.prediction_confidence) 
      WHERE p.prediction_confidence[ec] >= 0.7)
RETURN p

// Compare predicted vs actual (for labeled proteins)
MATCH (p:Protein)
WHERE p.is_labeled = true 
  AND exists(p.predicted_ec_numbers)
RETURN p.id, p.ec_numbers, p.predicted_ec_numbers

// Find unlabeled proteins now with predictions
MATCH (p:Protein)
WHERE p.is_labeled = false 
  AND exists(p.predicted_ec_numbers)
RETURN count(p)
```

## API Integration

### Add Prediction Endpoint to Flask

```python
@app.route('/api/predictions/<protein_id>')
def get_prediction(protein_id):
    """Get prediction for a protein."""
    pred = mongo_client.db['predictions'].find_one({'protein_id': protein_id})
    if pred:
        pred['_id'] = str(pred['_id'])
        return jsonify(pred)
    return jsonify({'error': 'No prediction found'}), 404

@app.route('/api/predictions/statistics')
def prediction_statistics():
    """Get prediction statistics."""
    total = mongo_client.db['predictions'].count_documents({})
    avg_conf = mongo_client.db['predictions'].aggregate([
        {'$group': {
            '_id': None,
            'avg_confidence': {'$avg': '$average_confidence'},
            'avg_labels': {'$avg': {'$size': '$predicted_ec_numbers'}}
        }}
    ]).next()
    
    return jsonify({
        'total_predictions': total,
        'average_confidence': avg_conf['avg_confidence'],
        'average_labels_per_protein': avg_conf['avg_labels']
    })
```

## Parameter Tuning

### Confidence Threshold

**Too low** (< 0.2):
- More predictions
- Lower quality
- More false positives

**Too high** (> 0.5):
- Fewer predictions
- Higher quality
- More false negatives

**Recommended**: 0.3 - 0.4

### Min Edge Weight

**Too low** (< 0.05):
- Consider weak similarities
- More noise
- Less reliable

**Too high** (> 0.3):
- Only strong similarities
- Fewer neighbors used
- May miss predictions

**Recommended**: 0.1 - 0.2

### Max Labels Per Protein

**Biological reality**: Most proteins have 1-3 EC numbers

**Recommended**: 3 - 5

## Advantages & Limitations

### Advantages

✓ **Simple and interpretable**: Easy to understand and explain  
✓ **No training required**: Works directly on graph structure  
✓ **Multi-label support**: Naturally handles multiple EC numbers  
✓ **Confidence scores**: Provides prediction reliability  
✓ **Fast**: Efficient for large graphs

### Limitations

✗ **Requires labeled neighbors**: Can't predict for isolated proteins  
✗ **One-hop propagation**: Doesn't propagate through unlabeled proteins  
✗ **No learning**: Doesn't discover new patterns  
✗ **Sensitive to parameters**: Threshold choice affects results  
✗ **No feature learning**: Only uses graph structure

## Future Improvements

### 1. Iterative Propagation

Propagate labels in multiple rounds, allowing newly labeled proteins to propagate to their neighbors.

### 2. Feature Integration

Incorporate additional features:
- Sequence similarity
- Domain architecture
- Gene expression data
- Protein-protein interactions

### 3. Graph Neural Networks

Use deep learning on graphs:
- Graph Convolutional Networks (GCN)
- GraphSAGE
- Graph Attention Networks (GAT)

### 4. Active Learning

Prioritize which proteins to experimentally validate based on prediction uncertainty.

### 5. GO Term Prediction

Extend to Gene Ontology (GO) terms, which have hierarchical structure.

## Testing & Validation

```bash
# Run with test parameters
docker compose exec python python -c "
import os
os.environ['PROTEIN_LIMIT'] = '1000'
os.environ['CONFIDENCE_THRESHOLD'] = '0.4'
exec(open('src/label_propagation.py').read())
"

# Check predictions in MongoDB
docker compose exec mongodb mongosh -u root -p password123 << EOF
use protein_db
db.predictions.countDocuments()
db.predictions.findOne()
db.predictions.aggregate([
  {\$group: {_id: null, avgConf: {\$avg: '\$average_confidence'}}}
])
EOF

# Check predictions in Neo4j
docker compose exec neo4j cypher-shell -u neo4j -p password123 << EOF
MATCH (p:Protein) WHERE exists(p.predicted_ec_numbers)
RETURN count(p);
EOF
```

## Integration with Previous Tasks

- **Task 1 (MongoDB)**: Source of labeled proteins
- **Task 2 (Graph)**: Structure for propagation
- **Task 3 (API)**: Expose predictions via endpoints
- **Task 5 (Visualization)**: Display prediction confidence

## Conclusion

The label propagation algorithm successfully:
- Leverages graph structure for function prediction
- Provides confidence scores for reliability assessment
- Handles multi-label classification naturally
- Scales to large protein networks
- Integrates with existing database infrastructure

This enables automatic annotation of unlabeled proteins, helping bridge the gap between known and unknown protein functions.
