# FAQ - Questions Fréquentes

## Questions sur la Propagation de Labels

### Q: Je lance la propagation de labels mais je ne vois aucun changement dans l'interface. Pourquoi ?

**R:** Ce problème a été résolu ! Assurez-vous d'utiliser la version corrigée du code. Les changements apparaissent maintenant immédiatement après :

1. Lancer la propagation : `docker-compose exec python python src/label_propagation.py`
2. Rafraîchir la page web (F5)
3. Observer la carte "Predicted" dans le dashboard

Si vous ne voyez toujours rien, vérifiez :
- Le script s'est-il terminé sans erreur ?
- Y avait-il des protéines non labellisées avec des voisins labellisés ?
- Les seuils de confiance ne sont-ils pas trop élevés ?

### Q: Pourquoi "Updated 0 proteins" s'affiche quand je relance le script ?

**R:** C'est normal ! MongoDB utilise `update_one()` qui ne compte comme "modifié" que si la valeur change. Si vous relancez le script avec les mêmes paramètres :
- Les **mêmes protéines** reçoivent les **mêmes prédictions**
- MongoDB détecte qu'il n'y a pas de changement réel
- `modified_count = 0` mais les données sont toujours là

Pour forcer une mise à jour, changez les paramètres :
```bash
export CONFIDENCE_THRESHOLD=0.4  # Augmenter le seuil
docker-compose exec python python src/label_propagation.py
```

### Q: Comment vérifier que les prédictions sont bien enregistrées ?

**R:** Plusieurs méthodes :

**1. Via le script de test :**
```bash
./test_predictions.sh
```

**2. Via l'API :**
```bash
curl http://localhost:5000/api/mongodb/statistics | python3 -m json.tool
```
Regardez le champ `predicted_proteins`

**3. Via l'interface web :**
- Ouvrez http://localhost:5000
- Regardez la carte "Predicted" dans le dashboard

**4. Directement dans MongoDB :**
```bash
docker-compose exec mongodb mongosh -u root -p password123 \
  --authenticationDatabase admin \
  --eval 'use protein_db; db.proteins.countDocuments({is_predicted: true})'
```

### Q: Quelle est la différence entre `labeled` et `predicted` ?

**R:**
- **Labeled (Labelisé)** : Protéines avec des annotations EC provenant de la base de données UniProt (vérité terrain)
- **Predicted (Prédit)** : Protéines sans annotations d'origine, mais qui ont reçu des prédictions grâce à l'algorithme de propagation de labels

Une protéine ne peut pas être les deux en même temps.

### Q: Pourquoi certaines protéines ne reçoivent-elles pas de prédiction ?

**R:** Pour qu'une protéine reçoive une prédiction, elle doit :

1. **Être non labellisée** (`is_labeled = false`)
2. **Avoir des voisins labellisés** dans le graphe
3. **Avoir des voisins avec un poids d'arête ≥ MIN_EDGE_WEIGHT** (défaut: 0.1)
4. **Obtenir une confiance ≥ CONFIDENCE_THRESHOLD** (défaut: 0.3)

Si aucune de ces conditions n'est remplie, la protéine reste sans prédiction.

### Q: Comment ajuster les paramètres de la propagation ?

**R:** Modifiez le fichier `.env` :

```bash
# Dans .env
CONFIDENCE_THRESHOLD=0.3      # Seuil de confiance (0.0 à 1.0)
MIN_EDGE_WEIGHT=0.1          # Poids minimum des arêtes
MAX_LABELS_PER_PROTEIN=5     # Maximum de labels par protéine
```

Puis relancez :
```bash
docker-compose exec python python src/label_propagation.py
```

**Conseils :**
- **CONFIDENCE_THRESHOLD trop haut** → Moins de prédictions mais plus fiables
- **CONFIDENCE_THRESHOLD trop bas** → Plus de prédictions mais moins fiables
- **MIN_EDGE_WEIGHT trop haut** → Moins de voisins considérés
- **MIN_EDGE_WEIGHT trop bas** → Plus de bruit dans les prédictions

## Questions sur l'Interface Web

### Q: L'interface web ne se charge pas

**R:** Vérifiez que tous les services sont démarrés :
```bash
docker-compose ps
```

Tous les services doivent être "Up" et "healthy". Si ce n'est pas le cas :
```bash
docker-compose restart
docker-compose logs python
```

### Q: Les statistiques sont à 0 ou vides

