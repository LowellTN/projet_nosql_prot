from flask import Flask, jsonify, request, render_template_string, render_template
from flask_cors import CORS
from database.mongodb_client import MongoDBClient
from database.neo4j_client import Neo4jClient
import os

app = Flask(__name__)
CORS(app)

# Initialize database clients
mongo_client = MongoDBClient(
    uri=os.getenv('MONGO_URI'),
    db_name=os.getenv('MONGO_DB_NAME', 'protein_db')
)

neo4j_client = Neo4jClient(
    uri=os.getenv('NEO4J_URI'),
    username=os.getenv('NEO4J_USERNAME'),
    password=os.getenv('NEO4J_PASSWORD')
)

# ============================================================================
# HOME AND HEALTH ENDPOINTS
# ============================================================================

@app.route('/')
def index():
    """
    Home page with graphical interface.
    """
    return render_template('index.html')

@app.route('/health')
def health():
    """
    Health check endpoint - verifies database connections.
    
    Returns:
        JSON with connection status for MongoDB and Neo4j
    """
    return jsonify({
        'status': 'running',
        'mongodb': mongo_client.check_connection(),
        'neo4j': neo4j_client.check_connection()
    })

# ============================================================================
# MONGODB ENDPOINTS (Task 3.1)
# ============================================================================

