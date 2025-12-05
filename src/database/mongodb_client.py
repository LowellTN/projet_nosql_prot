from pymongo import MongoClient
from typing import Dict, List, Optional

class MongoDBClient:
    def __init__(self, uri: str, db_name: str):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.proteins = self.db['proteins']
    
    def check_connection(self) -> bool:
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            return False
    
    def insert_protein(self, protein_data: Dict) -> str:
        result = self.proteins.insert_one(protein_data)
        return str(result.inserted_id)
    
    def find_protein(self, query: Dict) -> Optional[Dict]:
        return self.proteins.find_one(query)
    
    def search_proteins(self, text: str) -> List[Dict]:
        return list(self.proteins.find({
            '$or': [
                {'identifier': {'$regex': text, '$options': 'i'}},
                {'name': {'$regex': text, '$options': 'i'}},
                {'description': {'$regex': text, '$options': 'i'}}
            ]
        }))
    
    def close(self):
        self.client.close()