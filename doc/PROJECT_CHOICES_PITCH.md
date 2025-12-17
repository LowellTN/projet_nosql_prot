# Présentation du projet – 5 minutes chrono

## Introduction (30 sec)
Contexte du sujet : UniProt contient 568 000 protéines annotées manuellement mais plus de 229 millions sans annotations fonctionnelles. Notre objectif est de réduire cet écart en utilisant deux bases NoSQL complémentaires et un algorithme de propagation de labels sur graphe.

## Tâche 1 : Document Store avec MongoDB (1 min)

### Implémentation
- **Collection `proteins`** avec schéma flexible :
  - Identifiants, noms, organisme, séquence
  - `ec_numbers` (array) → protéines annotées (labeled)
  - `interpro_domains` (array) → domaines protéiques
  - Flag `is_labeled` dérivé automatiquement
- **Index créés** : `identifier` (unique), `entry_name`, `is_labeled`, `ec_numbers`, `interpro_domains`

### Réponse aux exigences du sujet
✓ **Requêtes complexes en un seul appel** : pipeline d'agrégation pour `/api/mongodb/statistics` (`$match`, `$unwind`, `$group`, `$sort`)  
✓ **Recherche multi-attributs** : regex sur identifier/name/description avec index  
✓ **Vue applicative complète** : un document rassemble toutes les propriétés nécessaires

### Choix techniques
- Parsing TSV → insertion par lots (1000 documents/batch)
- Gestion des doublons par index unique
- Calcul de métriques (longueur séquence, présence EC/domaines)

## Tâche 2 : Construction du graphe Neo4j (1 min 30)

### Modélisation
- **Nœuds `Protein`** : copie des attributs essentiels depuis Mongo (id, name, is_labeled, ec_numbers, interpro_domains)
- **Arêtes `SIMILAR_TO {weight}`** : poids = coefficient de Jaccard entre ensembles de domaines InterPro
- **Index Neo4j** : `Protein(id)` et `Protein(is_labeled)`

### Algorithme de similarité (exigence sujet)
Jaccard entre protéines P1 et P2 :
```
J(P1,P2) = |domaines_P1 ∩ domaines_P2| / |domaines_P1 ∪ domaines_P2|
```
Exemple du sujet : P1=(d1,d2,d3,d4), P2=(d1,d3,d5) → J = 2/5 = 0,4

### Solution « big data » implémentée
- **Filtrage** : uniquement protéines avec domaines (réduit N)
- **Seuil de similarité** : `SIMILARITY_THRESHOLD = 0,1` pour élaguer les arêtes faibles
- **Calcul par lots** : comparaisons par paires, écriture batch via Cypher `UNWIND`
- **Complexité** : O(N²) naïf, optimisé par filtrage + seuil
- **Limite configurable** : `PROTEIN_LIMIT` pour tests (1000 protéines → ~5 min)

### Résultat
Graphe pondéré non dirigé (stocké dirigé Neo4j, interrogé bidirectionnel) avec nœuds labeled/unlabeled.

## Tâche 3 : Requêtes sur les deux bases (1 min)

### MongoDB
- **Recherche** : `/api/mongodb/search?q=cytochrome` (identifier OU name OU description)
- **Détail** : `/api/mongodb/protein/{id}`
- **Statistiques** : counts labeled/unlabeled, top EC numbers, top domaines

### Neo4j
- **Recherche** : `/api/neo4j/search?q=kinase` (id OU name)
- **Voisins** : `/api/neo4j/neighbors/{id}?depth=1|2&min_weight=0.1`
- **Visualisation** : `/api/neo4j/neighborhood/{id}` → payload nodes/edges pour UI
- **Statistiques** : total nœuds/arêtes, protéines isolées, degré moyen, top connectées

### Interface graphique
Template HTML simple avec recherche, affichage détails, et visualisation voisinage (bonus +3 pts).

## Tâche 4 : Propagation de labels (1 min)

### Problème
Classification multi-étiquette : prédire EC numbers pour protéines unlabeled.

### Algorithme implémenté
Pour chaque protéine non annotée :
1. Collecter EC des voisins annotés
2. Vote pondéré par poids d'arête (`SIMILAR_TO.weight`)
3. Normaliser → score de confiance par EC
4. Retenir top-K au-dessus de `CONFIDENCE_THRESHOLD = 0,3`

Paramètres : `MIN_EDGE_WEIGHT=0,1`, `MAX_LABELS_PER_PROTEIN=5`

### Stockage
- Collection Mongo `predictions` : protein_id, predicted_ec_numbers, confidence_scores
- Propriétés Neo4j : `predicted_ec_numbers`, `prediction_confidence_ec/values`

### Justification
- Simple, explicable, adapté aux graphes de similarité (homophilie)
- Pas d'entraînement lourd contrairement aux classifieurs supervisés

## Démo rapide (30 sec)

1. `docker-compose up -d` → healthcheck OK
2. `data_loader.py` → 50 000 protéines en MongoDB
3. `graph_builder.py` → 48 500 nœuds, 250 000 arêtes
4. `label_propagation.py` → 25 000 prédictions
5. API `/api/statistics/overview` → stats combinées
6. Neo4j Browser → voisinage d'une protéine

## Points forts & limites (30 sec)

### Réalisé
✓ Document store + graph DB fonctionnels  
✓ Requêtes complexes en un appel (pipelines Mongo)  
✓ Graphe domaine-based avec Jaccard (conforme sujet)  
✓ Propagation de labels multi-étiquettes  
✓ Statistiques (labeled/unlabeled, isolées)  
✓ Interface de visualisation  

### Limites connues
- Complexité O(N²) : gérable jusqu'à ~100k protéines, au-delà nécessite index inversé domaine→protéines
- Similarité uniquement sur domaines (pas séquence/profils HMM)
- UI basique (pas Angular/React/D3 avancé)

### Pistes
- Ajout GO terms (multi-source propagation)
- MinHash/LSH pour grands volumes
- Détection de communautés (APOC Neo4j)
