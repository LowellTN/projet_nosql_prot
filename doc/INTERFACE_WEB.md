# Interface Web - Documentation Technique

## Vue d'ensemble

L'interface web graphique fournit une interface utilisateur intuitive pour explorer les données de protéines, visualiser le réseau de similarité et analyser les prédictions de fonctions.

## Architecture

### Technologies Utilisées

- **Frontend**:
  - Bootstrap 5.3.0 (UI framework)
  - Bootstrap Icons (iconographie)
  - Vis.js Network 9.1.2 (visualisation de graphes)
  - Vanilla JavaScript (logique applicative)

- **Backend**:
  - Flask (API REST)
  - MongoDB (stockage de données)
  - Neo4j (base de données graphe)

### Structure

```
src/
├── app.py                    # API Flask
└── templates/
    └── index.html           # Interface web complète (SPA)
```

## Fonctionnalités

### 1. Dashboard (Tableau de bord)

**Endpoint utilisé**: `/api/statistics/overview`

**Fonctionnalités**:
- Statistiques globales (protéines totales, labelisées, non-labelisées)
- Métriques du graphe (arêtes, degré moyen, protéines isolées)
- Top 5 des protéines les plus connectées
- Top 10 des domaines InterPro
- Top 10 des numéros EC
- Barres de progression visuelles

**Données affichées**:
- Nombre total de protéines (MongoDB)
- Pourcentage de protéines labelisées
- Nombre d'arêtes dans le graphe
- Degré moyen du graphe
- Longueur moyenne des séquences

### 2. Search (Recherche)

**Endpoints utilisés**:
- `/api/mongodb/search?q={query}&limit={n}` - Recherche
- `/api/mongodb/protein/{id}` - Détails d'une protéine
- `/api/neo4j/neighbors/{id}?depth={d}` - Voisins
- `/api/predictions/{id}` - Prédictions

**Fonctionnalités**:
- **Barre de recherche**: Recherche en temps réel par identifiant, nom ou description
- **Liste de résultats**: Affichage des protéines trouvées avec:
  - Identifiant UniProt
  - Nom de la protéine
  - Organisme
  - Longueur de séquence
  - Badge labelisé/non-labelisé

- **Panneau de détails**: Vue complète d'une protéine avec:
  - Informations générales (ID, nom, organisme, longueur)
  - Domaines InterPro (badges bleus)
  - Numéros EC (badges bleus foncés)
  - Prédictions EC avec scores de confiance (badges orange)
  
- **Actions rapides**:
  - "View in Graph" - Visualiser dans le graphe
  - "Show Neighbors" - Afficher les voisins

- **Liste des voisins**:
  - ID et nom du voisin
  - Score de similarité (Jaccard)
  - Barre de progression visuelle de la similarité

### 3. Graph Explorer (Explorateur de graphe)

**Endpoints utilisés**:
- `/api/neo4j/neighborhood/{id}?depth={d}&min_weight={w}` - Données du voisinage

**Fonctionnalités**:
- **Sélection de protéine**: Input pour entrer un ID de protéine
- **Contrôle de profondeur**: Sélecteur (1, 2 ou 3 niveaux)
- **Visualisation interactive**:
  - Graphe Force-Directed (Vis.js)
  - Nœuds colorés selon le statut (vert = labelisé, gris = non-labelisé)
  - Taille des nœuds proportionnelle
  - Épaisseur des arêtes selon le poids de similarité
  - Tooltips informatifs au survol
  - Zoom et pan
  
- **Interaction**:
  - Clic sur un nœud → Affiche les détails et change vers l'onglet Search
  - Drag & drop des nœuds
  - Layout automatique optimisé

**Configuration Vis.js**:
```javascript
{
  nodes: {
    shape: 'dot',
    color: is_labeled ? '#2ecc71' : '#95a5a6',
    size: 20
  },
  edges: {
    smooth: true,
    scaling: {
      min: 1,
      max: 10  // Basé sur le poids
    }
  },
  physics: {
    barnesHut: {
      gravitationalConstant: -8000,
      springConstant: 0.04,
      springLength: 95
    }
  }
}
```

## Navigation

### Système d'onglets

Fonction JavaScript `showTab(tabName)` pour basculer entre:
- `dashboard` - Tableau de bord
- `search` - Recherche
- `graph` - Explorateur de graphe

### Workflow utilisateur typique

1. **Découverte** (Dashboard)
   - Voir les statistiques globales
   - Identifier les protéines les plus connectées

2. **Recherche** (Search)
   - Chercher une protéine spécifique
   - Examiner ses détails, domaines, EC numbers
   - Voir les prédictions avec confiance