**R:** Vous devez d'abord charger les données :
```bash
# 1. Charger les données dans MongoDB
docker-compose exec python python src/data_loader.py

# 2. Construire le graphe Neo4j
docker-compose exec python python src/graph_builder.py

# 3. (Optionnel) Générer des prédictions
docker-compose exec python python src/label_propagation.py
```

### Q: Le graphe ne s'affiche pas

**R:** Assurez-vous d'avoir chargé la bibliothèque vis-network. Si le problème persiste :
1. Ouvrez la console du navigateur (F12)
2. Regardez les erreurs
3. Vérifiez que Neo4j est bien connecté : http://localhost:5000/health

## Questions sur les Performances

### Q: La propagation de labels est-elle lente ?

**R:** Temps typiques :
- **3,000 protéines** : ~30 secondes
- **10,000 protéines** : ~2 minutes
- **50,000 protéines** : ~15 minutes

Si c'est plus lent :
- Vérifiez que les index existent dans MongoDB
- Augmentez `MIN_EDGE_WEIGHT` pour réduire le nombre de voisins
- Vérifiez les ressources Docker (RAM, CPU)

### Q: Le graphe prend beaucoup de temps à se charger

**R:** Le graphe peut être volumineux. Pour améliorer les performances :
- Limitez la profondeur (`depth=1` au lieu de `depth=2`)
- Augmentez `min_weight` pour filtrer les arêtes faibles
- Réduisez `limit` dans les paramètres de requête

### Q: MongoDB/Neo4j manquent de mémoire

**R:** Ajustez les ressources dans `docker-compose.yml` :

```yaml
services:
  mongodb:
    deploy:
      resources:
        limits:
          memory: 2G  # Augmentez si nécessaire
```

## Questions sur les Données

### Q: Combien de protéines devrais-je avoir ?

**R:** Avec le dataset complet UniProt :
- **Total** : ~50,000 protéines
- **Labeled** : ~20,000 (40%)
- **Unlabeled** : ~30,000 (60%)
- **Arêtes** : ~250,000

Si vous avez beaucoup moins, vous utilisez peut-être un sous-ensemble réduit.

### Q: D'où viennent les données ?

**R:** Les données proviennent de **UniProt** (Universal Protein Resource) :
- Fichier TSV avec identifiants, noms, organismes, séquences
- Domaines InterPro pour les annotations fonctionnelles
- Numéros EC pour les enzymes
- Similitudes calculées via les domaines partagés (Jaccard)

### Q: Puis-je utiliser mes propres données ?

**R:** Oui ! Modifiez `src/data_loader.py` pour charger votre format. Le fichier TSV doit contenir :
- `Identifier` : ID unique
- `Name` : Nom de la protéine
- `Organism` : Espèce
- `Sequence` : Séquence d'acides aminés
- `InterPro Domains` : Domaines (séparés par `;`)
- `EC Numbers` : Numéros EC (séparés par `;`)

## Questions sur le Déploiement

### Q: Comment sauvegarder mes données ?

**R:** Utilisez les volumes Docker :
```bash
# Sauvegarder MongoDB
docker-compose exec mongodb mongodump --out /backup

# Sauvegarder Neo4j
docker-compose exec neo4j neo4j-admin backup --to=/backup
```

### Q: Comment réinitialiser complètement le projet ?

**R:**
```bash
# Arrêter et supprimer tous les conteneurs et volumes
docker-compose down -v

# Redémarrer
docker-compose up -d

# Recharger les données
docker-compose exec python python src/data_loader.py
docker-compose exec python python src/graph_builder.py
docker-compose exec python python src/label_propagation.py
```

### Q: Puis-je exécuter ceci en production ?

**R:** Pour la production, modifiez :
1. Les mots de passe dans `.env` (utilisez des mots de passe forts)
2. Activez l'authentification dans Neo4j
3. Désactivez le mode debug de Flask
4. Utilisez un serveur WSGI (gunicorn, uwsgi)
5. Ajoutez HTTPS via nginx/Traefik
6. Configurez les sauvegardes automatiques

## Support

Si vous avez d'autres questions :
1. Consultez [LABEL_PROPAGATION_GUIDE.md](LABEL_PROPAGATION_GUIDE.md)
2. Lisez [CORRECTIONS_SUMMARY.md](CORRECTIONS_SUMMARY.md)
3. Vérifiez [PROBLEME_RESOLU.md](PROBLEME_RESOLU.md)
4. Exécutez `./test_predictions.sh` pour diagnostiquer les problèmes
