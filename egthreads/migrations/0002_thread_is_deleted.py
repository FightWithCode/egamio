# Generated by Django 5.1.2 on 2024-12-28 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('egthreads', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='thread',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
