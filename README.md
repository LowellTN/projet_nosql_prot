# Projet NoSQL Protein Annotation

## Overview

This project aims to query and analyze protein data using MongoDB and Neo4j. With the rapid growth of protein sequences in public databases, the need for efficient data storage, querying, and analysis has become paramount. This project leverages NoSQL technologies to facilitate the management and exploration of protein data.

## Project Structure

The project is organized as follows:

```
projet_nosql_prot
├── docker
│   ├── mongodb
│   │   └── Dockerfile
│   ├── neo4j
│   │   └── Dockerfile
│   └── python
│       ├── Dockerfile
│       └── requirements.txt
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── README.md
├── subject.md
└── task.md
```

## Technologies Used

- **MongoDB**: A NoSQL document database used for storing protein data.
- **Neo4j**: A graph database used for constructing and querying protein-protein networks.
- **Python**: The programming language used for data processing, analysis, and interaction with the databases.

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd projet_nosql_prot
   ```

2. **Build the Docker images**:
   ```
   docker-compose build
   ```

3. **Start the services**:
   ```
   docker-compose up
   ```

4. **Access the services**:
   - MongoDB: Accessible at `mongodb://localhost:27017`
   - Neo4j: Accessible at `http://localhost:7474`
   - Python application: Accessible as defined in the `docker-compose.yml`

## Environment Variables

Refer to the `.env.example` file for the required environment variables. Copy this file to `.env` and fill in the necessary values.

## Additional Information

For more details on the project objectives and requirements, please refer to `subject.md` and `task.md`.