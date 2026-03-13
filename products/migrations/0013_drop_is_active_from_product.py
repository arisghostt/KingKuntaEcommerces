from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0012_ensure_brand_column'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE products_product DROP COLUMN IF EXISTS is_active;",
            reverse_sql="ALTER TABLE products_product ADD COLUMN is_active boolean NOT NULL DEFAULT true;",
        ),
    ]

