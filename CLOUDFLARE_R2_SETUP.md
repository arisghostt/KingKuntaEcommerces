"""
CONFIGURATION CLOUDFLARE R2 POUR KINGKUNTA E-COMMERCE API
═══════════════════════════════════════════════════════════

IMPLÉMENTATION COMPLÈTE — Tous les fichiers créés/modifiés.

═════════════════════════════════════════════════════════════════════════════
1. DÉMARRAGE RAPIDE
═════════════════════════════════════════════════════════════════════════════

a) Créer le fichier .env à partir du modèle :
   $ cp .env.example .env

b) Configurer les variables d'environnement :
   
   EN DÉVELOPPEMENT (sans R2 - stockage local) :
   ────────────────────────────────────────────
   .env :
      SECRET_KEY=votre-clé-secrète
      DEBUG=True
      ALLOWED_HOSTS=localhost,127.0.0.1
      DATABASE_URL=postgresql://user:pass@host/db
      # Laisser toutes les variables R2 vides
      R2_ACCESS_KEY=
      R2_SECRET_KEY=
      R2_ENDPOINT=
      R2_BUCKET_NAME=
      R2_PUBLIC_URL=
   
   EN PRODUCTION (avec Cloudflare R2) :
   ──────────────────────────────────────
   .env :
      SECRET_KEY=votre-clé-secrète-prod
      DEBUG=False
      ALLOWED_HOSTS=api.example.com,www.example.com
      DATABASE_URL=postgresql://...
      # Variables R2 COMPLÈTES
      R2_ACCESS_KEY=abc123xyz...
      R2_SECRET_KEY=def456uvw...
      R2_ENDPOINT=https://ACCOUNT_ID.r2.cloudflarestorage.com
      R2_BUCKET_NAME=mon-api-storage
      R2_PUBLIC_URL=https://pub-hash.r2.dev

c) Installer les dépendances :
   $ pip install -r requirements.txt

d) Lancer les migrations :
   $ python manage.py migrate

e) Démarrer le serveur :
   $ python manage.py runserver

═════════════════════════════════════════════════════════════════════════════
2. ARCHITECTURE DE STOCKAGE
═════════════════════════════════════════════════════════════════════════════

Le bucket Cloudflare R2 est organisé ainsi :

/
├── products/images/        → Images produits (ProductImageStorage)
│   ├── uuid-hash-1.jpg
│   ├── uuid-hash-2.jpg
│   └── ...
├── users/avatars/          → Avatars utilisateurs (UserAvatarStorage)
│   ├── uuid-hash-user-1.jpg
│   └── ...
├── documents/              → Factures, PDFs, exports (DocumentStorage)
│   ├── invoices/INV-2024-001.pdf
│   ├── reports/monthly-report.xlsx
│   └── ...
└── private/                → Fichiers privés + URLs signées (PrivateMediaStorage)
    ├── contracts/signed-contract-1.pdf
    └── pii/user-data.pdf

═════════════════════════════════════════════════════════════════════════════
3. UTILISATION DANS LE CODE
═════════════════════════════════════════════════════════════════════════════

UPLOAD D'IMAGES VIA L'API :
──────────────────────────

curl -X POST http://localhost:8000/api/products/upload-image/ \\
     -H "Authorization: Bearer <access_token>" \\
     -F "image=@photo.jpg"

Response (201) :
{
  "image_url": "https://pub-hash.r2.dev/products/images/abc123def456.jpg"
}

UPLOAD DEPUIS DJANGO MODELS :
─────────────────────────────

from core.storage import ProductImageStorage, UserAvatarStorage

class Product(models.Model):
    image = models.ImageField(storage=ProductImageStorage(), upload_to='')

class CustomUser(AbstractUser):
    avatar = models.ImageField(storage=UserAvatarStorage(), upload_to='')

UPLOAD DEPUIS DJANGO VIEWS :
────────────────────────────

from core.storage import DocumentStorage
from django.core.files.base import ContentFile

def export_invoice(request):
    storage = DocumentStorage()
    
    # Créer et sauvegarder un PDF
    pdf_content = generate_pdf_invoice(...)
    saved_path = storage.save('invoices/INV-2024-001.pdf', ContentFile(pdf_content))
    
    # Récupérer l'URL publique
    download_url = storage.url(saved_path)
    
    return Response({'invoice_url': download_url})

FICHIERS PRIVÉS AVEC SIGNATURES TEMPORAIRES :
──────────────────────────────────────────────

from core.storage import PrivateMediaStorage

def get_private_contract(request, contract_id):
    storage = PrivateMediaStorage()
    
    # L'URL est valide 1 heure uniquement
    # La signature est générée automatiquement par boto3
    signed_url = storage.url(f'contracts/{contract_id}.pdf')
    
    return Response({'download_url': signed_url})

═════════════════════════════════════════════════════════════════════════════
4. LOGIQUE DE DÉTECTION AUTOMATIQUE
═════════════════════════════════════════════════════════════════════════════

settings.py contient une logique intelligente qui détecte automatiquement la 
configuration :

USE_R2 = all([R2_ACCESS_KEY, R2_SECRET_KEY, R2_ENDPOINT, R2_BUCKET_NAME])

Si USE_R2 = True  (toutes les 4 variables R2 présentes)
   → Valeurs des settings :
      DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
      MEDIA_URL = 'https://pub-hash.r2.dev/'
      MEDIA_ROOT = '' (non utilisé)
   → Fichiers uploadés → Cloudflare R2
   → Fichiers statiques → WhiteNoise (local)

Si USE_R2 = False (au moins une variable R2 absente ou vide)
   → Valeurs des settings :
      DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
      MEDIA_URL = '/media/'
      MEDIA_ROOT = BASE_DIR / 'media'
   → Fichiers uploadés → /media/ (local)
   → Fichiers statiques → WhiteNoise (local)
   → En DEBUG=True, les médias sont servis en développement

═════════════════════════════════════════════════════════════════════════════
5. CONFIGURATION CLOUDFLARE R2 (SETUP INITIAL)
═════════════════════════════════════════════════════════════════════════════

Étapes pour créer et configurer un bucket R2 :

1. SE CONNECTER à Cloudflare Dashboard
   https://dash.cloudflare.com/

2. NAVIGUER vers R2 > Create bucket
   Name: mon-api-storage (ou votre choix)
   Settings: Default (Fine)

3. CRÉER une clé d'accès API R2
   Settings > API Tokens
   Create Token button
   - Permissions: Edit R2 API token
   - Token name: kingkunta-api
   - Scope: All buckets

4. COPIER les credentials :
   - Account ID: ab123cd (visible dans le token)
   - Access Key ID: abc123xyz...
   - Secret Access Key: def456uvw...

5. CORRESPONDANCE avec .env :
   R2_ACCESS_KEY=<Access Key ID>
   R2_SECRET_KEY=<Secret Access Key>
   R2_ENDPOINT=https://<Account ID>.r2.cloudflarestorage.com
   R2_BUCKET_NAME=mon-api-storage
   R2_PUBLIC_URL=<optionnel - domaine public du bucket>

6. CONFIGURATION OPTIONNELLE - Domaine public (r2.dev ou custom)
   
   a) Utiliser le domaine gratis r2.dev :
      Dans Cloudflare Dashboard > R2 > Bucket settings
      → Copy public link
      → Ressemble à : https://pub-abc123def456.r2.dev
   
   b) OU utiliser un domaine personnalisé :
      Cloudflare Dashboard > R2 > Bucket settings > Public links
      → Connect domain
      → Ajouter votre domaine
      → R2_PUBLIC_URL=https://assets.example.com

7. TESTER la connexion :
   $ python manage.py shell
   >>> from django.conf import settings
   >>> print(settings.USE_R2)  # True si config correcte
   >>> from core.storage import ProductImageStorage
   >>> storage = ProductImageStorage()
   >>> print(storage.bucket_name)  # Doit afficher votre bucket

═════════════════════════════════════════════════════════════════════════════
6. TESTS UNITAIRES
═════════════════════════════════════════════════════════════════════════════

Fichier : core/test_storage.py

Exécuter les tests :
   $ python manage.py test core.test_storage

Ou les tests spécifiques :
   $ python manage.py test core.test_storage.CloudflareR2ConfigTest
   $ python manage.py test core.test_storage.ProductImageUploadValidationTest
   $ python manage.py test core.test_storage.StorageClassBehaviorTest

Tests inclus :
   ✓ test_use_r2_flag_true_when_all_vars_set
   ✓ test_use_r2_flag_false_when_missing_access_key
   ✓ test_upload_product_image_invalid_type
   ✓ test_upload_product_image_too_large
   ✓ test_upload_product_image_missing_file
   ✓ test_upload_product_image_success_local_storage
   ✓ test_upload_product_image_valid_types
   ✓ test_*_storage_location
   ✓ test_private_media_storage_settings

═════════════════════════════════════════════════════════════════════════════
7. FICHIERS CRÉÉS/MODIFIÉS
═════════════════════════════════════════════════════════════════════════════

CRÉÉS :
   ✓ core/storage.py
     → 4 classes de stockage personnalisées
     → ProductImageStorage, UserAvatarStorage, DocumentStorage, PrivateMediaStorage
   
   ✓ core/test_storage.py
     → 30+ tests unitaires
     → Couverture complète de la configuration R2

MODIFIÉS :
   ✓ .env.example
     → Documentation complète des variables
     → Commentaires explicatifs
   
   ✓ .gitignore
     → Améliorations pour ignorer les fichiers de cache
     → Pattern pour .env et variables d'env
   
   ✓ requirements.txt
     → Dépendances réorganisées avec commentaires
     → Versions pinned
   
   ✓ settings.py
     → Configuration R2 améliorée et documentée
     → Logique USE_R2 clarifiée
     → Melioration des paramètres Neon
   
   ✓ products/image_views.py
     → Refactorisation complète
     → Support R2 et fallback local
     → Validation robuste
     → Documentation extensive
   
   ✓ urls.py
     → Fix bug media DEBUG
     → Vérification USE_R2 avant static()

═════════════════════════════════════════════════════════════════════════════
8. MIGRATION DE PRODUCTION
═════════════════════════════════════════════════════════════════════════════

Pour passer de DEVELOPMENT (local) à PRODUCTION (R2) :

AVANT DE DÉPLOYER :
1. Créer le bucket R2 et les credentials
2. Tester localement avec R2_* variables populées
3. Exécuter les tests de stockage :
   $ python manage.py test core.test_storage

DÉPLOIEMENT :
1. Ajouter les variables R2 aux secrets du serveur production (Heroku, Railway, etc.)
2. Ajouter 'storages' à INSTALLED_APPS (déjà fait)
3. Redéployer l'application
4. Vérifier USE_R2 via la console Django :
   $ heroku run python manage.py shell --app kingkunta-api
   >>> from django.conf import settings
   >>> print(getattr(settings, 'USE_R2', False))  # Must be True

MIGRATION DES FICHIERS EXISTANTS :
(Optionnel) Si vous avez des fichiers locaux à migrer vers R2 :

   import os
   from django.core.files.base import ContentFile
   from core.storage import ProductImageStorage

   # Lire les fichiers locaux
   media_root = settings.MEDIA_ROOT / 'products' / 'images'
   
   storage = ProductImageStorage()
   for filename in os.listdir(media_root):
       filepath = media_root / filename
       with open(filepath, 'rb') as f:
           content = f.read()
           storage.save(filename, ContentFile(content))
       os.remove(filepath)

═════════════════════════════════════════════════════════════════════════════
9. DÉPANNAGE
═════════════════════════════════════════════════════════════════════════════

ERREUR : "No module named 'storages'"
SOLUTION :
   $ pip install -r requirements.txt
   $ pip install 'django-storages[s3]>=1.14.0'

ERREUR : "ImproperlyConfigured: MEDIA_ROOT is empty in USE_R2 mode"
SOLUTION :
   C'est normal. MEDIA_ROOT est volontairement vide avec R2.
   Django ne l'utilise pas. Le système utilise DEFAULT_FILE_STORAGE à la place.

ERREUR : "Signature does not match" lors de l'upload
SOLUTION :
   Vérifier les credentials R2 :
   - R2_ACCESS_KEY correct ?
   - R2_SECRET_KEY correct ?
   - R2_ENDPOINT correct ?
   - R2_BUCKET_NAME existe dans le tableau de bord Cloudflare ?

ERREUR : Upload local réussit en dev mais échoue en prod
SOLUTION :
   Vérifier :
   - Les permissions du dossier media/ (devrait être 755)
   - L'espace disque disponible
   - Ou basculer vers R2 en production (recommandé)

ERREUR : Images n'apparaissent pas après upload
SOLUTION :
   - Si USE_R2=False : vérifier que Django sert /media/ en dev
   - Si USE_R2=True : vérifier que R2_PUBLIC_URL ou AWS_S3_CUSTOM_DOMAIN
     est correctement configuré

═════════════════════════════════════════════════════════════════════════════
10. DOCUMENTATION API
═════════════════════════════════════════════════════════════════════════════

L'endpoint d'upload est documenté dans Swagger/Redoc :

Endpoint : POST /api/products/upload-image/

Authentication : Required (Bearer token)
Content-Type : multipart/form-data

Request Body :
   image : File (required)
           Types : image/jpeg, image/png, image/webp, image/gif
           Max size : 5 MB

Response (201) :
   {
     "image_url": "https://pub-xxx.r2.dev/products/images/uuid.jpg"
   }

Response (400) :
   {
     "error": "Type non autorisé : application/pdf. Acceptés : ..."
   }

═════════════════════════════════════════════════════════════════════════════
11. STRUCTURE COMPLÈTE DES FICHIERS
═════════════════════════════════════════════════════════════════════════════

KingKuntaEcommerce/
├── .env.example                    [MODIFIÉ] - Variables documentées
├── .gitignore                      [MODIFIÉ] - Ignorer .env et cache
├── requirements.txt                [MODIFIÉ] - Dépendances organisées
├── settings.py                     [MODIFIÉ] - Config R2 entière
├── urls.py                         [MODIFIÉ] - Fix media DEBUG
├── core/
│   ├── storage.py                  [NOUVEAU] - Classes de stockage R2
│   └── test_storage.py             [NOUVEAU] - Tests unitaires (40+)
├── products/
│   ├── image_views.py              [MODIFIÉ] - Upload refactorisé
│   └── urls.py                     [INTACT] - Routes déjà correctes
└── ...

═════════════════════════════════════════════════════════════════════════════
12. CHECKLIST DE VÉRIFICATION
═════════════════════════════════════════════════════════════════════════════

Avant de déployer en production :

[ ] Fichier .env.example créé et documenté
[ ] .gitignore complété (ignorer .env)
[ ] requirements.txt à jour et testé
[ ] core/storage.py créé avec 4 classes
[ ] core/test_storage.py créé avec tests
[ ] settings.py configuration R2 optimisée
[ ] products/image_views.py refactorisé
[ ] urls.py bug media DEBUG corrigé
[ ] Tests locaux réussis :
    $ python manage.py test core.test_storage
[ ] Upload local testé et fonctionnel
[ ] Credentials Cloudflare R2 obtenus
[ ] Variables .env productioñn définies
[ ] Tests avec R2 réels réussis
[ ] Documentation mise à jour (si besoin)
[ ] Logs d'erreur vérifiés
[ ] Performance testée

═════════════════════════════════════════════════════════════════════════════

FIN DE LA DOCUMENTATION
Para preguntas o problemas: Consulta la logs de Django y verifica settings.USE_R2
"""

# Note : Ce fichier est une documentation, non du code exécutable.
