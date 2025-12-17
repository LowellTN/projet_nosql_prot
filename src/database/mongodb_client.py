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
    
    def search_proteins(self, text: str, limit: int = 50) -> List[Dict]:
        results = list(self.proteins.find({
            '$or': [
                {'identifier': {'$regex': text, '$options': 'i'}},
                {'entry_name': {'$regex': text, '$options': 'i'}},
                {'name': {'$regex': text, '$options': 'i'}}
            ]
        }).limit(limit))
        
        # Convert ObjectId to string
        for protein in results:
            protein['_id'] = str(protein['_id'])
        
        return results
    
    def get_statistics(self) -> Dict:
        try:
            total_count = self.proteins.count_documents({})
            labeled_count = self.proteins.count_documents({'is_labeled': True})
            unlabeled_count = self.proteins.count_documents({'is_labeled': False})
            predicted_count = self.proteins.count_documents({'is_predicted': True})
            
            # Average sequence length
            pipeline = [
                {'$group': {
                    '_id': None,
                    'avg_length': {'$avg': '$sequence_length'}
                }}
            ]
            avg_result = list(self.proteins.aggregate(pipeline))
            avg_length = avg_result[0]['avg_length'] if avg_result else 0
            
            # EC number distribution (top 10)
            ec_pipeline = [
                {'$match': {'ec_numbers': {'$ne': []}}},
                {'$unwind': '$ec_numbers'},
                {'$group': {
                    '_id': '$ec_numbers',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]
            ec_distribution = list(self.proteins.aggregate(ec_pipeline))
            
            # InterPro domain distribution (top 10)
            domain_pipeline = [
                {'$match': {'interpro_domains': {'$ne': []}}},
                {'$unwind': '$interpro_domains'},
                {'$group': {
                    '_id': '$interpro_domains',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]
            domain_distribution = list(self.proteins.aggregate(domain_pipeline))
            
            return {
                'total_proteins': total_count,
                'labeled_proteins': labeled_count,
                'unlabeled_proteins': unlabeled_count,
                'predicted_proteins': predicted_count,
                'labeled_percentage': round((labeled_count / total_count * 100), 2) if total_count > 0 else 0,
                'predicted_percentage': round((predicted_count / total_count * 100), 2) if total_count > 0 else 0,
                'average_sequence_length': round(avg_length, 2),
                'top_ec_numbers': [{'ec_number': item['_id'], 'count': item['count']} for item in ec_distribution],
                'top_domains': [{'domain': item['_id'], 'count': item['count']} for item in domain_distribution]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def close(self):
        self.client.close()