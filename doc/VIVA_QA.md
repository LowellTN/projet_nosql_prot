# Questions de soutenance – Projet NoSQL Protéines

## Questions sur MongoDB (Document Store)

### Q: Comment avez-vous structuré les documents MongoDB ?
**R:** Collection `proteins` avec schéma flexible : `identifier`, `entry_name`, `name`, `organism`, `sequence`, `ec_numbers` (array), `interpro_domains` (array), `is_labeled` (booléen dérivé). Les arrays permettent de stocker plusieurs EC/domaines sans jointures.

### Q: Comment répondez-vous à l'exigence « une seule requête » du sujet ?
**R:** Pipeline d'agrégation MongoDB. Exemple pour `/api/mongodb/statistics` :
```javascript
db.proteins.aggregate([
  { $match: { is_labeled: true } },
  { $unwind: "$ec_numbers" },
  { $group: { _id: "$ec_numbers", count: { $sum: 1 } } },
  { $sort: { count: -1 } },
  { $limit: 10 }
])
```
Une seule requête retourne tous les top EC avec comptages.

### Q: Quels index avez-vous créés et pourquoi ?
**R:**
- `identifier` (unique) → accès direct par ID, dédoublonnage
- `entry_name` → recherche par nom d'entrée
- `is_labeled` → filtrage labeled/unlabeled rapide
- `ec_numbers`, `interpro_domains` → requêtes sur ces champs, agrégations

### Q: Comment gérez-vous les données volumineuses (scalabilité MongoDB) ?
**R:** Insertion par batch (1000 docs), index pour queries rapides, possibilité de sharding par `identifier` si volume > 10M documents.

## Questions sur Neo4j (Graph Database)

### Q: Pourquoi des arêtes dirigées si le graphe est non dirigé (sujet) ?
**R:** Contrainte Neo4j : toutes les relations sont dirigées. On les traite comme non dirigées en requête Cypher avec `-[:SIMILAR_TO]-` (pattern bidirectionnel).

### Q: Comment calculez-vous la similarité Jaccard ?
**R:** Code Python :
```python
intersection = set(domains_P1) & set(domains_P2)
union = set(domains_P1) | set(domains_P2)
jaccard = len(intersection) / len(union)
```
Exemple sujet : P1=(d1,d2,d3,d4), P2=(d1,d3,d5) → J = 2/5 = 0,4

### Q: Complexité O(N²) : comment gérez-vous ?
**R:**
- Filtre : protéines sans domaines exclues
- Seuil : `SIMILARITY_THRESHOLD=0,1` élimine arêtes faibles
- Batch writes : `UNWIND` pour 1000 arêtes/requête
- Pour >100k : index inversé domaine→[protéines] réduirait candidats

### Q: Quelles requêtes Cypher clés pour la Tâche 3 ?
**R:**
- Voisins profondeur 1 :
  ```cypher
  MATCH (p:Protein {id: $id})-[r:SIMILAR_TO]-(n)
  WHERE r.weight >= 0.1
  RETURN p, n, r.weight
  ```
- Stats protéines isolées :
  ```cypher
  MATCH (p:Protein)
  WHERE NOT (p)-[:SIMILAR_TO]-()
  RETURN count(p)
  ```

### Q: Comment visualisez-vous le voisinage (Tâche 3.4) ?
**R:** Endpoint `/api/neo4j/neighborhood/{id}` retourne JSON nodes/edges. Template HTML affiche avec bibliothèque simple (ou Neo4j Browser pour démo).

## Questions sur la Propagation de Labels

### Q: Pourquoi label propagation et pas un classifieur ML classique ?
**R:**
- Peu de labels (568k annotés vs 229M non annotés)
- Graphe de similarité avec homophilie forte (voisins similaires → mêmes fonctions)
- Simple, explicable, pas d'entraînement complexe

### Q: Comment calculez-vous la confiance des prédictions ?
**R:** Pour une protéine P non annotée, pour chaque EC :
```
confiance(EC) = Σ(poids_arête × a_EC(voisin)) / Σ(poids_arête)
```
où `a_EC(voisin)` = 1 si voisin a cet EC, 0 sinon.
On garde top-K au-dessus de `CONFIDENCE_THRESHOLD=0,3`.

### Q: Que signifient les paramètres MIN_EDGE_WEIGHT et CONFIDENCE_THRESHOLD ?
**R:**
- `MIN_EDGE_WEIGHT=0,1` : ignore arêtes faibles (bruit)
- `CONFIDENCE_THRESHOLD=0,3` : confiance minimale pour assigner un EC (précision vs rappel)
- `MAX_LABELS_PER_PROTEIN=5` : limite réaliste (évite sur-prédiction)

### Q: Où stockez-vous les prédictions ?
**R:** Double stockage pour cohérence :
- MongoDB : collection `predictions` (protein_id, predicted_ec_numbers, confidence_scores)
- Neo4j : propriétés sur nœuds `Protein` (`predicted_ec_numbers`, `prediction_confidence_ec/values`)

## Questions sur l'implémentation

### Q: Pourquoi Docker Compose ?
**R:** Orchestration reproductible : MongoDB + Neo4j + API Python avec healthchecks (ordre démarrage), volumes (persistence), réseau interne (DNS `mongodb`, `neo4j`).

### Q: Comment testez-vous sur petit jeu de données ?
**R:** Variable `PROTEIN_LIMIT=1000` dans `graph_builder.py` → graphe réduit en 5 min vs 2h pour 50k protéines.

