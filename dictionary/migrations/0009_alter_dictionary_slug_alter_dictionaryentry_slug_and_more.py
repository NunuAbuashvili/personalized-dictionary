# Generated by Django 5.1.3 on 2024-12-19 10:08

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dictionary", "0008_dictionaryentry_notes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="dictionary",
            name="slug",
            field=models.SlugField(allow_unicode=True, verbose_name="slug"),
        ),
        migrations.AlterField(
            model_name="dictionaryentry",
            name="slug",
            field=models.SlugField(allow_unicode=True, verbose_name="slug"),
        ),
        migrations.AlterField(
            model_name="dictionaryfolder",
            name="slug",
            field=models.SlugField(allow_unicode=True, verbose_name="slug"),
        ),
        migrations.AddConstraint(
            model_name="dictionary",
            constraint=models.UniqueConstraint(
                fields=("folder", "slug"), name="unique_slug_per_folder"
            ),
        ),
        migrations.AddConstraint(
            model_name="dictionaryentry",
            constraint=models.UniqueConstraint(
                fields=("dictionary", "slug"), name="unique_slug_per_dictionary"
            ),
        ),
        migrations.AddConstraint(
            model_name="dictionaryfolder",
            constraint=models.UniqueConstraint(
                fields=("user", "slug"), name="unique_slug_per_user"
            ),
        ),
    ]
