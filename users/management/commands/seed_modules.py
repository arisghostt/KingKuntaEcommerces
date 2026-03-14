from django.core.management.base import BaseCommand

from users.models import Module


class Command(BaseCommand):
    help = 'Seed default modules for the KingKunta e-commerce system.'

    def handle(self, *args, **options):
        """
        Populate Module table with default modules if empty.
        """
        modules_data = [
            {"module_name": "Dashboard", "module_url": "/dashboard", "is_menu": True, "is_active": True, "display_order": 1},
            {"module_name": "Products", "module_url": "/products", "is_menu": True, "is_active": True, "display_order": 2},
            {"module_name": "Orders", "module_url": "/orders", "is_menu": True, "is_active": True, "display_order": 3},
            {"module_name": "Customers", "module_url": "/customers", "is_menu": True, "is_active": True, "display_order": 4},
            {"module_name": "Users", "module_url": "/settings/users", "is_menu": True, "is_active": True, "display_order": 5},
            {"module_name": "Analytics", "module_url": "/analytics", "is_menu": True, "is_active": True, "display_order": 6},
            {"module_name": "Promotions", "module_url": "/promotions", "is_menu": True, "is_active": True, "display_order": 7},
            {"module_name": "Billing", "module_url": "/billing", "is_menu": True, "is_active": True, "display_order": 8},
        ]

        created_count = 0
        updated_count = 0

        for module_data in modules_data:
            module, created = Module.objects.get_or_create(
                module_url=module_data["module_url"],
                defaults=module_data
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Created: {module_data['module_name']}"))
            else:
                # Update existing if necessary
                module.module_name = module_data["module_name"]
                module.is_menu = module_data["is_menu"]
                module.is_active = module_data["is_active"]
                module.display_order = module_data["display_order"]
                module.save(update_fields=['module_name', 'is_menu', 'is_active', 'display_order'])
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"⟳ Updated: {module_data['module_name']}"))

        total = created_count + updated_count
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Seed complete: created={created_count}, updated={updated_count}, total modules={total}'
            )
        )
