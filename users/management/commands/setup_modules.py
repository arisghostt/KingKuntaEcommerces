from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import Module
from users.module_catalog import MODULE_CATALOG, prepare_module_entry


class Command(BaseCommand):
    help = 'Populate Module table with e-commerce dashboard pages'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

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
                self.stdout.write(self.style.SUCCESS(f'✓ Module "{module.module_name}" processed'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSetup complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
