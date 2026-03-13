ÉTAPE 1 — Vérifier les permissions du token API R2 :
  1. Cloudflare Dashboard → R2 → Manage R2 API Tokens
  2. Trouver le token avec Access Key : 30ac2c241fb0e4647ac2a1f0e19eb086
  3. Vérifier qu'il a : "Object Read & Write" sur le bucket "kingkunta-cdn" (pas juste Write)
  4. Si Access Denied persiste → créer un nouveau token :
     → Create API Token
     → Permissions : Object Read & Write
     → Specify bucket : kingkunta-cdn
     → Copier le nouvel Access Key ID et Secret Access Key
     → Mettre à jour R2_ACCESS_KEY et R2_SECRET_KEY dans .env

ÉTAPE 2 — Activer l'accès public (pour R2_PUBLIC_URL) :
  1. R2 → kingkunta-cdn → Settings
  2. Public Access → Allow Access
  3. Copier l'URL publique : https://pub-XXXX.r2.dev
  4. Mettre à jour R2_PUBLIC_URL dans .env
  5. Redémarrer Django : python manage.py runserver

ÉTAPE 3 — Configurer CORS pour l'upload depuis le frontend :
  R2 → kingkunta-cdn → Settings → CORS Policy :
  [
    {
      "AllowedOrigins": [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://votredomaine.com"
      ],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3600
    }
  ]

ÉTAPE 4 — Tester après corrections :
  python manage.py check_r2
  # Résultat attendu :
  # ✅ Bucket "kingkunta-cdn" accessible
  # ✅ Écriture OK
  # ✅ Lecture OK
  # ✅ Nettoyage OK