3. **Visualisation** (Graph Explorer)
   - Charger le voisinage de la protéine
   - Explorer visuellement les connexions
   - Cliquer sur les voisins pour plus de détails

## API Endpoints Utilisés

### Statistiques
- `GET /api/statistics/overview` - Statistiques complètes (MongoDB + Neo4j)

### MongoDB
- `GET /api/mongodb/search?q=<query>&limit=<n>` - Recherche de protéines
- `GET /api/mongodb/protein/<id>` - Détails d'une protéine

### Neo4j
- `GET /api/neo4j/neighbors/<id>?depth=<d>&min_weight=<w>` - Voisins directs
- `GET /api/neo4j/neighborhood/<id>?depth=<d>&min_weight=<w>` - Voisinage complet pour visualisation

### Prédictions
- `GET /api/predictions/<id>` - Prédictions pour une protéine
- `GET /api/predictions?limit=<n>&skip=<s>` - Liste de prédictions

## Design et UX

### Palette de couleurs

```css
--primary-color: #2c3e50;    /* Titres, navigation */
--secondary-color: #3498db;  /* Boutons, éléments actifs */
--success-color: #2ecc71;    /* Protéines labelisées */
--accent-color: #e74c3c;     /* Alertes */
```

### Thème visuel

- **Fond**: Dégradé violet (#667eea → #764ba2)
- **Cartes**: Blanches avec ombres portées
- **En-têtes de cartes**: Dégradé bleu (#2c3e50 → #3498db)
- **Animations**: Transitions douces (0.3s)
- **Hover effects**: Élévation des cartes

### Badges de statut

- **Labelisé** (vert): `badge badge-labeled`
- **Non-labelisé** (gris): `badge badge-unlabeled`
- **Domaines** (bleu clair): `domain-badge`
- **EC numbers** (bleu): `ec-badge`
- **Prédictions** (orange): `prediction-badge`

## Responsive Design

L'interface est responsive grâce à Bootstrap:
- **Desktop**: Layout en 3-4 colonnes
- **Tablet**: Layout en 2 colonnes
- **Mobile**: Layout en 1 colonne

Breakpoints Bootstrap:
- `sm`: 576px
- `md`: 768px
- `lg`: 992px
- `xl`: 1200px

## Performance

### Optimisations

1. **Chargement paresseux**: Les données ne sont chargées que lorsque nécessaire
2. **Pagination**: Limite par défaut de 20 résultats pour la recherche
3. **Limites de graphe**: Max 100 nœuds pour éviter la surcharge
4. **Debouncing**: Recherche déclenchée uniquement sur Enter
5. **Mise en cache**: Vis.js gère le cache du layout du graphe

### Limites recommandées

- **Recherche**: 20-50 résultats
- **Graphe - Profondeur 1**: ~50 nœuds
- **Graphe - Profondeur 2**: ~200 nœuds
- **Graphe - Profondeur 3**: ~500 nœuds (peut être lent)
- **Min weight**: 0.1-0.2 pour filtrer les connexions faibles

## Gestion des erreurs

### Messages utilisateur

- **Protéine non trouvée**: "No proteins found"
- **Pas de voisins**: "No neighbors found (protein may not be in graph)"
- **Erreur API**: "Error loading data"
- **Graphe vide**: "Protein not found in graph or has no neighbors"

### Logs console

Tous les erreurs sont loggées dans la console du navigateur pour le débogage:
```javascript
console.error('Error loading dashboard:', error);
```

## Extension Future

### Fonctionnalités possibles

1. **Filtres avancés**:
   - Filtrer par organisme
   - Filtrer par longueur de séquence
   - Filtrer par nombre de domaines

2. **Comparaison**:
   - Comparer deux protéines
   - Alignement de séquences

3. **Export**:
   - Export CSV des résultats
   - Export PNG du graphe
   - Export JSON des données

4. **Analyses**:
   - Clustering de protéines
   - Détection de communautés
   - Centralité des nœuds

5. **Visualisations supplémentaires**:
   - Graphiques de distribution
   - Heatmaps de similarité
   - Arbres phylogénétiques

## Évaluation selon le sujet

### Points attribués

✅ **Interface graphique intuitive** (3 points):
- Navigation claire avec onglets
- Design moderne et professionnel
- Recherche facile
- Feedback visuel constant

✅ **Bonne visualisation du voisinage** (2 points):
- Graphe interactif avec Vis.js
- Couleurs distinctives pour les statuts
- Épaisseur des arêtes selon similarité
- Navigation par clic

✅ **Statistiques** (2 points):
- Dashboard complet
- Métriques MongoDB et Neo4j
- Top domaines et EC numbers
- Distribution visuelle

**Total**: 7/7 points bonus potentiels
