from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0011_alter_product_image_alter_product_status_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE products_product
                ADD COLUMN IF NOT EXISTS brand varchar(100) NOT NULL DEFAULT '';
                ALTER TABLE products_product ALTER COLUMN brand SET DEFAULT '';
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
