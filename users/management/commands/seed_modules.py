from django.core.management.base import BaseCommand

from users.models import Module
from users.module_catalog import MODULE_CATALOG, prepare_module_entry


class Command(BaseCommand):
    help = 'Seed default modules for the KingKunta e-commerce system.'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

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
                self.stdout.write(self.style.SUCCESS(f"✓ Created: {module.module_name}"))
            else:
                module.module_name = defaults['module_name']
                module.is_menu = defaults['is_menu']
                module.is_active = defaults['is_active']
                module.display_order = defaults['display_order']
                module.parent = parent
                module.save(update_fields=['module_name', 'is_menu', 'is_active', 'display_order', 'parent'])
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"⟳ Updated: {module.module_name}"))

        total = created_count + updated_count
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Seed complete: created={created_count}, updated={updated_count}, total modules={total}'
            )
        )
