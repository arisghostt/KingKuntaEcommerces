from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import Module
from users.module_catalog import MODULE_CATALOG, prepare_module_entry

REQUIRED_MODULE_URLS = [
    '/dashboard',
    '/products',
    '/orders',
    '/customers',
    '/suppliers',
    '/inventory',
    '/analytics',
    '/promotions',
    '/billing',
    '/invoices',
    '/chat',
    '/email',
    '/events',
    '/settings',
    '/settings/users',
    '/users',
]


class Command(BaseCommand):
    help = 'Populate modules table with default modules'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        configured_urls = {module_config['module_url'] for module_config in MODULE_CATALOG}
        missing_urls = [url for url in REQUIRED_MODULE_URLS if url not in configured_urls]
        if missing_urls:
            self.stdout.write(self.style.WARNING(
                'MODULE_CATALOG is missing module_url entries: ' + ', '.join(missing_urls)
            ))

        with transaction.atomic():
            for module_config in MODULE_CATALOG:
                module_url, defaults, parent_url = prepare_module_entry(module_config)
                parent = Module.objects.filter(module_url=parent_url).first() if parent_url else None
                defaults['parent'] = parent
                module, created = Module.objects.update_or_create(
                    module_url=module_url,
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully ensured {len(MODULE_CATALOG)} modules (created={created_count}, updated={updated_count})'
            )
        )
