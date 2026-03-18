from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import Module, UserPermission
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

        AUTO_ACCESS_MODULES = ['/events', '/chat', '/email', '/settings']
        auto_modules = {
            m.module_url: m
            for m in Module.objects.filter(module_url__in=AUTO_ACCESS_MODULES, is_active=True)
        }
        if auto_modules:
            User = get_user_model()
            users = list(User.objects.filter(is_active=True, is_superuser=False))
            user_ids = [user.id for user in users]

            covered_by_user_id = {}
            if user_ids:
                for user_id, module_url in UserPermission.objects.filter(
                    user_id__in=user_ids,
                    module__module_url__in=AUTO_ACCESS_MODULES,
                ).values_list('user_id', 'module__module_url'):
                    covered_by_user_id.setdefault(user_id, set()).add(module_url)

            perms_to_create = []
            patched_user_ids = set()
            for user in users:
                covered = covered_by_user_id.get(user.id, set())
                missing_urls = [url for url in AUTO_ACCESS_MODULES if url in auto_modules and url not in covered]
                if missing_urls:
                    patched_user_ids.add(user.id)
                    for url in missing_urls:
                        perms_to_create.append(
                            UserPermission(
                                user=user,
                                module=auto_modules[url],
                                is_view=True,
                                is_add=False,
                                is_edit=False,
                                is_delete=False,
                            )
                        )

            if perms_to_create:
                UserPermission.objects.bulk_create(perms_to_create, ignore_conflicts=True)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Auto-access permissions patched for {len(patched_user_ids)} users'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSetup complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
