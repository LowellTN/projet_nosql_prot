FROM neo4j:5.13.0

# Set environment variables for authentication
ENV NEO4J_AUTH=neo4j/password123

# Configure memory settings
ENV NEO4J_server_memory_pagecache_size=512M
ENV NEO4J_server_memory_heap_initial__size=512M
ENV NEO4J_server_memory_heap_max__size=1G

# Accept license (if using enterprise, otherwise not needed for community)
ENV NEO4J_ACCEPT_LICENSE_AGREEMENT=yes

EXPOSE 7474 7687