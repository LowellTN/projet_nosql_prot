"""
Protein Graph Builder for Neo4j

This script constructs a domain-based protein-protein network (PPN) in Neo4j.
The graph is built by calculating similarity between proteins based on their
shared InterPro domains using the Jaccard similarity coefficient.

The Jaccard coefficient is calculated as:
    J(A,B) = |A ∩ B| / |A ∪ B|

where A and B are sets of InterPro domain IDs for two proteins.

Author: Project NoSQL Team
Date: December 2025
"""

import os
import sys
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from database.mongodb_client import MongoDBClient
from database.neo4j_client import Neo4jClient


class ProteinGraphBuilder:
    """
    Builds a protein-protein network in Neo4j based on domain similarity.
    
    The graph construction process:
    1. Load proteins with domains from MongoDB
    2. Create protein nodes in Neo4j with attributes
    3. Calculate Jaccard similarity for all protein pairs
    4. Create weighted edges for protein pairs above similarity threshold
    
    Graph properties:
    - Nodes represent proteins (labeled and unlabeled)
    - Edges represent domain similarity (Jaccard coefficient)
    - Graph is undirected and weighted
    """
    
    def __init__(self, mongo_client: MongoDBClient, neo4j_client: Neo4jClient,
                 similarity_threshold: float = 0.1):
        """
        Initialize the graph builder.
        
        Args:
            mongo_client: MongoDB client instance
            neo4j_client: Neo4j client instance
            similarity_threshold: Minimum Jaccard similarity to create an edge (default: 0.1)
        """
        self.mongo_client = mongo_client
        self.neo4j_client = neo4j_client
        self.similarity_threshold = similarity_threshold
        self.stats = {
            'proteins_loaded': 0,
            'nodes_created': 0,
            'edges_created': 0,
            'labeled_nodes': 0,
            'unlabeled_nodes': 0,
            'comparisons': 0
        }
    
    def calculate_jaccard_similarity(self, domains1: Set[str], domains2: Set[str]) -> float:
        """
        Calculate Jaccard similarity coefficient between two sets of domains.
        
        The Jaccard index measures similarity as:
            J(A,B) = |A ∩ B| / |A ∪ B|
        
        Example:
            P1 domains: {d1, d2, d3, d4}
            P2 domains: {d1, d3, d5}
            Intersection: {d1, d3} -> size = 2
            Union: {d1, d2, d3, d4, d5} -> size = 5
            Jaccard = 2/5 = 0.4
        
        Args:
            domains1: Set of InterPro domain IDs for first protein
            domains2: Set of InterPro domain IDs for second protein
            
        Returns:
            Jaccard similarity coefficient (0.0 to 1.0)
        """
        if not domains1 or not domains2:
            return 0.0
        
        intersection = domains1.intersection(domains2)
        union = domains1.union(domains2)
        
        if len(union) == 0:
            return 0.0
        
        return len(intersection) / len(union)
    
    def load_proteins_from_mongodb(self, limit: int = None) -> List[Dict]:
        """
        Load proteins with domain information from MongoDB.
        
        Only proteins with at least one InterPro domain are included
        since we need domains to calculate similarity.
        
        Args:
            limit: Maximum number of proteins to load (None = all)
            
        Returns:
            List of protein documents with domains
        """
        print(f"\n{'='*60}")
        print("LOADING PROTEINS FROM MONGODB")
        print(f"{'='*60}\n")
        
        # Query: proteins with at least one InterPro domain
        query = {
            'interpro_domains': {'$exists': True, '$ne': []}
        }
        
        cursor = self.mongo_client.proteins.find(query)
        if limit:
            cursor = cursor.limit(limit)
        
        proteins = list(cursor)
        self.stats['proteins_loaded'] = len(proteins)
        
        # Count labeled vs unlabeled
        labeled = sum(1 for p in proteins if p.get('is_labeled', False))
        unlabeled = len(proteins) - labeled
        
        print(f"✓ Loaded {len(proteins):,} proteins with domains")
        print(f"  - Labeled (with EC numbers): {labeled:,}")
        print(f"  - Unlabeled (no EC numbers): {unlabeled:,}")
        
        return proteins
    
    def create_protein_nodes(self, proteins: List[Dict]) -> None:
        """
        Create protein nodes in Neo4j with their attributes.
        
        Each node contains:
        - id: Protein identifier
        - entry_name: Entry name
        - name: Full protein name
        - organism: Species
        - is_labeled: Has EC numbers?
        - ec_numbers: List of EC classifications (if labeled)
        - interpro_domains: List of domain IDs
        - sequence_length: Length of amino acid sequence
        
        Args:
            proteins: List of protein documents from MongoDB
        """
        print(f"\n{'='*60}")
        print("CREATING PROTEIN NODES IN NEO4J")
        print(f"{'='*60}\n")
        
        batch_size = 500
        batch = []
        
        for i, protein in enumerate(proteins):
            # Prepare node properties
            node_data = {
                'id': protein['identifier'],
                'entry_name': protein.get('entry_name', ''),
                'name': protein.get('name', ''),
                'organism': protein.get('organism', ''),
                'is_labeled': protein.get('is_labeled', False),
                'ec_numbers': protein.get('ec_numbers', []),
                'interpro_domains': protein.get('interpro_domains', []),
                'sequence_length': protein.get('sequence_length', 0)
            }
            
            batch.append(node_data)
            
            # Track statistics
            if protein.get('is_labeled', False):
                self.stats['labeled_nodes'] += 1
            else:
                self.stats['unlabeled_nodes'] += 1
            
            # Insert batch
            if len(batch) >= batch_size:
                self._create_node_batch(batch)
                batch = []
                
                if (i + 1) % 5000 == 0:
                    print(f"Created {i + 1:,} nodes...")
        
        # Insert remaining nodes
        if batch:
            self._create_node_batch(batch)
        
        print(f"\n✓ Created {self.stats['nodes_created']:,} protein nodes")
        print(f"  - Labeled: {self.stats['labeled_nodes']:,}")
        print(f"  - Unlabeled: {self.stats['unlabeled_nodes']:,}")
    
    def _create_node_batch(self, batch: List[Dict]) -> None:
        """
        Create a batch of protein nodes in Neo4j.
        
        Uses Cypher UNWIND for efficient batch creation.
        
        Args:
            batch: List of node data dictionaries
        """
        with self.neo4j_client.driver.session() as session:
            session.run("""
                UNWIND $batch AS protein
                CREATE (p:Protein {
                    id: protein.id,
                    entry_name: protein.entry_name,
                    name: protein.name,
                    organism: protein.organism,
                    is_labeled: protein.is_labeled,
                    ec_numbers: protein.ec_numbers,
                    interpro_domains: protein.interpro_domains,
                    sequence_length: protein.sequence_length
                })
            """, batch=batch)
        
        self.stats['nodes_created'] += len(batch)
    
    def create_similarity_edges(self, proteins: List[Dict], 
                               batch_size: int = 1000) -> None:
        """
        Create similarity edges between proteins based on Jaccard coefficient.
        
        This is the most computationally intensive part of graph construction.
        For N proteins, we need to compare N*(N-1)/2 pairs.
        
        To optimize:
        - Only create edges above similarity threshold
        - Process in batches
        - Show progress updates
        
        Args:
            proteins: List of protein documents
            batch_size: Number of edges to create in each batch
        """
        print(f"\n{'='*60}")
        print("CREATING SIMILARITY EDGES")
        print(f"{'='*60}\n")
        print(f"Similarity threshold: {self.similarity_threshold}")
        print(f"Maximum comparisons: {len(proteins) * (len(proteins) - 1) // 2:,}\n")
        
        # Prepare domain sets for fast lookup
        protein_domains = {}
        for protein in proteins:
            pid = protein['identifier']
            domains = set(protein.get('interpro_domains', []))
            if domains:
                protein_domains[pid] = domains
        
        protein_ids = list(protein_domains.keys())
        edges_batch = []
        
        # Compare all pairs
        total_pairs = len(protein_ids) * (len(protein_ids) - 1) // 2
        processed = 0
        
        for i in range(len(protein_ids)):
            for j in range(i + 1, len(protein_ids)):
                id1 = protein_ids[i]
                id2 = protein_ids[j]
                
                # Calculate Jaccard similarity
                similarity = self.calculate_jaccard_similarity(
                    protein_domains[id1],
                    protein_domains[id2]
                )
                
                self.stats['comparisons'] += 1
                processed += 1
                
                # Create edge if above threshold
                if similarity >= self.similarity_threshold:
                    edges_batch.append({
                        'id1': id1,
                        'id2': id2,
                        'weight': similarity
                    })
                    
                    # Insert batch
                    if len(edges_batch) >= batch_size:
                        self._create_edge_batch(edges_batch)
                        edges_batch = []
                
                # Progress update
                if processed % 100000 == 0:
                    progress = (processed / total_pairs) * 100
                    print(f"Progress: {processed:,}/{total_pairs:,} comparisons "
                          f"({progress:.1f}%) - Edges: {self.stats['edges_created']:,}")
        
        # Insert remaining edges
        if edges_batch:
            self._create_edge_batch(edges_batch)
        
        print(f"\n✓ Created {self.stats['edges_created']:,} similarity edges")
    
    def _create_edge_batch(self, batch: List[Dict]) -> None:
        """
        Create a batch of similarity edges in Neo4j.
        
        Creates directed edges with weight property.
        Note: In Neo4j, all relationships must be directed, but we can
        query them as undirected using Cypher patterns.
        
        Args:
            batch: List of edge data dictionaries
        """
        with self.neo4j_client.driver.session() as session:
            session.run("""
                UNWIND $batch AS edge
                MATCH (p1:Protein {id: edge.id1})
                MATCH (p2:Protein {id: edge.id2})
                CREATE (p1)-[:SIMILAR_TO {weight: edge.weight}]->(p2)
            """, batch=batch)
        
        self.stats['edges_created'] += len(batch)
    
    def create_indexes(self) -> None:
        """
        Create indexes on Neo4j for efficient queries.
        """
        print(f"\n{'='*60}")
        print("CREATING NEO4J INDEXES")
        print(f"{'='*60}\n")
        
        with self.neo4j_client.driver.session() as session:
            # Index on protein ID
            session.run("CREATE INDEX protein_id IF NOT EXISTS FOR (p:Protein) ON (p.id)")
            print("✓ Created index on protein ID")
            
            # Index on labeled status
            session.run("CREATE INDEX protein_labeled IF NOT EXISTS FOR (p:Protein) ON (p.is_labeled)")
            print("✓ Created index on labeled status")
    
    def print_statistics(self) -> None:
        """
        Print graph construction statistics.
        """
        print(f"\n{'='*60}")
        print("GRAPH CONSTRUCTION STATISTICS")
        print(f"{'='*60}")
        print(f"Proteins loaded:        {self.stats['proteins_loaded']:,}")
        print(f"Nodes created:          {self.stats['nodes_created']:,}")
        print(f"  - Labeled:            {self.stats['labeled_nodes']:,}")
        print(f"  - Unlabeled:          {self.stats['unlabeled_nodes']:,}")
        print(f"Edges created:          {self.stats['edges_created']:,}")
        print(f"Comparisons made:       {self.stats['comparisons']:,}")
        print(f"Similarity threshold:   {self.similarity_threshold}")
        
        if self.stats['nodes_created'] > 0:
            avg_degree = (2 * self.stats['edges_created']) / self.stats['nodes_created']
            print(f"Average node degree:    {avg_degree:.2f}")
        
        print(f"{'='*60}\n")


