"""
Data Loader for Protein Database

This script loads protein data from TSV files into MongoDB.
It parses the UniProt data files and creates structured documents
with searchable fields for identifier, name, description, domains (InterPro),
and EC numbers.

Author: Project NoSQL Team
Date: December 2025
"""

import csv
import os
import sys
from typing import Dict, List, Optional
from database.mongodb_client import MongoDBClient


class ProteinDataLoader:
    """
    Loads protein data from TSV files into MongoDB.
    
    The loader processes UniProt TSV files and extracts:
    - Entry (identifier)
    - Entry Name
    - Protein names (description)
    - Organism
    - Sequence
    - EC numbers (enzyme classification)
    - InterPro domains (protein signatures)
    """
    
    def __init__(self, mongo_client: MongoDBClient):
        self.mongo_client = mongo_client
        self.stats = {
            'total_processed': 0,
            'total_inserted': 0,
            'with_ec': 0,
            'with_interpro': 0,
            'errors': 0
        }
    
    def parse_ec_numbers(self, ec_string: str) -> List[str]:
        """
        Parse EC numbers from the EC number field.
        
        EC numbers are enzyme classification numbers (e.g., 1.14.14.1)
        They can be separated by semicolons and may have trailing spaces.
        
        Args:
            ec_string: Raw EC number string from TSV
            
        Returns:
            List of EC numbers (empty list if none)
        """
        if not ec_string or ec_string.strip() == '':
            return []
        
        # Split by semicolon and clean up
        ec_numbers = [ec.strip() for ec in ec_string.split(';') if ec.strip()]
        return ec_numbers
    
    def parse_interpro_domains(self, interpro_string: str) -> List[str]:
        """
        Parse InterPro domain identifiers from the InterPro field.
        
        InterPro IDs are protein domain/family identifiers (e.g., IPR001128)
        They can be separated by semicolons.
        
        Args:
            interpro_string: Raw InterPro string from TSV
            
        Returns:
            List of InterPro IDs (empty list if none)
        """
        if not interpro_string or interpro_string.strip() == '':
            return []
        
        # Split by semicolon and clean up
        domains = [domain.strip() for domain in interpro_string.split(';') if domain.strip()]
        return domains
    
    def create_protein_document(self, row: Dict[str, str]) -> Optional[Dict]:
        """
        Create a MongoDB document from a TSV row.
        
        The document structure includes:
        - identifier: Protein entry ID (e.g., A0A087X1C5)
        - entry_name: Entry name (e.g., CP2D7_HUMAN)
        - name: Full protein name
        - organism: Species information
        - sequence: Amino acid sequence
        - ec_numbers: List of EC numbers (for labeled proteins)
        - interpro_domains: List of InterPro domain IDs
        - is_labeled: Boolean indicating if protein has EC numbers
        
        Args:
            row: Dictionary representing a TSV row
            
        Returns:
            MongoDB document as dictionary, or None if invalid
        """
        try:
            # Extract fields based on column names
            identifier = row.get('Entry', '').strip()
            entry_name = row.get('Entry Name', '').strip()
            protein_names = row.get('Protein names', '').strip()
            organism = row.get('Organism', '').strip()
            sequence = row.get('Sequence', '').strip()
            ec_string = row.get('EC number', '')
            interpro_string = row.get('InterPro', '')
            
            # Skip if no identifier
            if not identifier:
                return None
            
            # Parse EC numbers and InterPro domains
            ec_numbers = self.parse_ec_numbers(ec_string)
            interpro_domains = self.parse_interpro_domains(interpro_string)
            
            # Create the document
            document = {
                'identifier': identifier,
                'entry_name': entry_name,
                'name': protein_names,
                'organism': organism,
                'sequence': sequence,
                'ec_numbers': ec_numbers,
                'interpro_domains': interpro_domains,
                'is_labeled': len(ec_numbers) > 0,
                'sequence_length': len(sequence) if sequence else 0
            }
            
            return document
            
        except Exception as e:
            print(f"Error creating document: {e}")
            return None
    
    def load_tsv_file(self, filepath: str, batch_size: int = 1000) -> None:
        """
        Load protein data from a TSV file into MongoDB.
        
        The loader processes the file in batches for efficiency.
        It provides progress updates and statistics.
        
        Args:
            filepath: Path to the TSV file
            batch_size: Number of documents to insert at once
        """
        if not os.path.exists(filepath):
            print(f"Error: File not found: {filepath}")
            return
        
        print(f"\n{'='*60}")
        print(f"Loading data from: {os.path.basename(filepath)}")
        print(f"{'='*60}\n")
        
        batch = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Use DictReader to handle TSV with headers
                reader = csv.DictReader(f, delimiter='\t')
                
                for row in reader:
                    self.stats['total_processed'] += 1
                    
                    # Create MongoDB document
                    document = self.create_protein_document(row)
                    
                    if document:
                        batch.append(document)
                        
                        # Update statistics
                        if document['ec_numbers']:
                            self.stats['with_ec'] += 1
                        if document['interpro_domains']:
                            self.stats['with_interpro'] += 1
                        
                        # Insert batch when it reaches batch_size
                        if len(batch) >= batch_size:
                            self._insert_batch(batch)
                            batch = []
                            
                            # Progress update
                            if self.stats['total_processed'] % 5000 == 0:
                                print(f"Processed {self.stats['total_processed']} proteins...")
                    else:
                        self.stats['errors'] += 1
                
                # Insert remaining documents
                if batch:
                    self._insert_batch(batch)
        
        except Exception as e:
            print(f"Error reading file: {e}")
            self.stats['errors'] += 1
    
    def _insert_batch(self, batch: List[Dict]) -> None:
        """
        Insert a batch of documents into MongoDB.
        
        Args:
            batch: List of protein documents to insert
        """
        try:
            if batch:
                result = self.mongo_client.proteins.insert_many(batch, ordered=False)
                self.stats['total_inserted'] += len(result.inserted_ids)
        except Exception as e:
            print(f"Error inserting batch: {e}")
            self.stats['errors'] += 1
    
    def print_statistics(self) -> None:
        """
        Print loading statistics to console.
        """
        print(f"\n{'='*60}")
        print("LOADING STATISTICS")
        print(f"{'='*60}")
        print(f"Total rows processed:       {self.stats['total_processed']:,}")
        print(f"Total proteins inserted:    {self.stats['total_inserted']:,}")
        print(f"Proteins with EC numbers:   {self.stats['with_ec']:,} ({self._percentage(self.stats['with_ec'], self.stats['total_inserted'])}%)")
        print(f"Proteins with InterPro:     {self.stats['with_interpro']:,} ({self._percentage(self.stats['with_interpro'], self.stats['total_inserted'])}%)")
        print(f"Errors encountered:         {self.stats['errors']}")
        print(f"{'='*60}\n")
    
    def _percentage(self, part: int, total: int) -> str:
        """Calculate percentage string."""
        if total == 0:
            return "0.00"
        return f"{(part / total * 100):.2f}"


