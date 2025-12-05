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
    
    def close(self):
        self.driver.close()