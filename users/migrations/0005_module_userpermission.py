# Generated migration for Module and UserPermission models

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_customuser_tenant'),
    ]

    operations = [
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module_name', models.CharField(max_length=100)),
                ('module_url', models.CharField(max_length=200, unique=True)),
                ('is_menu', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('display_order', models.IntegerField(default=0)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='users.module')),
            ],
            options={
                'ordering': ['display_order'],
            },
        ),
        migrations.CreateModel(
            name='UserPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_view', models.BooleanField(default=False)),
                ('is_add', models.BooleanField(default=False)),
                ('is_edit', models.BooleanField(default=False)),
                ('is_delete', models.BooleanField(default=False)),
                ('domain_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='domain_permissions', to='users.customuser')),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.module')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='module_permissions', to='users.customuser')),
            ],
            options={
                'unique_together': {('user', 'module')},
            },
        ),
    ]
