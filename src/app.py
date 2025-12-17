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

@app.route('/')
def index():
    return render_template('index.html') # Homepage

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

# MongoDB

@app.route('/api/mongodb/search')
def mongodb_search():
    query_term = request.args.get('q', '')
    limit = int(request.args.get('limit', 50))
    
    if not query_term:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    try:
        proteins = mongo_client.search_proteins(query_term, limit=limit)
        
        return jsonify({
            'query': query_term,
            'count': len(proteins),
            'limit': limit,
            'proteins': proteins
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mongodb/protein/<protein_id>')
def mongodb_get_protein(protein_id):
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
    try:
        stats = mongo_client.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Neo4j

@app.route('/api/neo4j/protein/<protein_id>')
def neo4j_get_protein(protein_id):
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
    depth = int(request.args.get('depth', 1))
    min_weight = float(request.args.get('min_weight', 0.0))
    limit = int(request.args.get('limit', 100))  # Increased default to 100
    
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
    depth = int(request.args.get('depth', 2))
    min_weight = float(request.args.get('min_weight', 0.1))
    limit = int(request.args.get('limit', 500))  # Increased from 100 to 500
    
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
    try:
        stats = neo4j_client.get_graph_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/neo4j/adaptive-threshold/<protein_id>')
def neo4j_adaptive_threshold(protein_id):
    target_neighbors = int(request.args.get('target_neighbors', 10))
    
    try:
        result = neo4j_client.get_adaptive_threshold(
            protein_id=protein_id,
            target_neighbors=target_neighbors
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/neo4j/neighbors-adaptive/<protein_id>')
def neo4j_get_neighbors_adaptive(protein_id):
    target_neighbors = int(request.args.get('target_neighbors', 10))
    depth = int(request.args.get('depth', 1))
    
    try:
        # Get adaptive threshold
        threshold_info = neo4j_client.get_adaptive_threshold(
            protein_id=protein_id,
            target_neighbors=target_neighbors
        )
        
        # Get neighbors with that threshold
        neighbors = neo4j_client.get_neighbors(
            protein_id=protein_id,
            depth=depth,
            min_weight=threshold_info['recommended_threshold'],
            limit=target_neighbors * 2  # Allow some overflow
        )
        
        if neighbors:
            neighbors['threshold_info'] = threshold_info
            return jsonify(neighbors)
        else:
            return jsonify({'error': 'Protein not found in graph'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Statistics

@app.route('/api/statistics/overview')
def statistics_overview():
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

# Predictions

@app.route('/api/predictions/<protein_id>')
def get_prediction(protein_id):
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


# ERROR HANDLERS

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# MAIN

if __name__ == '__main__':
    print("\n" + "="*60)
    print("PROTEIN ANALYSIS API")
    print("="*60)
    print(f"MongoDB: {os.getenv('MONGO_URI', 'Not configured')}")
    print(f"Neo4j: {os.getenv('NEO4J_URI', 'Not configured')}")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)