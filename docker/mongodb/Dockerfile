FROM mongo:latest

# Create init script
RUN mkdir -p /docker-entrypoint-initdb.d/

# Create initialization script inline
RUN echo 'db = db.getSiblingDB("protein_db");\n\
db.createCollection("proteins");\n\
db.proteins.createIndex({ "identifier": 1 });\n\
db.proteins.createIndex({ "name": 1 });\n\
db.proteins.createIndex({ "description": "text" });' > /docker-entrypoint-initdb.d/init-mongo.js

EXPOSE 27017