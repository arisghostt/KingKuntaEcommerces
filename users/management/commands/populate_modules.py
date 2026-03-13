from django.core.management.base import BaseCommand
from users.models import Module


class Command(BaseCommand):
    help = 'Populate modules table with default modules'

    def handle(self, *args, **options):
        modules = [
            {"module_name": "Tableau de bord", "module_url": "/dashboard", "is_menu": True, "is_active": True, "display_order": 1},
            {"module_name": "Produits", "module_url": "/products", "is_menu": True, "is_active": True, "display_order": 2},
            {"module_name": "Commandes", "module_url": "/orders", "is_menu": True, "is_active": True, "display_order": 3},
            {"module_name": "Inventaire", "module_url": "/inventory", "is_menu": True, "is_active": True, "display_order": 4},
            {"module_name": "Clients", "module_url": "/clients", "is_menu": True, "is_active": True, "display_order": 5},
            {"module_name": "Utilisateurs", "module_url": "/users", "is_menu": True, "is_active": True, "display_order": 6},
            {"module_name": "Promotions", "module_url": "/promotions", "is_menu": True, "is_active": True, "display_order": 7},
            {"module_name": "Paiement", "module_url": "/payments", "is_menu": True, "is_active": True, "display_order": 8},
            {"module_name": "Facturation", "module_url": "/billing", "is_menu": True, "is_active": True, "display_order": 9},
            {"module_name": "Facture", "module_url": "/invoices", "is_menu": True, "is_active": True, "display_order": 10},
            {"module_name": "Analytique", "module_url": "/analytics", "is_menu": True, "is_active": True, "display_order": 11},
            {"module_name": "Discussion", "module_url": "/chat", "is_menu": True, "is_active": True, "display_order": 12},
            {"module_name": "E-mail", "module_url": "/email", "is_menu": True, "is_active": True, "display_order": 13},
            {"module_name": "Événements", "module_url": "/events", "is_menu": True, "is_active": True, "display_order": 14},
            {"module_name": "Paramètres", "module_url": "/settings", "is_menu": True, "is_active": True, "display_order": 15},
        ]

        created_count = 0
        for m in modules:
            _, created = Module.objects.get_or_create(module_url=m["module_url"], defaults=m)
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} modules'))
