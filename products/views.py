from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiExample, extend_schema

from .models import Category, Product, ProductGalleryImage, ProductVariant
from .serializers import CategorySerializer, ProductSerializer, ProductVariantSerializer


class ProductListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @extend_schema(summary='List products', responses={200: ProductSerializer(many=True)}, tags=['Products'])
    def get(self, request):
        queryset = Product.objects.select_related('category').prefetch_related('gallery_images', 'variants')
        search = request.query_params.get('search')
        status_filter = request.query_params.get('status')
        category_id = request.query_params.get('category_id')
        if search:
            queryset = queryset.filter(name__icontains=search)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return Response(ProductSerializer(queryset, many=True, context={'request': request}).data)

    @extend_schema(
        summary='Create product',
        request=ProductSerializer,
        responses={201: ProductSerializer},
        examples=[OpenApiExample('Product Example', value={'name': 'Wireless Headphones', 'price': '99.99', 'stock': 25})],
        tags=['Products'],
    )
    def post(self, request):
        serializer = ProductSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(ProductSerializer(product, context={'request': request}).data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self, pk):
        return Product.objects.select_related('category').prefetch_related('gallery_images', 'variants').filter(pk=pk).first()

    def _append_gallery_images(self, product, files):
        next_sort = product.gallery_images.count()
        for offset, image in enumerate(files, start=1):
            ProductGalleryImage.objects.create(product=product, image=image, sort_order=next_sort + offset)

    @extend_schema(summary='Get product', responses={200: ProductSerializer}, tags=['Products'])
    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(product, context={'request': request}).data)

    @extend_schema(summary='Update product', request=ProductSerializer, responses={200: ProductSerializer}, tags=['Products'])
    def put(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        payload = request.data.copy()
        payload.pop('gallery_images', None)
        image_file = request.FILES.get('image')
        gallery_files = request.FILES.getlist('gallery_images')
        serializer = ProductSerializer(product, data=payload, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        if image_file is not None:
            product.image = image_file
            product.save(update_fields=['image', 'updated_at'])
        if gallery_files:
            self._append_gallery_images(product, gallery_files)
        return Response(ProductSerializer(self.get_object(pk), context={'request': request}).data)

    @extend_schema(summary='Delete product', responses={204: None}, tags=['Products'])
    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductVariantListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(summary='List product variants', tags=['Products'])
    def get(self, request, pk):
        product = Product.objects.filter(pk=pk).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductVariantSerializer(product.variants.all(), many=True).data)

    @extend_schema(summary='Create product variant', request=ProductVariantSerializer, responses={201: ProductVariantSerializer}, tags=['Products'])
    def post(self, request, pk):
        product = Product.objects.filter(pk=pk).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductVariantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant = ProductVariant.objects.create(product=product, **serializer.validated_data)
        return Response(ProductVariantSerializer(variant).data, status=status.HTTP_201_CREATED)


class ProductVariantDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk, variant_id):
        return ProductVariant.objects.filter(product_id=pk, pk=variant_id).first()

    @extend_schema(summary='Get product variant', tags=['Products'])
    def get(self, request, pk, variant_id):
        variant = self.get_object(pk, variant_id)
        if not variant:
            return Response({'error': 'Variant not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductVariantSerializer(variant).data)

    @extend_schema(summary='Update product variant', request=ProductVariantSerializer, responses={200: ProductVariantSerializer}, tags=['Products'])
    def put(self, request, pk, variant_id):
        variant = self.get_object(pk, variant_id)
        if not variant:
            return Response({'error': 'Variant not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductVariantSerializer(variant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(summary='Delete product variant', responses={204: None}, tags=['Products'])
    def delete(self, request, pk, variant_id):
        variant = self.get_object(pk, variant_id)
        if not variant:
            return Response({'error': 'Variant not found'}, status=status.HTTP_404_NOT_FOUND)
        variant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductGalleryImagesDeleteView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(summary='Delete selected gallery images', tags=['Products'])
    def post(self, request, pk):
        product = Product.objects.filter(pk=pk).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        images = request.data.get('images', []) or []
        deleted = 0
        for gallery_image in product.gallery_images.all():
            if not gallery_image.image:
                continue
            try:
                image_url = gallery_image.image.url
            except Exception:
                continue

            # Normaliser la comparaison : comparer les fins d'URL
            # pour être compatible local (/media/...) et R2 (https://...)
            matched = any(
                str(candidate).strip('/').endswith(
                    image_url.strip('/').split('/')[-1]  # comparer le nom du fichier
                )
                for candidate in images
            ) or image_url in images

            if matched:
                # Supprimer le fichier physique (local) ou l'objet R2
                try:
                    gallery_image.image.delete(save=False)
                except Exception:
                    pass  # Continuer même si la suppression R2 échoue
                gallery_image.delete()
                deleted += 1
        return Response({'deleted': deleted}, status=status.HTTP_200_OK)


class ProductMainImageClearView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(summary='Clear main product image', tags=['Products'])
    def post(self, request, pk):
        product = Product.objects.filter(pk=pk).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        if product.image:
            try:
                product.image.delete(save=False)
            except Exception:
                pass  # Log mais ne pas bloquer
        product.image = None
        product.save(update_fields=['image', 'updated_at'])
        return Response({'success': True}, status=status.HTTP_200_OK)


class CategoryListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(summary='List categories', responses={200: CategorySerializer(many=True)}, tags=['categories'])
    def get(self, request):
        return Response(CategorySerializer(Category.objects.all(), many=True).data)

    @extend_schema(summary='Create category', request=CategorySerializer, responses={201: CategorySerializer}, tags=['categories'])
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(summary='Get category', responses={200: CategorySerializer}, tags=['categories'])
    def get(self, request, pk):
        category = Category.objects.filter(pk=pk).first()
        if not category:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CategorySerializer(category).data)

    @extend_schema(summary='Update category', request=CategorySerializer, responses={200: CategorySerializer}, tags=['categories'])
    def put(self, request, pk):
        category = Category.objects.filter(pk=pk).first()
        if not category:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(summary='Partial update category', request=CategorySerializer, responses={200: CategorySerializer}, tags=['categories'])
    def patch(self, request, pk):
        category = Category.objects.filter(pk=pk).first()
        if not category:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(summary='Delete category', responses={204: None}, tags=['categories'])
    def delete(self, request, pk):
        category = Category.objects.filter(pk=pk).first()
        if not category:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