### Q: Comment synchronisez-vous MongoDB et Neo4j ?
**R:**
1. MongoDB source de vérité (TSV → Mongo)
2. Neo4j dérive : lecture Mongo → création nœuds/arêtes
3. Prédictions écrites dans les deux (API expose les deux vues)

## Questions sur les choix techniques

### Q: Pourquoi Jaccard et pas autre mesure ?
**R:** Sujet impose Jaccard. Avantages : normalisé [0,1], insensible à la taille, adapté aux ensembles discrets (domaines). Alternatives : Tanimoto (comptages), cosinus (vecteurs).

### Q: Pourquoi pas GO terms (sujet les mentionne) ?
**R:** Implémentation centrée EC (format simple). GO terms = évolution future avec hiérarchie ontologique (plus complexe).

### Q: Quelle est votre « solution big data » (Tâche 2) ?
**R:**
- Batch processing (insertion/calcul par lots)
- Filtrage sélectif (protéines avec domaines)
- Seuils configurables (SIMILARITY_THRESHOLD)
- Index stratégiques (Mongo + Neo4j)
- Architecture scalable Docker (peut ajouter workers)
- Piste >1M protéines : MinHash/LSH, Spark/Neo4j Enterprise

## Questions sur les statistiques (Tâche 3.3)

### Q: Quelles statistiques calculez-vous ?
**R:**
- **MongoDB** : total protéines, labeled/unlabeled counts, top 10 EC, top 10 domaines, longueur moyenne séquence
- **Neo4j** : total nœuds/arêtes, protéines isolées, degré moyen, top 10 protéines connectées
- **Combiné** : `/api/statistics/overview` agrège les deux

### Q: Comment comptez-vous les protéines isolées ?
**R:** Cypher :
```cypher
MATCH (p:Protein)
WHERE NOT (p)-[:SIMILAR_TO]-()
RETURN count(p)
```

### Q: Comment gérez-vous les protéines avec trop/trop peu de voisins ?
**R:** **Seuils adaptatifs** implémentés pour répondre à l'exigence du professeur :
- **Problème** : certaines protéines ont 200+ voisins (seuil 0.1 trop bas), d'autres seulement 2-3 (seuil trop haut)
- **Solution** : algorithme adaptatif qui ajuste automatiquement le seuil par protéine

**Endpoint API** :
```bash
# Obtenir le seuil recommandé pour une protéine
curl http://localhost:5000/api/neo4j/adaptive-threshold/A0A087X1C5?target_neighbors=10

# Obtenir les voisins avec seuil adaptatif automatique
curl http://localhost:5000/api/neo4j/neighbors-adaptive/A0A087X1C5?target_neighbors=15
```

**Algorithme Cypher** :
```cypher
-- Récupérer tous les poids triés (décroissant) pour une protéine
MATCH (p:Protein {id: 'A0A087X1C5'})-[r:SIMILAR_TO]-()
WITH p, r
ORDER BY r.weight DESC
WITH p, collect(r.weight) as weights, count(r) as total
RETURN 
  p.id,
  total as total_neighbors,
  weights[9] as threshold_for_10_neighbors,  -- 10e poids = seuil pour garder top 10
  weights[0] as max_weight,
  weights[size(weights)-1] as min_weight
```

**Stratégie** :
- Si protéine a ≤10 voisins → seuil = poids minimal (garde tout)
- Si protéine a >10 voisins → seuil = poids du 10e voisin (limite aux top 10)
- Paramètre `target_neighbors` ajustable (défaut : 10)

**Résultat JSON** :
```json
{
  "protein_id": "A0A087X1C5",
  "total_neighbors": 47,
  "recommended_threshold": 0.285,
  "strategy": "adaptive_threshold",
  "message": "Protein has 47 neighbors, using adaptive threshold",
  "weight_distribution": {
    "max": 0.912,
    "min": 0.102,
    "median": 0.334
  }
}
```

## Questions sur l'interface graphique

### Q: Quelle interface avez-vous implémentée ?
**R:** Template HTML/JavaScript simple :
- Recherche protéines (MongoDB + Neo4j)
- Affichage détails (EC, domaines, prédictions)
- Visualisation voisinage (récupère JSON, affiche graphe)
- Bonus : +3 pts pour GUI (critère sujet)

### Q: Pourquoi pas Angular/React/D3 (sujet les mentionne) ?
**R:** Choix pragmatique : template HTML suffit pour démo fonctionnelle. Évolution possible avec framework dédié.

## Questions pièges / avancées

### Q: Et si deux protéines n'ont aucun domaine en commun ?
**R:** Jaccard = 0, pas d'arête créée (sous seuil 0,1). Normal : pas de similarité de composition.

### Q: Comment gérez-vous les mises à jour incrémentales ?
**R:** Actuellement rebuild complet. Évolution : détection nouvelles protéines → recalcul arêtes uniquement pour celles-ci (index inversé domaines).

### Q: Performances : combien de temps pour 50k protéines ?
**R:**
- Chargement MongoDB : ~5 min
- Construction graphe : ~2h (48k nœuds, 250k arêtes)
- Propagation : ~10 min
Total : ~2h15 pour workflow complet

### Q: Qualité des prédictions : comment évaluez-vous ?
**R:** Métriques potentielles : précision/rappel sur subset annoté caché, validation croisée. Implémentation actuelle : confiance moyenne reportée (0,3–0,8 typique).
