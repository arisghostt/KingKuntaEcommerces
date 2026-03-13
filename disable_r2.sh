#!/bin/bash
# Script pour basculer entre R2 et stockage local

echo "=== Désactivation temporaire de R2 ==="
echo ""
echo "Commentez les variables R2 dans .env :"
echo ""
echo "# R2_ACCESS_KEY=..."
echo "# R2_SECRET_KEY=..."
echo "# R2_ENDPOINT=..."
echo "# R2_BUCKET_NAME=..."
echo ""
echo "Puis redémarrez le serveur."
echo ""
echo "Les fichiers seront stockés dans ./media/ localement."
