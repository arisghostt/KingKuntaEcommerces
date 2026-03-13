"""
Django settings for KingKuntaEcommerce project.
"""
import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-your-secret-key-here-change-in-production'
)

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else []

# ─────────────────────────────────────────────────────────
# APPLICATIONS
# ─────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'storages',          # ← NOUVEAU : django-storages pour R2

    # Local apps
    'core',
    'inventory',
    'products',
    'parties',
    'procurement',
    'sales',
    'finance',
    'users',
    'shipping',
    'promotions',
    'reviews',
    'wishlist',
    'returns_app',
    'search_app',
    'taxes',
    'webhooks',
]

# ─────────────────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'

# ─────────────────────────────────────────────────────────
# BASE DE DONNÉES — Neon PostgreSQL
# ─────────────────────────────────────────────────────────
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise RuntimeError(
        'DATABASE_URL est requis et doit pointer vers la base Neon PostgreSQL.'
    )

DATABASES = {
    'default': dj_database_url.parse(database_url)
}

# Optimisation connexion Neon (serverless PostgreSQL)
default_conn_max_age = '0' if DEBUG else '600'
DATABASES['default']['CONN_MAX_AGE'] = int(os.getenv('DB_CONN_MAX_AGE', default_conn_max_age))
DATABASES['default']['CONN_HEALTH_CHECKS'] = True

if DATABASES['default'].get('ENGINE', '').endswith('postgresql'):
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS'].update({
        'connect_timeout':     int(os.getenv('DB_CONNECT_TIMEOUT', '15')),
        'keepalives':          int(os.getenv('DB_KEEPALIVES', '1')),
        'keepalives_idle':     int(os.getenv('DB_KEEPALIVES_IDLE', '30')),
        'keepalives_interval': int(os.getenv('DB_KEEPALIVES_INTERVAL', '10')),
        'keepalives_count':    int(os.getenv('DB_KEEPALIVES_COUNT', '5')),
    })

# ─────────────────────────────────────────────────────────
# CLOUDFLARE R2 — Stockage fichiers & médias
# ─────────────────────────────────────────────────────────
# Configuration automatique : R2 s'active seulement si les 4
# variables d'environnement sont définies dans .env
#
# Structure du bucket R2 :
#   /products/images/     → Images produits (via ProductImageStorage)
#   /users/avatars/       → Avatars utilisateurs (via UserAvatarStorage)
#   /documents/           → Factures, PDFs, exports (via DocumentStorage)
#   /private/             → Fichiers privés avec signatures (via PrivateMediaStorage)
#
# EN DÉVELOPPEMENT (sans R2) :
#   - Fichiers médias sauvegardés dans BASE_DIR/media/
#   - Servis par Django en tant que /media/
#
# EN PRODUCTION (avec R2) :
#   - Fichiers uploadés → Cloudflare R2 bucket
#   - URLs publiques → domaine custom ou r2.dev
#   - Templates/CSS/JS statiques → WhiteNoise (local, optimisé)

# Lire les variables R2 depuis .env
_R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY', '').strip()
_R2_SECRET_KEY = os.getenv('R2_SECRET_KEY', '').strip()
_R2_ENDPOINT = os.getenv('R2_ENDPOINT', '').strip().rstrip('/')
_R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', '').strip()
_R2_PUBLIC_URL = os.getenv('R2_PUBLIC_URL', '').strip()

# Détection automatique : USE_R2 == True si les 4 variables clés sont présentes
USE_R2 = all([_R2_ACCESS_KEY, _R2_SECRET_KEY, _R2_ENDPOINT, _R2_BUCKET_NAME])

if USE_R2:
    # ── Paramètres boto3 / S3-compatible pour R2 ────────
    AWS_ACCESS_KEY_ID = _R2_ACCESS_KEY
    AWS_SECRET_ACCESS_KEY = _R2_SECRET_KEY
    AWS_STORAGE_BUCKET_NAME = _R2_BUCKET_NAME
    AWS_S3_ENDPOINT_URL = _R2_ENDPOINT
    
    # R2 utilise 'auto' comme région (pas de régions AWS)
    AWS_S3_REGION_NAME = 'auto'
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_S3_ADDRESSING_STYLE = 'path'
    AWS_S3_VERIFY = True
    
    # Configuration du domaine public
    # Si R2_PUBLIC_URL défini → utiliser domaine public/custom (r2.dev)
    # Sinon → URLs générées depuis endpoint (requiert signature)
    if _R2_PUBLIC_URL:
        AWS_S3_CUSTOM_DOMAIN = _R2_PUBLIC_URL.replace('https://', '').rstrip('/')
    else:
        AWS_S3_CUSTOM_DOMAIN = None
    
    # R2 n'implémente pas les ACLs S3 standard
    AWS_DEFAULT_ACL = None
    
    # Pas d'authentication par query string pour les fichiers publics
    AWS_QUERYSTRING_AUTH = False
    
    # UUID dans les noms garantit l'unicité sans HeadObject
    AWS_S3_FILE_OVERWRITE = True
    
    # Cache-Control pour les médias (images, PDFs)
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',  # 1 jour
    }
    
    # ── Fichiers statiques → WhiteNoise (local) ────────
    # Django admin CSS, JS, images restent locaux pour optimiser les coûts
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    
    # ── Fichiers médias → Cloudflare R2 ────────────────
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # STORAGES dict pour Django 4.2+
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
    else:
        MEDIA_URL = f'{_R2_ENDPOINT}/{_R2_BUCKET_NAME}/'
    
    # MEDIA_ROOT requis par Django même avec R2
    MEDIA_ROOT = BASE_DIR / 'media'

else:
    # ── Fallback stockage local (développement sans R2) ──
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    
    # STORAGES dict pour Django 4.2+
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# ─────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'users.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─────────────────────────────────────────────────────────
# INTERNATIONALISATION
# ─────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────────────────
# DJANGO REST FRAMEWORK
# ─────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'exceptions.api_exception_handler',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authentication.CookieJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('Bearer', 'Token'),
}

# ─────────────────────────────────────────────────────────
# DRF SPECTACULAR (Swagger)
# ─────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'KingKunta E-commerce API',
    'DESCRIPTION': 'A comprehensive e-commerce API.',
    'VERSION': '1.0.0',
    'TAGS': [
        {'name': 'auth'},
        {'name': 'categories'},
        {'name': 'Products'},
        {'name': 'cart'},
        {'name': 'Sales'},
        {'name': 'Inventory'},
        {'name': 'Finance'},
        {'name': 'Procurement'},
        {'name': 'Parties'},
        {'name': 'events'},
        {'name': 'roles'},
        {'name': 'users'},
        {'name': 'permissions'},
        {'name': 'notifications'},
        {'name': 'Core'},
        {'name': 'admin'},
    ],
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SECURITY': [{'bearerAuth': []}],
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'bearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'Enter: Bearer <access_token>',
            },
        },
    },
    'SWAGGER_UI_SETTINGS': {'persistAuthorization': True},
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': [],
    'SERVE_PUBLIC': True,
    'DEFAULT_GENERATOR_CLASS': 'drf_spectacular.generators.SchemaGenerator',
}

# ─────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
CORS_ALLOW_CREDENTIALS = True
