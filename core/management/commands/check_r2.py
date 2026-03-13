from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Vérifie la connexion et les permissions Cloudflare R2'

    TEST_KEY = 'test/check_r2_write.txt'

    def handle(self, *args, **options):
        if not getattr(settings, 'USE_R2', False):
            self.stdout.write(self.style.WARNING('USE_R2=False — mode stockage local actif'))
            return

        import boto3
        from botocore.exceptions import (
            ClientError,
            EndpointConnectionError,
            EndpointResolutionError,
            NoCredentialsError,
        )

        self.stdout.write('Test connexion R2...')

        s3 = None
        created_test_object = False
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        try:
            s3 = boto3.client(
                's3',
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )

            # TEST 1 — head_bucket (connexion + existence bucket)
            s3.head_bucket(Bucket=bucket)
            self.stdout.write(self.style.SUCCESS('✅ Connexion R2 OK'))
            self.stdout.write(self.style.SUCCESS(f'✅ Bucket "{bucket}" accessible'))

            # TEST 2 — put_object (permission Write)
            s3.put_object(
                Bucket=bucket,
                Key=self.TEST_KEY,
                Body=b'write test',
                ContentType='text/plain',
            )
            created_test_object = True
            self.stdout.write(self.style.SUCCESS('✅ Écriture OK'))

            # TEST 3 — get_object (permission Read)
            s3.get_object(Bucket=bucket, Key=self.TEST_KEY)
            self.stdout.write(self.style.SUCCESS('✅ Lecture OK'))

            # TEST 4 — URL publique
            public_domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)
            if public_domain:
                public_url = getattr(settings, 'MEDIA_URL', f'https://{public_domain}/')
                try:
                    self._head_public_url(public_url)
                    self.stdout.write(self.style.SUCCESS('✅ URL publique accessible'))
                except Exception as exc:
                    self.stdout.write(self.style.WARNING(
                        '⚠️ URL publique inaccessible — vérifiez que R2_PUBLIC_URL reste valide et publiquement accessible.'
                    ))
                    self.stdout.write(f'   → {exc}')
            else:
                self.stdout.write(self.style.WARNING(
                    '⚠️ AWS_S3_CUSTOM_DOMAIN non configuré — ajoutez R2_PUBLIC_URL (Cloudflare Dashboard → R2 → kingkunta-cdn → Settings → Public Access)'
                ))

            # TEST 5 — delete_object (nettoyage)
            s3.delete_object(Bucket=bucket, Key=self.TEST_KEY)
            created_test_object = False
            self.stdout.write(self.style.SUCCESS('✅ Nettoyage OK'))

            self.stdout.write('\n── Configuration active ──')
            self.stdout.write(f'  Endpoint  : {settings.AWS_S3_ENDPOINT_URL}')
            self.stdout.write(f'  Bucket    : {settings.AWS_STORAGE_BUCKET_NAME}')
            self.stdout.write(f'  Region    : {settings.AWS_S3_REGION_NAME}')
            self.stdout.write(f'  Signing   : {settings.AWS_S3_SIGNATURE_VERSION}')
            domain_value = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)
            domain_label = domain_value or 'non configuré'
            self.stdout.write(f'  Domain    : {domain_label}')
            media_url = getattr(settings, 'MEDIA_URL', 'non configuré')
            self.stdout.write(f'  Media URL : {media_url}')

        except NoCredentialsError:
            self.stdout.write(self.style.ERROR(
                '❌ Clés manquantes. Vérifiez R2_ACCESS_KEY et R2_SECRET_KEY dans .env'
            ))
        except (EndpointConnectionError, EndpointResolutionError) as exc:
            self.stdout.write(self.style.ERROR(
                '❌ R2_ENDPOINT incorrect. Format attendu : https://ACCOUNT_ID.r2.cloudflarestorage.com'
            ))
            self.stdout.write(f'   → {exc}')
        except ClientError as exc:
            code = exc.response['Error']['Code']
            message = exc.response['Error'].get('Message', '')
            self.stdout.write(self.style.ERROR(f'❌ Erreur R2 [{code}] : {message}'))
            if code in ('AccessDenied', '403'):
                self.stdout.write(
                    '   → Token sans permission Read ou Write. Vérifier Cloudflare Dashboard → R2 → Manage R2 API Tokens. '
                    'Le token doit avoir "Object Read & Write" sur kingkunta-cdn.'
                )
            elif code in ('NoSuchBucket', '404'):
                self.stdout.write(
                    f'   → Bucket "{bucket}" introuvable. Vérifier R2_BUCKET_NAME dans .env'
                )
            elif code == 'InvalidAccessKeyId':
                self.stdout.write('   → R2_ACCESS_KEY invalide. Générer un nouveau token dans Cloudflare Dashboard.')
            elif code == 'SignatureDoesNotMatch':
                self.stdout.write('   → R2_SECRET_KEY incorrecte. Vérifier la valeur dans .env.')
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'❌ Erreur inattendue : {exc}'))
        finally:
            if s3 and created_test_object:
                try:
                    s3.delete_object(Bucket=bucket, Key=self.TEST_KEY)
                except Exception:
                    pass

    def _head_public_url(self, url):
        try:
            import requests
        except ImportError:
            return self._head_public_url_urllib(url)

        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            response.raise_for_status()
        except Exception as exc:
            raise RuntimeError(f'HEAD {url} a échoué : {exc}') from exc

    def _head_public_url_urllib(self, url):
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen

        request = Request(url, method='HEAD')
        try:
            with urlopen(request, timeout=5) as response:
                status = getattr(response, 'status', getattr(response, 'getcode', None))
                if status and status >= 400:
                    raise RuntimeError(f'HTTP {status}')
        except (HTTPError, URLError) as exc:
            raise RuntimeError(f'HEAD {url} a échoué : {exc}') from exc
