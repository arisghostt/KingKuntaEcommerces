from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from users.models import RoleProfile
from users.serializers import PERMISSION_CATALOG


class Command(BaseCommand):
    help = 'Seed fixed role permissions for frontend role management.'

    def handle(self, *args, **options):
        content_type = ContentType.objects.get_for_model(RoleProfile)
        created_count = 0
        updated_count = 0

        for item in PERMISSION_CATALOG:
            permission, created = Permission.objects.get_or_create(
                content_type=content_type,
                codename=item['id'],
                defaults={'name': item['name']},
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {item['id']}"))
                continue

            if permission.name != item['name']:
                permission.name = item['name']
                permission.save(update_fields=['name'])
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated: {item['id']}"))

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed complete. created={created_count}, updated={updated_count}, total={len(PERMISSION_CATALOG)}'
            )
        )
