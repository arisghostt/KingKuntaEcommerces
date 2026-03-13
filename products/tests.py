from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Product


class CategoryDeleteRouteTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name="To Delete")

    def test_delete_category_with_trailing_slash(self):
        response = self.client.delete(f"/api/categories/{self.category.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_category_without_trailing_slash(self):
        response = self.client.delete(f"/api/categories/{self.category.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class CategoryAuthTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Public Category")

    def test_category_list_is_public(self):
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_category_delete_requires_auth(self):
        response = self.client.delete(f"/api/categories/{self.category.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProductGalleryUploadTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="gallery_tester", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name="Gallery Category")
        self.product = Product.objects.create(
            name="Gallery Product",
            category=self.category,
            price="10.00",
            stock=5,
            status="active",
            rating="4.0",
        )

    @patch('storages.backends.s3boto3.S3Boto3Storage.save')
    @patch('storages.backends.s3boto3.S3Boto3Storage.url')
    def test_update_product_with_multiple_gallery_images(
        self, mock_url, mock_save
    ):
        mock_save.return_value = 'products/gallery/test.gif'
        mock_url.return_value = 'https://pub-xxx.r2.dev/products/gallery/test.gif'
        
        image1 = SimpleUploadedFile(
            "image1.gif",
            (
                b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
                b"\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00"
                b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
            ),
            content_type="image/gif",
        )
        image2 = SimpleUploadedFile(
            "image2.gif",
            (
                b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
                b"\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00"
                b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
            ),
            content_type="image/gif",
        )

        update_response = self.client.put(
            f"/api/products/{self.product.id}/",
            {
                "name": self.product.name,
                "category": self.category.name,
                "price": "10.00",
                "stock": 5,
                "status": "active",
                "rating": "4.0",
                "gallery_images": [image1, image2],
            },
            format="multipart",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        detail_response = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(detail_response.data["gallery_images"]), 2)

    @patch('storages.backends.s3boto3.S3Boto3Storage.save')
    @patch('storages.backends.s3boto3.S3Boto3Storage.url')
    def test_delete_selected_gallery_images(
        self, mock_url, mock_save
    ):
        mock_save.return_value = 'products/gallery/test.gif'
        mock_url.return_value = 'https://pub-xxx.r2.dev/products/gallery/test.gif'
        
        image1 = SimpleUploadedFile(
            "image1.gif",
            (
                b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
                b"\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00"
                b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
            ),
            content_type="image/gif",
        )
        image2 = SimpleUploadedFile(
            "image2.gif",
            (
                b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
                b"\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00"
                b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
            ),
            content_type="image/gif",
        )

        update_response = self.client.put(
            f"/api/products/{self.product.id}/",
            {
                "name": self.product.name,
                "category": self.category.name,
                "price": "10.00",
                "stock": 5,
                "status": "active",
                "rating": "4.0",
                "gallery_images": [image1, image2],
            },
            format="multipart",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        detail_response = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(detail_response.data["gallery_images"]), 2)

        first_image_url = detail_response.data["gallery_images"][0]

        delete_response = self.client.post(
            f"/api/products/{self.product.id}/gallery-images/delete/",
            {"images": [first_image_url]},
            format="json",
        )
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delete_response.data["deleted"], 1)

        refreshed_detail_response = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(refreshed_detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(refreshed_detail_response.data["gallery_images"]), 1)

    @patch('storages.backends.s3boto3.S3Boto3Storage.save')
    @patch('storages.backends.s3boto3.S3Boto3Storage.url')
    def test_clear_main_image(
        self, mock_url, mock_save
    ):
        mock_save.return_value = 'products/main.gif'
        mock_url.return_value = 'https://pub-xxx.r2.dev/products/main.gif'
        
        main_image = SimpleUploadedFile(
            "main.gif",
            (
                b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
                b"\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00"
                b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
            ),
            content_type="image/gif",
        )

        update_response = self.client.put(
            f"/api/products/{self.product.id}/",
            {
                "name": self.product.name,
                "category": self.category.name,
                "price": "10.00",
                "stock": 5,
                "status": "active",
                "rating": "4.0",
                "image": main_image,
            },
            format="multipart",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        clear_response = self.client.post(
            f"/api/products/{self.product.id}/main-image/clear/",
            {},
            format="json",
        )
        self.assertEqual(clear_response.status_code, status.HTTP_200_OK)

        detail_response = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertIsNone(detail_response.data["image"])



class ProductImageUploadTests(APITestCase):
    """Tests pour l'endpoint /api/products/upload-image/"""
    
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='uploader', password='pass12345'
        )
        self.client.force_authenticate(user=self.user)

    def test_upload_requires_auth(self):
        """L'upload d'image nécessite une authentification"""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/products/upload-image/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_missing_file_returns_400(self):
        """L'upload sans fichier retourne une erreur 400"""
        response = self.client.post('/api/products/upload-image/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @patch('storages.backends.s3boto3.S3Boto3Storage.save')
    @patch('storages.backends.s3boto3.S3Boto3Storage.url')
    def test_upload_invalid_type_returns_400(self, mock_url, mock_save):
        """L'upload d'un fichier non-image retourne une erreur 400"""
        fake_pdf = SimpleUploadedFile(
            'doc.pdf', b'%PDF-1.4', content_type='application/pdf'
        )
        response = self.client.post(
            '/api/products/upload-image/',
            {'image': fake_pdf},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Type non autorisé', response.data['error'])
