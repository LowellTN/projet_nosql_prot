from flask import Flask, jsonify, request
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
    return jsonify({
        'status': 'running',
        'message': 'Protein Analysis API'
    })

@app.route('/health')
def health():
    return jsonify({
        'mongodb': mongo_client.check_connection(),
        'neo4j': neo4j_client.check_connection()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)