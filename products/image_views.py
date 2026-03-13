import uuid
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, parser_classes
from drf_spectacular.utils import extend_schema, OpenApiExample


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
@extend_schema(
    summary="Upload product image",
    description="Upload an image file for a product. Returns the image URL.",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'image': {'type': 'string', 'format': 'binary'}
            },
            'required': ['image']
        }
    },
    responses={
        201: {
            'type': 'object',
            'properties': {
                'image_url': {'type': 'string', 'description': 'URL publique de l\'image'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'error': {'type': 'string', 'description': 'Message d\'erreur de validation'}
            }
        }
    },
    tags=['Products'],
    examples=[
        OpenApiExample(
            'Succès',
            value={'image_url': 'https://pub-xxx.r2.dev/products/images/abc123.jpg'},
            response_only=True
        ),
        OpenApiExample(
            'Erreur type',
            value={'error': 'Type non autorisé : application/pdf. Acceptés : image/jpeg, image/png, image/webp, image/gif'},
            response_only=True
        ),
    ]
)
def upload_product_image(request):
    """
    Upload et stockage d'une image produit.

    POST /api/products/upload-image/

    Règles de validation :
        - Champ obligatoire   : 'image' (multipart/form-data)
        - Types autorisés     : image/jpeg, image/png, image/webp, image/gif
        - Taille maximale     : 5 Mo
        - Nom de fichier      : UUID généré automatiquement

    Comportement selon configuration :
        - Si USE_R2=True  (variables R2 dans .env)
          → Upload vers Cloudflare R2 via ProductImageStorage
          → Retour : URL publique depuis R2 (https://...)

        - Si USE_R2=False (variables R2 absentes/vides)
          → Stockage local dans MEDIA_ROOT/products/images/
          → Retour : URL relative /media/products/images/...
          → En développement, servi par Django

    Utilisations recommandées :
        - Depuis le frontend : POST multipart/form-data avec image
        - Dans les vues : ajouter image_url à la réponse API
        - Affichage client : utiliser directement le image_url retourné

    Exemple cURL :
        curl -X POST http://localhost:8000/api/products/upload-image/ \\
             -H "Authorization: Bearer <token>" \\
             -F "image=@photo.jpg"
    """
    # ──────────────────────────────────────────────────
    # 1. Validation : présence du fichier
    # ──────────────────────────────────────────────────
    image_file = request.FILES.get('image')

    if not image_file:
        return Response(
            {'error': 'Champ "image" requis. Envoyez un fichier multipart/form-data.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ──────────────────────────────────────────────────
    # 2. Validation : type MIME
    # ──────────────────────────────────────────────────
    ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    
    if image_file.content_type not in ALLOWED_TYPES:
        return Response(
            {
                'error': f'Type non autorisé : {image_file.content_type}. '
                         f'Acceptés : {", ".join(ALLOWED_TYPES)}'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ──────────────────────────────────────────────────
    # 3. Validation : taille maximale (5 Mo)
    # ──────────────────────────────────────────────────
    MAX_SIZE = 5 * 1024 * 1024  # 5 Mo en octets

    if image_file.size > MAX_SIZE:
        size_mb = image_file.size / (1024 * 1024)
        return Response(
            {
                'error': f'Fichier trop volumineux ({size_mb:.2f} Mo). '
                         f'Maximum autorisé : 5 Mo.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ──────────────────────────────────────────────────
    # 4. Génération d'un nom unique
    # ──────────────────────────────────────────────────
    # Extraire l'extension du fichier original
    ext = image_file.name.rsplit('.', 1)[-1].lower() if '.' in image_file.name else 'jpg'
    
    # UUID garantit l'unicité et évite les injections
    unique_filename = f'{uuid.uuid4().hex}.{ext}'

    # ──────────────────────────────────────────────────
    # 5. Upload selon la configuration active
    # ──────────────────────────────────────────────────
    try:
        if getattr(settings, 'USE_R2', False):
            # ── Mode R2 : upload vers Cloudflare ──────────
            from core.storage import ProductImageStorage
            storage = ProductImageStorage()
            saved_name = storage.save(unique_filename, image_file)
            image_url = storage.url(saved_name)
            # image_url = https://pub-<hash>.r2.dev/products/images/<uuid>.jpg
        else:
            # ── Mode local : stockage FileSystem ──────────
            path = f'products/images/{unique_filename}'
            saved = default_storage.save(path, ContentFile(image_file.read()))
            image_url = request.build_absolute_uri(settings.MEDIA_URL + saved)
            # image_url = http://localhost:8000/media/products/images/<uuid>.jpg

        return Response(
            {'image_url': image_url},
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        error_str = str(e)

        if '403' in error_str or 'Forbidden' in error_str:
            return Response(
                {
                    'error': 'Accès R2 refusé (403). Vérifiez : '
                             '1) Clés R2 valides avec permissions Read+Write, '
                             '2) R2_ENDPOINT sans slash final, '
                             '3) Bucket existant et accessible.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        elif '404' in error_str or 'NoSuchBucket' in error_str:
            return Response(
                {'error': f'Bucket R2 introuvable : {settings.AWS_STORAGE_BUCKET_NAME}'},
                status=status.HTTP_404_NOT_FOUND
            )
        elif 'InvalidAccessKeyId' in error_str:
            return Response(
                {'error': 'Clé R2_ACCESS_KEY invalide ou expirée.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        else:
            return Response(
                {'error': f'Erreur lors de l\'upload : {error_str}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ────────────────────────────────────────────────────
# Classe APIView — pour compatibilité avec ancien code
# ────────────────────────────────────────────────────

class ProductImageUploadView(APIView):
    """
    Classe APIView pour upload produit (compatibilité rétro).

    Même fonctionnalité que la fonction vue upload_product_image(),
    mais en tant que classe APIView pour cohérence avec le codebase.

    Note : La fonction décorée @api_view est recommandée pour du code
    nouveau. Cette classe est maintenue pour compatibilité.
    """

    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Upload product image",
        description="Upload an image file for a product. Returns the image URL.",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'image': {'type': 'string', 'format': 'binary'}
                },
                'required': ['image']
            }
        },
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'image_url': {'type': 'string'}
                }
            }
        },
        tags=['Products']
    )
    def post(self, request):
        """Appeler la vue fonction upload_product_image"""
        # Réutiliser la logique depuis la fonction décorée
        image_file = request.FILES.get('image')

        if not image_file:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        
        if image_file.content_type not in ALLOWED_TYPES:
            return Response(
                {
                    'error': f'Invalid type: {image_file.content_type}. '
                             f'Allowed: {", ".join(ALLOWED_TYPES)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        MAX_SIZE = 5 * 1024 * 1024

        if image_file.size > MAX_SIZE:
            return Response(
                {'error': f'File too large ({image_file.size / (1024 * 1024):.2f} MB). Max: 5 MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ext = image_file.name.rsplit('.', 1)[-1].lower() if '.' in image_file.name else 'jpg'
        unique_filename = f'{uuid.uuid4().hex}.{ext}'

        try:
            if getattr(settings, 'USE_R2', False):
                # ── Mode R2 : upload vers Cloudflare ──────────
                from core.storage import ProductImageStorage
                storage = ProductImageStorage()
                saved_name = storage.save(unique_filename, image_file)
                image_url = storage.url(saved_name)
                # image_url = https://pub-<hash>.r2.dev/products/images/<uuid>.jpg
            else:
                # ── Mode local : stockage FileSystem ──────────
                path = f'products/images/{unique_filename}'
                saved = default_storage.save(path, ContentFile(image_file.read()))
                image_url = request.build_absolute_uri(settings.MEDIA_URL + saved)
                # image_url = http://localhost:8000/media/products/images/<uuid>.jpg

            return Response(
                {'image_url': image_url},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            error_str = str(e)

            if '403' in error_str or 'Forbidden' in error_str:
                return Response(
                    {
                        'error': 'R2 access denied (403). Check: '
                                 '1) Valid R2 keys with Read+Write permissions, '
                                 '2) R2_ENDPOINT without trailing slash, '
                                 '3) Bucket exists and is accessible.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            elif '404' in error_str or 'NoSuchBucket' in error_str:
                return Response(
                    {'error': f'R2 bucket not found: {settings.AWS_STORAGE_BUCKET_NAME}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            elif 'InvalidAccessKeyId' in error_str:
                return Response(
                    {'error': 'R2_ACCESS_KEY invalid or expired.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            else:
                return Response(
                    {'error': f'Upload error: {error_str}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
