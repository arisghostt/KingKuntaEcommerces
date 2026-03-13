"""
Cloudflare R2 Storage Classes

Classes de stockage personnalisées pour organiser les fichiers
dans des dossiers dédiés au sein du bucket R2.

Chaque classe hérite de S3Boto3Storage et définit un 'location'
(préfixe/dossier) pour isoler les types de fichiers.

Usage dans models.py :
    from core.storage import ProductImageStorage
    image = models.ImageField(storage=ProductImageStorage())

Configuration requise dans settings.py :
    - USE_R2 = True
    - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    - AWS_STORAGE_BUCKET_NAME, AWS_S3_ENDPOINT_URL
    - AWS_S3_CUSTOM_DOMAIN (optionnel, pour URLs publiques)
"""

from storages.backends.s3boto3 import S3Boto3Storage


class ProductImageStorage(S3Boto3Storage):
    """
    Images principales des produits.
    
    Dossier R2 : products/images/
    Usage : image = models.ImageField(storage=ProductImageStorage())
    
    Caractéristiques :
        - file_overwrite = True : UUID garantit l'unicité
        - Évite HeadObject qui cause 403 sur R2
        - URLs publiques via AWS_S3_CUSTOM_DOMAIN
    """
    location = 'products/images'
    file_overwrite = True


class ProductGalleryStorage(S3Boto3Storage):
    """
    Images de galerie des produits.
    
    Dossier R2 : products/gallery/
    Usage : image = models.ImageField(storage=ProductGalleryStorage())
    
    Utilisé par ProductGalleryImage pour les images secondaires
    affichées dans les carrousels produit.
    """
    location = 'products/gallery'
    file_overwrite = True


class UserAvatarStorage(S3Boto3Storage):
    """
    Avatars utilisateurs.
    
    Dossier R2 : users/avatars/
    Usage : avatar = models.ImageField(storage=UserAvatarStorage())
    
    Pour les photos de profil des utilisateurs (clients, admins).
    """
    location = 'users/avatars'
    file_overwrite = True


class DocumentStorage(S3Boto3Storage):
    """
    Documents : PDFs, factures, exports.
    
    Dossier R2 : documents/
    Usage : file = models.FileField(storage=DocumentStorage())
    
    Pour les fichiers non-image : factures PDF, exports CSV,
    rapports générés, etc.
    """
    location = 'documents'
    file_overwrite = True


class PrivateMediaStorage(S3Boto3Storage):
    """
    Fichiers privés avec URLs signées (expiration 1h).
    
    Dossier R2 : private/
    Usage : file = models.FileField(storage=PrivateMediaStorage())
    
    Caractéristiques :
        - default_acl = None : pas d'accès public
        - custom_domain = False : force les URLs signées
        - querystring_auth = True : ajoute signature dans l'URL
        - querystring_expire = 3600 : expiration après 1 heure
    
    Cas d'usage :
        - Documents confidentiels (contrats, données personnelles)
        - Fichiers temporaires (exports utilisateur)
        - Médias nécessitant authentification
    """
    location = 'private'
    default_acl = None
    file_overwrite = True
    custom_domain = False

    def __init__(self, *args, **kwargs):
        kwargs['querystring_auth'] = True
        kwargs['querystring_expire'] = 3600  # 1 heure
        super().__init__(*args, **kwargs)
