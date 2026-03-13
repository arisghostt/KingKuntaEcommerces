# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='images',
            field=models.JSONField(blank=True, default=list, help_text='List of image URLs'),
        ),
        migrations.AddField(
            model_name='product',
            name='thumbnail',
            field=models.URLField(blank=True, null=True),
        ),
    ]