def main():
    """
    Main function to build the protein graph.
    """
    print("\n" + "="*60)
    print("PROTEIN GRAPH BUILDER - Neo4j Construction")
    print("="*60 + "\n")
    
    # Configuration
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://root:password123@mongodb:27017/')
    mongo_db = os.getenv('MONGO_DB_NAME', 'protein_db')
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
    neo4j_user = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_pass = os.getenv('NEO4J_PASSWORD', 'password123')
    
    # Get configuration from command line or environment
    similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', '0.1'))
    protein_limit = os.getenv('PROTEIN_LIMIT', None)
    if protein_limit:
        protein_limit = int(protein_limit)
    
    print(f"Configuration:")
    print(f"  Similarity threshold: {similarity_threshold}")
    print(f"  Protein limit: {protein_limit if protein_limit else 'None (all proteins)'}\n")
    
    # Check if Neo4j already has data
    neo4j_client = Neo4jClient(neo4j_uri, neo4j_user, neo4j_pass)
    with neo4j_client.driver.session() as session:
        result = session.run("MATCH (p:Protein) RETURN count(p) as count")
        existing_count = result.single()['count']
    
    if existing_count > 0:
        print(f"⚠ WARNING: Neo4j already contains {existing_count:,} protein nodes")
        print("\nOptions:")
        print("  1. Clear existing graph and rebuild (will delete everything)")
        print("  2. Skip building (keep existing graph)")
        print("  3. Continue anyway (will create duplicates!)\n")
        
        choice = os.getenv('RELOAD_MODE', '')
        if not choice:
            choice = input("Enter choice (1/2/3): ").strip()
        
        if choice == '1':
            print("\nClearing existing graph...")
            with neo4j_client.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            print("✓ Existing graph cleared\n")
        elif choice == '2':
            print("\n✓ Keeping existing graph. Exiting.\n")
            neo4j_client.close()
            sys.exit(0)
        else:
            print("\n⚠ Continuing with existing graph (will create duplicates)...\n")
    
    neo4j_client.close()
    
    # Connect to databases (reconnect after check)
    print("Connecting to databases...")
    mongo_client = MongoDBClient(mongo_uri, mongo_db)
    neo4j_client = Neo4jClient(uri=neo4j_uri, username=neo4j_user, password=neo4j_pass)
    
    if not mongo_client.check_connection():
        print("ERROR: Cannot connect to MongoDB!")
        sys.exit(1)
    
    if not neo4j_client.check_connection():
        print("ERROR: Cannot connect to Neo4j!")
        sys.exit(1)
    
    print("✓ Database connections successful\n")
    
    # Initialize graph builder
    builder = ProteinGraphBuilder(
        mongo_client=mongo_client,
        neo4j_client=neo4j_client,
        similarity_threshold=similarity_threshold
    )
    
    # Clear existing graph (optional - for fresh start)
    clear_graph = os.getenv('CLEAR_GRAPH', 'false').lower() == 'true'
    if clear_graph:
        print("Clearing existing graph...")
        with neo4j_client.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✓ Graph cleared\n")
    
    # Step 1: Load proteins from MongoDB
    proteins = builder.load_proteins_from_mongodb(limit=protein_limit)
    
    if not proteins:
        print("ERROR: No proteins with domains found in MongoDB!")
        print("Please run data_loader.py first to populate MongoDB.")
        sys.exit(1)
    
    # Step 2: Create indexes
    builder.create_indexes()
    
    # Step 3: Create protein nodes
    builder.create_protein_nodes(proteins)
    
    # Step 4: Create similarity edges
    builder.create_similarity_edges(proteins)
    
    # Print final statistics
    builder.print_statistics()
    
    print("="*60)
    print("GRAPH CONSTRUCTION COMPLETE!")
    print("="*60 + "\n")
    
    # Close connections
    mongo_client.close()
    neo4j_client.close()


if __name__ == '__main__':
    main()
