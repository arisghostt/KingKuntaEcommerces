from django.core.management.base import BaseCommand
from users.models import Module


class Command(BaseCommand):
    help = 'Populate Module table with e-commerce dashboard pages'

    def handle(self, *args, **options):
        modules_data = [
            {
                'module_name': 'Dashboard',
                'module_url': '/dashboard',
                'is_menu': True,
                'is_active': True,
                'display_order': 1,
                'parent': None,
            },
            {
                'module_name': 'Products',
                'module_url': '/products',
                'is_menu': True,
                'is_active': True,
                'display_order': 2,
                'parent': None,
            },
            {
                'module_name': 'Orders',
                'module_url': '/orders',
                'is_menu': True,
                'is_active': True,
                'display_order': 3,
                'parent': None,
            },
            {
                'module_name': 'Customers',
                'module_url': '/customers',
                'is_menu': True,
                'is_active': True,
                'display_order': 4,
                'parent': None,
            },
            {
                'module_name': 'Users',
                'module_url': '/users',
                'is_menu': True,
                'is_active': True,
                'display_order': 5,
                'parent': None,
            },
            {
                'module_name': 'Billing',
                'module_url': '/billing',
                'is_menu': True,
                'is_active': True,
                'display_order': 6,
                'parent': None,
            },
            {
                'module_name': 'Inventory',
                'module_url': '/inventory',
                'is_menu': True,
                'is_active': True,
                'display_order': 7,
                'parent': None,
            },
            {
                'module_name': 'Reports',
                'module_url': '/reports',
                'is_menu': True,
                'is_active': True,
                'display_order': 8,
                'parent': None,
            },
        ]

        created_count = 0
        updated_count = 0

        for module_data in modules_data:
            module, created = Module.objects.update_or_create(
                module_url=module_data['module_url'],
                defaults={
                    'module_name': module_data['module_name'],
                    'is_menu': module_data['is_menu'],
                    'is_active': module_data['is_active'],
                    'display_order': module_data['display_order'],
                    'parent': module_data['parent'],
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'✓ Module "{module.module_name}" processed')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSetup complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
