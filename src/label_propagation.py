"""
Label Propagation for Protein Function Annotation

This script implements a label propagation algorithm to infer EC numbers
(enzyme classifications) for unlabeled proteins based on the graph structure
and labeled neighbors.

This is a multi-label classification problem where each protein can have
multiple EC numbers.

Author: Project NoSQL Team
Date: December 2025
"""

import os
import sys
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
from database.mongodb_client import MongoDBClient
from database.neo4j_client import Neo4jClient


class LabelPropagation:
    """
    Implements weighted label propagation for protein function annotation.
    
    The algorithm propagates EC numbers from labeled proteins to unlabeled
    neighbors based on edge weights (Jaccard similarity).
    
    Key features:
    - Multi-label classification (proteins can have multiple EC numbers)
    - Weighted voting based on edge weights
    - Confidence scores for predictions
    - Iterative propagation through the graph
    """
    
    def __init__(self, mongo_client: MongoDBClient, neo4j_client: Neo4jClient):
        """
        Initialize label propagation.
        
        Args:
            mongo_client: MongoDB client instance
            neo4j_client: Neo4j client instance
        """
        self.mongo_client = mongo_client
        self.neo4j_client = neo4j_client
        self.stats = {
            'total_proteins': 0,
            'labeled_proteins': 0,
            'unlabeled_proteins': 0,
            'proteins_annotated': 0,
            'total_labels_propagated': 0,
            'average_confidence': 0.0
        }
    
    def get_neighbor_labels(self, protein_id: str, min_weight: float = 0.1) -> Dict[str, float]:
        """
        Get EC numbers from neighbors with weighted voting.
        
        For each EC number, calculates a weighted vote:
            vote(ec) = sum(weight * has_ec(neighbor)) / sum(weight)
        
        Args:
            protein_id: Protein identifier
            min_weight: Minimum edge weight to consider
            
        Returns:
            Dictionary mapping EC number to confidence score (0.0 to 1.0)
        """
        with self.neo4j_client.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Protein {id: $id})-[r:SIMILAR_TO]-(neighbor:Protein)
                WHERE r.weight >= $min_weight 
                  AND neighbor.is_labeled = true
                  AND size(neighbor.ec_numbers) > 0
                RETURN neighbor.ec_numbers as ec_numbers, r.weight as weight
                """,
                id=protein_id,
                min_weight=min_weight
            )
            
            # Collect weighted votes for each EC number
            ec_votes = defaultdict(float)
            total_weight = 0.0
            
            for record in result:
                ec_numbers = record['ec_numbers']
                weight = record['weight']
                total_weight += weight
                
                for ec in ec_numbers:
                    ec_votes[ec] += weight
            
            # Normalize by total weight to get confidence scores
            if total_weight > 0:
                ec_confidence = {
                    ec: vote / total_weight
                    for ec, vote in ec_votes.items()
                }
                return ec_confidence
            
            return {}
    
    def propagate_labels(self, confidence_threshold: float = 0.3,
                        min_edge_weight: float = 0.1,
                        max_labels_per_protein: int = 5) -> List[Dict]:
        """
        Propagate labels to all unlabeled proteins in the graph.
        
        Algorithm:
        1. Find all unlabeled proteins with labeled neighbors
        2. For each unlabeled protein:
           a. Collect EC numbers from neighbors
           b. Calculate weighted confidence scores
           c. Assign labels above confidence threshold
        3. Update MongoDB with predictions
        
        Args:
            confidence_threshold: Minimum confidence to assign label (default: 0.3)
            min_edge_weight: Minimum edge weight to consider (default: 0.1)
            max_labels_per_protein: Maximum EC numbers to assign (default: 5)
            
        Returns:
            List of predictions with confidence scores
        """
        print(f"\n{'='*60}")
        print("LABEL PROPAGATION - Function Annotation")
        print(f"{'='*60}\n")
        print(f"Configuration:")
        print(f"  Confidence threshold: {confidence_threshold}")
        print(f"  Min edge weight: {min_edge_weight}")
        print(f"  Max labels per protein: {max_labels_per_protein}\n")
        
        # Get all unlabeled proteins with labeled neighbors
        with self.neo4j_client.driver.session() as session:
            result = session.run(
                """
                MATCH (unlabeled:Protein)-[r:SIMILAR_TO]-(labeled:Protein)
                WHERE unlabeled.is_labeled = false
                  AND labeled.is_labeled = true
                  AND r.weight >= $min_weight
                WITH DISTINCT unlabeled
                RETURN unlabeled.id as protein_id
                """,
                min_weight=min_edge_weight
            )
            
            unlabeled_proteins = [record['protein_id'] for record in result]
        
        print(f"Found {len(unlabeled_proteins):,} unlabeled proteins with labeled neighbors\n")
        print("Propagating labels...")
        
        predictions = []
        processed = 0
        
        for protein_id in unlabeled_proteins:
            # Get neighbor labels with confidence scores
            ec_confidence = self.get_neighbor_labels(protein_id, min_edge_weight)
            
            if ec_confidence:
                # Filter by confidence threshold and limit
                filtered_labels = {
                    ec: conf for ec, conf in ec_confidence.items()
                    if conf >= confidence_threshold
                }
                
                # Sort by confidence and take top N
                top_labels = sorted(
                    filtered_labels.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:max_labels_per_protein]
                
                if top_labels:
                    prediction = {
                        'protein_id': protein_id,
                        'predicted_ec_numbers': [ec for ec, _ in top_labels],
                        'confidence_scores': {ec: conf for ec, conf in top_labels},
                        'average_confidence': sum(conf for _, conf in top_labels) / len(top_labels)
                    }
                    predictions.append(prediction)
                    
                    self.stats['proteins_annotated'] += 1
                    self.stats['total_labels_propagated'] += len(top_labels)
            
            processed += 1
            if processed % 100 == 0:
                print(f"Processed {processed:,} / {len(unlabeled_proteins):,} proteins...")
        
        print(f"\n✓ Label propagation complete!")
        print(f"  Proteins annotated: {self.stats['proteins_annotated']:,}")
        print(f"  Total labels assigned: {self.stats['total_labels_propagated']}")
        
        if predictions:
            avg_confidence = sum(p['average_confidence'] for p in predictions) / len(predictions)
            self.stats['average_confidence'] = avg_confidence
            print(f"  Average confidence: {avg_confidence:.3f}")
        
        return predictions
    
    def save_predictions_to_mongodb(self, predictions: List[Dict]) -> None:
        """
        Save predictions to MongoDB in a separate collection.
        
        Creates a 'predictions' collection with predicted EC numbers
        and confidence scores.
        
        Args:
            predictions: List of prediction dictionaries
        """
        print(f"\n{'='*60}")
        print("SAVING PREDICTIONS TO MONGODB")
        print(f"{'='*60}\n")
        
        if not predictions:
            print("No predictions to save.")
            return
        
        predictions_collection = self.mongo_client.db['predictions']
        
        # Create index first (if not exists)
        predictions_collection.create_index('protein_id', unique=True)
        
        # Use upsert to avoid duplicate key errors
        upserted_count = 0
        for pred in predictions:
            predictions_collection.update_one(
                {'protein_id': pred['protein_id']},
                {'$set': pred},
                upsert=True
            )
            upserted_count += 1
        
        print(f"✓ Saved {upserted_count:,} predictions to MongoDB")
    
    def update_proteins_with_predictions(self, predictions: List[Dict]) -> None:
        """
        Update the main proteins collection with predicted EC numbers.
        
        This adds the predicted_ec_numbers field to the protein documents
        and sets is_predicted flag to True.
        
        Args:
            predictions: List of prediction dictionaries
        """
        print(f"\n{'='*60}")
        print("UPDATING PROTEINS COLLECTION WITH PREDICTIONS")
        print(f"{'='*60}\n")
        
        if not predictions:
            print("No predictions to update.")
            return
        
        proteins_collection = self.mongo_client.db['proteins']
        updated_count = 0
        
        for pred in predictions:
            result = proteins_collection.update_one(
                {'identifier': pred['protein_id']},
                {
                    '$set': {
                        'predicted_ec_numbers': pred['predicted_ec_numbers'],
                        'prediction_confidence': pred['confidence_scores'],
                        'is_predicted': True,
                        'average_prediction_confidence': pred['average_confidence']
                    }
                }
            )
            if result.modified_count > 0:
                updated_count += 1
        
        print(f"✓ Updated {updated_count:,} proteins in MongoDB with predictions")
    
    def update_neo4j_with_predictions(self, predictions: List[Dict]) -> None:
        """
        Update Neo4j nodes with predicted EC numbers.
        
        Adds predicted EC numbers as a new property 'predicted_ec_numbers'.
        
        Args:
            predictions: List of prediction dictionaries
        """
        print(f"\n{'='*60}")
        print("UPDATING NEO4J WITH PREDICTIONS")
        print(f"{'='*60}\n")
        
        if not predictions:
            print("No predictions to update.")
            return
        
        batch_size = 500
        batch = []
        
        for pred in predictions:
            batch.append({
                'protein_id': pred['protein_id'],
                'predicted_ec': pred['predicted_ec_numbers'],
                'confidence': pred['confidence_scores']
            })
            
            if len(batch) >= batch_size:
                self._update_neo4j_batch(batch)
                batch = []
        
        if batch:
            self._update_neo4j_batch(batch)
        
        print(f"✓ Updated {len(predictions):,} proteins in Neo4j")
    
    def _update_neo4j_batch(self, batch: List[Dict]) -> None:
        """
        Update a batch of proteins in Neo4j.
        
        Args:
            batch: List of protein updates
        """
        # Convert confidence dict to parallel lists for Neo4j storage
        for item in batch:
            confidence_dict = item['confidence']
            # Create two parallel lists: EC numbers and their confidence scores
            item['confidence_ec'] = list(confidence_dict.keys())
            item['confidence_values'] = list(confidence_dict.values())
        
        with self.neo4j_client.driver.session() as session:
            session.run(
                """
                UNWIND $batch AS item
                MATCH (p:Protein {id: item.protein_id})
                SET p.predicted_ec_numbers = item.predicted_ec,
                    p.prediction_confidence_ec = item.confidence_ec,
                    p.prediction_confidence_values = item.confidence_values
                """,
                batch=batch
            )
    
    def evaluate_predictions(self, predictions: List[Dict]) -> Dict:
        """
        Evaluate prediction quality using proteins with known labels.
        
        For evaluation, we can:
        1. Hide labels from some known proteins
        2. Run label propagation
        3. Compare predictions with actual labels
        
        Metrics:
        - Precision: How many predicted labels are correct
        - Recall: How many actual labels were predicted
        - F1 Score: Harmonic mean of precision and recall
        
        Args:
            predictions: List of prediction dictionaries
            
        Returns:
            Dictionary with evaluation metrics
        """
        # This is a placeholder for evaluation logic
        # In practice, you would split labeled data into train/test sets
        
        return {
            'total_predictions': len(predictions),
            'average_labels_per_protein': self.stats['total_labels_propagated'] / max(1, self.stats['proteins_annotated']),
            'average_confidence': self.stats['average_confidence']
        }
    
    def print_statistics(self) -> None:
        """
        Print label propagation statistics.
        """
        print(f"\n{'='*60}")
        print("LABEL PROPAGATION STATISTICS")
        print(f"{'='*60}")
        print(f"Proteins annotated:         {self.stats['proteins_annotated']:,}")
        print(f"Total labels propagated:    {self.stats['total_labels_propagated']}")
        if self.stats['proteins_annotated'] > 0:
            avg_labels = self.stats['total_labels_propagated'] / self.stats['proteins_annotated']
            print(f"Avg labels per protein:     {avg_labels:.2f}")
        print(f"Average confidence:         {self.stats['average_confidence']:.3f}")
        print(f"{'='*60}\n")


def main():
    """
    Main function to run label propagation.
    """
    print("\n" + "="*60)
    print("LABEL PROPAGATION - Protein Function Annotation")
    print("="*60 + "\n")
    
    # Configuration
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://root:password123@mongodb:27017/')
    mongo_db = os.getenv('MONGO_DB_NAME', 'protein_db')
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
    neo4j_user = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_pass = os.getenv('NEO4J_PASSWORD', 'password123')
    
    # Algorithm parameters
    confidence_threshold = float(os.getenv('CONFIDENCE_THRESHOLD', '0.3'))
    min_edge_weight = float(os.getenv('MIN_EDGE_WEIGHT', '0.1'))
    max_labels = int(os.getenv('MAX_LABELS_PER_PROTEIN', '5'))
    
    print(f"Parameters:")
    print(f"  Confidence threshold: {confidence_threshold}")
    print(f"  Min edge weight: {min_edge_weight}")
    print(f"  Max labels per protein: {max_labels}\n")
    
    # Connect to databases
    print("Connecting to databases...")
    mongo_client = MongoDBClient(uri=mongo_uri, db_name=mongo_db)
    neo4j_client = Neo4jClient(uri=neo4j_uri, username=neo4j_user, password=neo4j_pass)
    
    if not mongo_client.check_connection():
        print("ERROR: Cannot connect to MongoDB!")
        sys.exit(1)
    
    if not neo4j_client.check_connection():
        print("ERROR: Cannot connect to Neo4j!")
        sys.exit(1)
    
    print("✓ Database connections successful\n")
    
    # Initialize label propagation
    lp = LabelPropagation(mongo_client=mongo_client, neo4j_client=neo4j_client)
    
    # Run label propagation
    predictions = lp.propagate_labels(
        confidence_threshold=confidence_threshold,
        min_edge_weight=min_edge_weight,
        max_labels_per_protein=max_labels
    )
    
    if predictions:
        # Save predictions to MongoDB (separate collection)
        lp.save_predictions_to_mongodb(predictions)
        
        # Update proteins collection with predictions
        lp.update_proteins_with_predictions(predictions)
        
        # Update Neo4j with predictions
        lp.update_neo4j_with_predictions(predictions)
        
        # Print statistics
        lp.print_statistics()
        
        # Show sample predictions
        print("Sample Predictions:")
        print("="*60)
        for i, pred in enumerate(predictions[:5]):
            print(f"\nProtein: {pred['protein_id']}")
            print(f"Predicted EC numbers: {', '.join(pred['predicted_ec_numbers'])}")
            print(f"Confidence scores:")
            for ec, conf in pred['confidence_scores'].items():
                print(f"  {ec}: {conf:.3f}")
        print("\n" + "="*60)
    else:
        print("\nNo predictions generated.")
        print("Possible reasons:")
        print("  - No unlabeled proteins with labeled neighbors")
        print("  - Confidence threshold too high")
        print("  - Min edge weight too high")
    
    print("\n" + "="*60)
    print("LABEL PROPAGATION COMPLETE!")
    print("="*60 + "\n")
    
    # Close connections
    mongo_client.close()
    neo4j_client.close()


if __name__ == '__main__':
    main()