def main():
    """
    Main function to load protein data into MongoDB.
    """
    print("\n" + "="*60)
    print("PROTEIN DATA LOADER - MongoDB Import")
    print("="*60 + "\n")
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://root:password123@mongodb:27017/')
    mongo_db = os.getenv('MONGO_DB_NAME', 'protein_db')
    
    print(f"Connecting to MongoDB: {mongo_db}")
    mongo_client = MongoDBClient(uri=mongo_uri, db_name=mongo_db)
    
    if not mongo_client.check_connection():
        print("ERROR: Cannot connect to MongoDB!")
        sys.exit(1)
    
    print("✓ MongoDB connection successful\n")
    
    # Check if data already exists
    existing_count = mongo_client.proteins.count_documents({})
    if existing_count > 0:
        print(f"⚠ WARNING: Database already contains {existing_count:,} proteins")
        print("\nOptions:")
        print("  1. Clear existing data and reload (will delete everything)")
        print("  2. Skip loading (keep existing data)")
        print("  3. Continue anyway (may cause duplicate errors)\n")
        
        choice = os.getenv('RELOAD_MODE', '')
        if not choice:
            choice = input("Enter choice (1/2/3): ").strip()
        
        if choice == '1':
            print("\nClearing existing data...")
            mongo_client.proteins.delete_many({})
            mongo_client.predictions.delete_many({})
            print("✓ Existing data cleared\n")
        elif choice == '2':
            print("\n✓ Keeping existing data. Exiting.\n")
            sys.exit(0)
        else:
            print("\n⚠ Continuing with existing data (may cause errors)...\n")
    
    # Create indexes for efficient querying
    print("Creating database indexes...")
    try:
        mongo_client.proteins.create_index('identifier', unique=True)
        mongo_client.proteins.create_index('entry_name')
        mongo_client.proteins.create_index('is_labeled')
        mongo_client.proteins.create_index('ec_numbers')
        mongo_client.proteins.create_index('interpro_domains')
        print("✓ Indexes created\n")
    except Exception as e:
        if "IndexKeySpecsConflict" in str(e) or "already exists" in str(e):
            print("✓ Indexes already exist (skipping)\n")
        else:
            raise
    
    # Initialize loader
    loader = ProteinDataLoader(mongo_client)
    
    # Load data files
    data_dir = os.getenv('DATA_DIR', '/app/data')
    
    # Find all TSV files in the data directory
    tsv_files = []
    if os.path.exists(data_dir):
        tsv_files = [f for f in os.listdir(data_dir) if f.endswith('.tsv')]
    
    if not tsv_files:
        print(f"WARNING: No TSV files found in {data_dir}")
        print("Please ensure data files are mounted to /app/data in the container.")
        sys.exit(1)
    
    # Load each file
    for tsv_file in tsv_files:
        filepath = os.path.join(data_dir, tsv_file)
        loader.load_tsv_file(filepath)
    
    # Print statistics
    loader.print_statistics()
    
    # Verify the data
    print("Verifying loaded data...")
    total_count = mongo_client.proteins.count_documents({})
    labeled_count = mongo_client.proteins.count_documents({'is_labeled': True})
    unlabeled_count = mongo_client.proteins.count_documents({'is_labeled': False})
    
    print(f"✓ Total proteins in database: {total_count:,}")
    print(f"  - Labeled (with EC numbers): {labeled_count:,}")
    print(f"  - Unlabeled (no EC numbers): {unlabeled_count:,}")
    
    print("\n" + "="*60)
    print("DATA LOADING COMPLETE!")
    print("="*60 + "\n")
    
    mongo_client.close()


if __name__ == '__main__':
    main()
