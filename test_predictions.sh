#!/bin/bash

# Script de test pour la propagation de labels
# Vérifie que les prédictions sont bien enregistrées et visibles

echo "============================================"
echo "Test de la Propagation de Labels"
echo "============================================"
echo ""

# Couleurs pour l'affichage
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Vérifier la connexion
echo "1. Vérification de la connexion aux services..."
HEALTH=$(curl -s http://localhost:5000/health)
MONGO_OK=$(echo $HEALTH | python3 -c "import sys, json; print(json.load(sys.stdin)['mongodb'])")
NEO4J_OK=$(echo $HEALTH | python3 -c "import sys, json; print(json.load(sys.stdin)['neo4j'])")

if [ "$MONGO_OK" = "True" ] && [ "$NEO4J_OK" = "True" ]; then
    echo -e "${GREEN}✓ MongoDB et Neo4j sont connectés${NC}"
else
    echo -e "${RED}✗ Problème de connexion aux bases de données${NC}"
    exit 1
fi

echo ""

# 2. Vérifier les statistiques AVANT
echo "2. Statistiques MongoDB..."
STATS=$(curl -s http://localhost:5000/api/mongodb/statistics)
TOTAL=$(echo $STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['total_proteins'])")
LABELED=$(echo $STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['labeled_proteins'])")
PREDICTED=$(echo $STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['predicted_proteins'])")
UNLABELED=$(echo $STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['unlabeled_proteins'])")

echo -e "   Total: ${BLUE}$TOTAL${NC}"
echo -e "   Labeled: ${GREEN}$LABELED${NC}"
echo -e "   Predicted: ${BLUE}$PREDICTED${NC}"
echo -e "   Unlabeled: $UNLABELED"

echo ""

# 3. Vérifier si des prédictions existent
if [ "$PREDICTED" -gt 0 ]; then
    echo -e "3. ${GREEN}✓ Des prédictions existent déjà ($PREDICTED protéines)${NC}"
    
    # Tester une prédiction spécifique
    echo ""
    echo "4. Test d'une prédiction spécifique..."
    
    # Récupérer une protéine prédite
    SAMPLE_PROTEIN=$(curl -s "http://localhost:5000/api/predictions?limit=1" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['predictions'][0]['protein_id'] if data['predictions'] else '')")
    
    if [ -n "$SAMPLE_PROTEIN" ]; then
        echo "   Protéine testée: $SAMPLE_PROTEIN"
        
        # Vérifier dans MongoDB
        PROTEIN_DATA=$(curl -s "http://localhost:5000/api/mongodb/protein/$SAMPLE_PROTEIN")
        IS_PREDICTED=$(echo $PROTEIN_DATA | python3 -c "import sys, json; print(json.load(sys.stdin).get('is_predicted', False))")
        PRED_EC=$(echo $PROTEIN_DATA | python3 -c "import sys, json; data = json.load(sys.stdin); print(', '.join(data.get('predicted_ec_numbers', [])))")
        
        if [ "$IS_PREDICTED" = "True" ]; then
            echo -e "   ${GREEN}✓ is_predicted = True${NC}"
            echo -e "   ${GREEN}✓ EC prédits: $PRED_EC${NC}"
        else
            echo -e "   ${RED}✗ is_predicted = False (problème!)${NC}"
        fi
        
        # Vérifier dans la collection predictions
        PRED_DATA=$(curl -s "http://localhost:5000/api/predictions/$SAMPLE_PROTEIN")
        PRED_EXISTS=$(echo $PRED_DATA | python3 -c "import sys, json; print('protein_id' in json.load(sys.stdin))")
        
        if [ "$PRED_EXISTS" = "True" ]; then
            echo -e "   ${GREEN}✓ Présent dans la collection predictions${NC}"
        else
            echo -e "   ${RED}✗ Absent de la collection predictions${NC}"
        fi
    fi
else
    echo -e "3. ${RED}✗ Aucune prédiction trouvée${NC}"
    echo ""
    echo "   Pour générer des prédictions, exécutez:"
    echo -e "   ${BLUE}docker-compose exec python python src/label_propagation.py${NC}"
fi

echo ""
echo "============================================"
echo "Test terminé"
echo "============================================"
echo ""
echo "Interface web: http://localhost:5000"
echo "Pour rafraîchir les données, appuyez sur F5 dans le navigateur"
echo ""
