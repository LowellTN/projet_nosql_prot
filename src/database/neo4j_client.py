from neo4j import GraphDatabase
from typing import Dict, List, Optional

class Neo4jClient:
    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def check_connection(self) -> bool:
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                return result.single()[0] == 1
        except Exception as e:
            print(f"Neo4j connection error: {e}")
            return False
    
    def create_protein_node(self, protein_id: str, properties: Dict):
        with self.driver.session() as session:
            session.run(
                "CREATE (p:Protein {id: $id}) SET p += $properties",
                id=protein_id,
                properties=properties
            )
    
    def create_similarity_relationship(self, protein1_id: str, protein2_id: str, weight: float):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (p1:Protein {id: $id1})
                MATCH (p2:Protein {id: $id2})
                CREATE (p1)-[:SIMILAR_TO {weight: $weight}]->(p2)
                """,
                id1=protein1_id,
                id2=protein2_id,
                weight=weight
            )
    
    def get_protein_node(self, protein_id: str) -> Optional[Dict]:
        """
        Get a protein node by ID.
        
        Args:
            protein_id: Protein identifier
            
        Returns:
            Dictionary with protein properties or None
        """
        with self.driver.session() as session:
            result = session.run(
                "MATCH (p:Protein {id: $id}) RETURN p",
                id=protein_id
            )
            record = result.single()
            if record:
                return dict(record['p'])
            return None
    
    def get_neighbors(self, protein_id: str, depth: int = 1, 
                     min_weight: float = 0.0, limit: int = 50) -> Optional[Dict]:
        """
        Get neighbors of a protein.
        
        Args:
            protein_id: Protein identifier
            depth: Neighborhood depth (1 or 2)
            min_weight: Minimum edge weight
            limit: Maximum neighbors to return
            
        Returns:
            Dictionary with protein and neighbors
        """
        with self.driver.session() as session:
            if depth == 1:
                query = """
                MATCH (p:Protein {id: $id})
                OPTIONAL MATCH (p)-[r:SIMILAR_TO]-(neighbor:Protein)
                WHERE r.weight >= $min_weight
                WITH p, neighbor, r
                ORDER BY r.weight DESC
                LIMIT $limit
                RETURN p, collect({neighbor: neighbor, weight: r.weight}) as neighbors
                """
            else:  # depth == 2
                query = """
                MATCH (p:Protein {id: $id})
                OPTIONAL MATCH path = (p)-[r1:SIMILAR_TO]-(n1:Protein)-[r2:SIMILAR_TO]-(n2:Protein)
                WHERE r1.weight >= $min_weight AND r2.weight >= $min_weight
                AND n2.id <> p.id
                WITH p, n1, n2, r1, r2
                ORDER BY r1.weight DESC, r2.weight DESC
                LIMIT $limit
                RETURN p, 
                       collect(DISTINCT {neighbor: n1, weight: r1.weight}) as neighbors1,
                       collect(DISTINCT {neighbor: n2, weight: r2.weight}) as neighbors2
                """
            
            result = session.run(query, id=protein_id, min_weight=min_weight, limit=limit)
            record = result.single()
            
            if record:
                protein = dict(record['p'])
                
                if depth == 1:
                    neighbors = []
                    for item in record['neighbors']:
                        if item['neighbor']:
                            neighbors.append({
                                'protein': dict(item['neighbor']),
                                'weight': item['weight']
                            })
                    return {
                        'protein': protein,
                        'neighbors': neighbors,
                        'depth': depth,
                        'count': len(neighbors)
                    }
                else:
                    all_neighbors = []
                    seen = set()
                    
                    for item in record['neighbors1']:
                        if item['neighbor']:
                            nid = item['neighbor']['id']
                            if nid not in seen:
                                all_neighbors.append({
                                    'protein': dict(item['neighbor']),
                                    'weight': item['weight'],
                                    'distance': 1
                                })
                                seen.add(nid)
                    
                    for item in record['neighbors2']:
                        if item['neighbor']:
                            nid = item['neighbor']['id']
                            if nid not in seen:
                                all_neighbors.append({
                                    'protein': dict(item['neighbor']),
                                    'weight': item['weight'],
                                    'distance': 2
                                })
                                seen.add(nid)
                    
                    return {
                        'protein': protein,
                        'neighbors': all_neighbors,
                        'depth': depth,
                        'count': len(all_neighbors)
                    }
            
            return None
    
    def get_neighborhood_visualization(self, protein_id: str, depth: int = 2,
                                      min_weight: float = 0.1, limit: int = 100) -> Optional[Dict]:
        """
        Get neighborhood data for visualization (nodes and edges).
        
        Args:
            protein_id: Protein identifier
            depth: Neighborhood depth
            min_weight: Minimum edge weight
            limit: Maximum nodes
            
        Returns:
            Dictionary with nodes and edges arrays
        """
        with self.driver.session() as session:
            query = """
            MATCH (center:Protein {id: $id})
            OPTIONAL MATCH path = (center)-[r:SIMILAR_TO*1..""" + str(depth) + """]->(neighbor:Protein)
            WHERE ALL(rel IN relationships(path) WHERE rel.weight >= $min_weight)
            WITH center, collect(DISTINCT neighbor)[0..$limit] as neighbors,
                 collect(DISTINCT path) as paths
            UNWIND paths as p
            WITH center, neighbors, relationships(p) as rels, nodes(p) as path_nodes
            UNWIND rels as rel
            RETURN center, neighbors, 
                   collect(DISTINCT {
                       source: startNode(rel).id, 
                       target: endNode(rel).id, 
                       weight: rel.weight
                   }) as edges
            """
            
            result = session.run(query, id=protein_id, min_weight=min_weight, limit=limit)
            record = result.single()
            
            if record:
                center = dict(record['center'])
                neighbors = [dict(n) for n in record['neighbors'] if n]
                edges = record['edges']
                
                # Build nodes array
                nodes = [center] + neighbors
                
                # Add node metadata
                for node in nodes:
                    node['is_center'] = (node['id'] == protein_id)
                    node['label_type'] = 'labeled' if node.get('is_labeled', False) else 'unlabeled'
                
                return {
                    'nodes': nodes,
                    'edges': edges,
                    'center_id': protein_id,
                    'node_count': len(nodes),
                    'edge_count': len(edges)
                }
            
            return None
    
    def search_proteins(self, search_term: str, limit: int = 50) -> List[Dict]:
        """
        Search proteins in graph by identifier or name.
        
        Args:
            search_term: Search term
            limit: Maximum results
            
        Returns:
            List of matching proteins
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Protein)
                WHERE p.id =~ $regex OR p.name =~ $regex OR p.entry_name =~ $regex
                RETURN p
                LIMIT $limit
                """,
                regex=f"(?i).*{search_term}.*",
                limit=limit
            )
            
            proteins = []
            for record in result:
                proteins.append(dict(record['p']))
            
            return proteins
    
    def get_graph_statistics(self) -> Dict:
        """
        Get comprehensive graph statistics.
        
        Returns:
            Dictionary with graph statistics
        """
        with self.driver.session() as session:
            # Total node count
            total_result = session.run("MATCH (p:Protein) RETURN count(p) as count")
            total_count = total_result.single()['count']
            
            # Labeled vs unlabeled
            labeled_result = session.run(
                "MATCH (p:Protein) WHERE p.is_labeled = true RETURN count(p) as count"
            )
            labeled_count = labeled_result.single()['count']
            unlabeled_count = total_count - labeled_count
            
            # Edge count
            edge_result = session.run("MATCH ()-[r:SIMILAR_TO]->() RETURN count(r) as count")
            edge_count = edge_result.single()['count']
            
            # Isolated proteins (no neighbors)
            isolated_result = session.run(
                "MATCH (p:Protein) WHERE NOT (p)-[:SIMILAR_TO]-() RETURN count(p) as count"
            )
            isolated_count = isolated_result.single()['count']
            
            # Average degree
            avg_degree = (2 * edge_count / total_count) if total_count > 0 else 0
            
            # Degree distribution (top 10 most connected)
            degree_result = session.run(
                """
                MATCH (p:Protein)-[r:SIMILAR_TO]-()
                WITH p, count(r) as degree
                RETURN p.id as protein_id, p.name as protein_name, degree
                ORDER BY degree DESC
                LIMIT 10
                """
            )
            top_connected = []
            for record in degree_result:
                top_connected.append({
                    'protein_id': record['protein_id'],
                    'protein_name': record['protein_name'],
                    'degree': record['degree']
                })
            
            return {
                'total_proteins': total_count,
                'labeled_proteins': labeled_count,
                'unlabeled_proteins': unlabeled_count,
                'labeled_percentage': round((labeled_count / total_count * 100), 2) if total_count > 0 else 0,
                'total_edges': edge_count,
                'isolated_proteins': isolated_count,
                'isolated_percentage': round((isolated_count / total_count * 100), 2) if total_count > 0 else 0,
                'average_degree': round(avg_degree, 2),
                'top_connected_proteins': top_connected
            }
    
    def close(self):
        self.driver.close()