@app.route('/api/mongodb/search')
def mongodb_search():
    """
    Search proteins in MongoDB by identifier, name, or description.
    
    Query Parameters:
        q (str): Search term
        limit (int): Maximum results (default: 50)
    
    Returns:
        JSON array of matching proteins
    
    Example:
        GET /api/mongodb/search?q=cytochrome&limit=10
    """
    query_term = request.args.get('q', '')
    limit = int(request.args.get('limit', 50))
    
    if not query_term:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    try:
        # Search across multiple fields
        proteins = mongo_client.search_proteins(query_term, limit=limit)
        
        return jsonify({
            'query': query_term,
            'count': len(proteins),
            'limit': limit,
            'proteins': proteins  # Changed from 'results' to 'proteins' for consistency with frontend
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mongodb/protein/<protein_id>')
def mongodb_get_protein(protein_id):
    """
    Get protein details by identifier from MongoDB.
    
    Path Parameters:
        protein_id (str): Protein identifier
    
    Returns:
        JSON with protein details
    
    Example:
        GET /api/mongodb/protein/A0A087X1C5
    """
    try:
        protein = mongo_client.find_protein({'identifier': protein_id})
        
        if protein:
            # Convert ObjectId to string
            protein['_id'] = str(protein['_id'])
            return jsonify(protein)
        else:
            return jsonify({'error': 'Protein not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mongodb/statistics')
def mongodb_statistics():
    """
    Get statistics from MongoDB.
    
    Returns:
        JSON with database statistics including:
        - Total protein count
        - Labeled/unlabeled counts
        - Average sequence length
        - EC number distribution
    
    Example:
        GET /api/mongodb/statistics
    """
    try:
        stats = mongo_client.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# NEO4J ENDPOINTS (Task 3.2)
# ============================================================================

@app.route('/api/neo4j/protein/<protein_id>')
def neo4j_get_protein(protein_id):
    """
    Get protein node from Neo4j graph.
    
    Path Parameters:
        protein_id (str): Protein identifier
    
    Returns:
        JSON with protein node properties
    
    Example:
        GET /api/neo4j/protein/A0A087X1C5
    """
    try:
        protein = neo4j_client.get_protein_node(protein_id)
        
        if protein:
            return jsonify(protein)
        else:
            return jsonify({'error': 'Protein not found in graph'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/neo4j/neighbors/<protein_id>')
def neo4j_get_neighbors(protein_id):
    """
    Get neighbors of a protein in the graph.
    
    Path Parameters:
        protein_id (str): Protein identifier
    
    Query Parameters:
        depth (int): Neighborhood depth (1 or 2, default: 1)
        min_weight (float): Minimum edge weight (default: 0.0)
        limit (int): Maximum neighbors to return (default: 50)
    
    Returns:
        JSON with protein and its neighbors
    
    Example:
        GET /api/neo4j/neighbors/A0A087X1C5?depth=1&min_weight=0.2&limit=20
    """
    depth = int(request.args.get('depth', 1))
    min_weight = float(request.args.get('min_weight', 0.0))
    limit = int(request.args.get('limit', 50))
    
    if depth not in [1, 2]:
        return jsonify({'error': 'Depth must be 1 or 2'}), 400
    
    try:
        result = neo4j_client.get_neighbors(
            protein_id=protein_id,
            depth=depth,
            min_weight=min_weight,
            limit=limit
        )
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Protein not found in graph'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/neo4j/neighborhood/<protein_id>')
def neo4j_get_neighborhood(protein_id):
    """
    Get full neighborhood data for visualization.
    
    Returns nodes and edges suitable for graph visualization libraries.
    
    Path Parameters:
        protein_id (str): Protein identifier
    
    Query Parameters:
        depth (int): Neighborhood depth (1 or 2, default: 2)
        min_weight (float): Minimum edge weight (default: 0.1)
        limit (int): Maximum nodes (default: 100)
    
    Returns:
        JSON with nodes and edges arrays
    
    Example:
        GET /api/neo4j/neighborhood/A0A087X1C5?depth=2&min_weight=0.2
    """
    depth = int(request.args.get('depth', 2))
    min_weight = float(request.args.get('min_weight', 0.1))
    limit = int(request.args.get('limit', 100))
    
    try:
        result = neo4j_client.get_neighborhood_visualization(
            protein_id=protein_id,
            depth=depth,
            min_weight=min_weight,
            limit=limit
        )
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Protein not found in graph'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/neo4j/search')
def neo4j_search():
    """
    Search proteins in Neo4j graph by identifier or name.
    
    Query Parameters:
        q (str): Search term
        limit (int): Maximum results (default: 50)
    
    Returns:
        JSON array of matching proteins
    
    Example:
        GET /api/neo4j/search?q=cytochrome&limit=10
    """
    query_term = request.args.get('q', '')
    limit = int(request.args.get('limit', 50))
    
    if not query_term:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    try:
        proteins = neo4j_client.search_proteins(query_term, limit=limit)
        
        return jsonify({
            'query': query_term,
            'count': len(proteins),
            'limit': limit,
            'results': proteins
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/neo4j/statistics')
def neo4j_statistics():
    """
    Get graph statistics from Neo4j (Task 3.3).
    
    Returns statistics including:
    - Total protein count
    - Labeled/unlabeled counts
    - Isolated proteins (no neighbors)
    - Average node degree
    - Edge count
    
    Returns:
        JSON with graph statistics
    
    Example:
        GET /api/neo4j/statistics
    """
    try:
        stats = neo4j_client.get_graph_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# COMBINED STATISTICS (Task 3.3)
# ============================================================================

@app.route('/api/statistics/overview')
def statistics_overview():
    """
    Get comprehensive statistics from both databases.
    
    Returns:
        JSON with combined statistics from MongoDB and Neo4j
    
    Example:
        GET /api/statistics/overview
    """
    try:
        mongo_stats = mongo_client.get_statistics()
        neo4j_stats = neo4j_client.get_graph_statistics()
        
        return jsonify({
            'mongodb': mongo_stats,
            'neo4j': neo4j_stats,
            'system': {
                'status': 'operational',
                'mongodb_connected': mongo_client.check_connection(),
                'neo4j_connected': neo4j_client.check_connection()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PREDICTIONS ENDPOINTS
# ============================================================================

@app.route('/api/predictions/<protein_id>')
def get_prediction(protein_id):
    """
    Get prediction for a specific protein.
    
    Path Parameters:
        protein_id (str): Protein identifier
    
    Returns:
        JSON with predicted EC numbers and confidence scores
    
    Example:
        GET /api/predictions/A0A0B4J2F0
    """
    try:
        # Get prediction from MongoDB predictions collection
        prediction = mongo_client.db['predictions'].find_one({'protein_id': protein_id})
        
        if prediction:
            prediction['_id'] = str(prediction['_id'])
            return jsonify(prediction)
        else:
            return jsonify({'error': 'No prediction found for this protein'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predictions')
def get_predictions():
    """
    Get list of predictions with pagination.
    
    Query Parameters:
        limit (int): Maximum number of predictions to return (default: 20)
        skip (int): Number of predictions to skip (default: 0)
    
    Returns:
        JSON with list of predictions
    
    Example:
        GET /api/predictions?limit=10
    """
    limit = int(request.args.get('limit', 20))
    skip = int(request.args.get('skip', 0))
    
    try:
        predictions = list(mongo_client.db['predictions'].find().skip(skip).limit(limit))
        
        # Convert ObjectId to string
        for pred in predictions:
            pred['_id'] = str(pred['_id'])
        
        total = mongo_client.db['predictions'].count_documents({})
        
        return jsonify({
            'predictions': predictions,
            'count': len(predictions),
            'total': total,
            'limit': limit,
            'skip': skip
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("PROTEIN ANALYSIS API")
    print("="*60)
    print(f"MongoDB: {os.getenv('MONGO_URI', 'Not configured')}")
    print(f"Neo4j: {os.getenv('NEO4J_URI', 'Not configured')}")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)