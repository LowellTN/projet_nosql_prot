# Guide de Propagation de Labels

## Problème Résolu

Le problème était que la propagation de labels générait des prédictions mais ne mettait pas à jour la collection `proteins` dans MongoDB. Les statistiques de l'interface web comptaient uniquement les protéines avec `is_labeled: true`, qui ne changeait jamais.

## Changements Effectués

### 1. Mise à jour de `label_propagation.py`
- ✅ Ajout de la méthode `update_proteins_with_predictions()` qui met à jour les documents MongoDB
- ✅ Les protéines prédites reçoivent maintenant les champs :
  - `predicted_ec_numbers`: Liste des numéros EC prédits
  - `prediction_confidence`: Scores de confiance pour chaque prédiction
  - `is_predicted`: Flag booléen à `True`
  - `average_prediction_confidence`: Confiance moyenne

### 2. Mise à jour de `mongodb_client.py`
- ✅ Ajout du comptage des protéines prédites dans `get_statistics()`
- ✅ Nouveau champ `predicted_proteins` dans les statistiques
- ✅ Nouveau champ `predicted_percentage` pour le pourcentage

### 3. Mise à jour de l'interface web (`index.html`)
- ✅ Ajout d'une carte pour afficher le nombre de protéines prédites
- ✅ Ajout d'une barre de progression pour les prédictions
- ✅ Mise à jour du JavaScript pour afficher ces nouvelles données

## Comment Relancer la Propagation de Labels

### Option 1: Avec Docker Compose (Recommandé)

```bash
# Depuis le répertoire projet_nosql_prot/
docker-compose run --rm python python src/label_propagation.py
```

### Option 2: Avec Docker Exec

```bash
# Si le conteneur Python est déjà en cours d'exécution
docker-compose exec python python src/label_propagation.py
```

### Option 3: Sans Docker

```bash
# Assurez-vous que les variables d'environnement sont définies
export MONGO_URI="mongodb://root:password123@localhost:27017/"
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="password123"

python src/label_propagation.py
```

## Vérifier les Résultats

### 1. Dans l'Interface Web
- Ouvrez http://localhost:5000
- Rafraîchissez la page (F5)
- Regardez la carte "Predicted" dans le dashboard
- Vérifiez les barres de progression qui montrent maintenant :
  - Labeled proteins (vert)
  - Predicted proteins (bleu)
  - Unlabeled proteins (jaune)

### 2. Via l'API

```bash
# Statistiques globales
curl http://localhost:5000/api/mongodb/statistics

# Obtenir les prédictions pour une protéine spécifique
curl http://localhost:5000/api/predictions/PROTEIN_ID

# Liste toutes les prédictions
curl http://localhost:5000/api/predictions
```

### 3. Directement dans MongoDB

```bash
# Compter les protéines avec prédictions
docker-compose exec mongodb mongosh -u root -p password123 --authenticationDatabase admin

use protein_db
db.proteins.countDocuments({is_predicted: true})
db.predictions.countDocuments({})
```

## Paramètres de Configuration

Vous pouvez ajuster les paramètres via variables d'environnement :

```bash
# Seuil de confiance minimum (0.0 à 1.0)
export CONFIDENCE_THRESHOLD="0.3"

# Poids minimum des arêtes à considérer (0.0 à 1.0)
export MIN_EDGE_WEIGHT="0.1"

# Nombre maximum de labels par protéine
export MAX_LABELS_PER_PROTEIN="5"
```

## Debugging

### Si vous ne voyez toujours pas de changements :

1. **Vérifiez que le script s'exécute correctement**
   ```bash
   docker-compose logs python
   ```

2. **Vérifiez le nombre de protéines non labellisées avec voisins labellisés**
   - Le script affiche ce nombre au début
   - Si c'est 0, aucune prédiction ne sera générée

3. **Vérifiez les seuils**
   - Un `CONFIDENCE_THRESHOLD` trop élevé peut filtrer toutes les prédictions
   - Un `MIN_EDGE_WEIGHT` trop élevé peut exclure tous les voisins

4. **Vérifiez la base de données**
   ```bash
   # Voir un exemple de protéine prédite
   docker-compose exec mongodb mongosh -u root -p password123 --authenticationDatabase admin
   use protein_db
   db.proteins.findOne({is_predicted: true})
   ```

## Architecture des Données

### Collection `proteins`
```javascript
{
  identifier: "A0A087X1C5",
  is_labeled: false,
  is_predicted: true,  // ← NOUVEAU
  predicted_ec_numbers: ["1.1.1.1", "2.7.11.1"],  // ← NOUVEAU
  prediction_confidence: {  // ← NOUVEAU
    "1.1.1.1": 0.75,
    "2.7.11.1": 0.62
  },
  average_prediction_confidence: 0.685  // ← NOUVEAU
}
```

### Collection `predictions` (séparée)
```javascript
{
  protein_id: "A0A087X1C5",
  predicted_ec_numbers: ["1.1.1.1", "2.7.11.1"],
  confidence_scores: {
    "1.1.1.1": 0.75,
    "2.7.11.1": 0.62
  },
  average_confidence: 0.685
}
```

## Prochaines Étapes (Optionnelles)

Pour améliorer davantage le système :

1. **Endpoint pour déclencher la propagation depuis l'interface**
   ```python
   @app.route('/api/predictions/run', methods=['POST'])
   def run_label_propagation():
       # Lancer la propagation en arrière-plan
   ```

2. **Affichage des prédictions dans les détails de protéines**
   - Déjà partiellement implémenté dans l'interface

3. **Validation croisée**
   - Cacher certains labels connus
   - Prédire et comparer
   - Calculer précision/rappel

4. **Propagation itérative**
   - Utiliser les prédictions à haute confiance pour propager davantage
