# Generated by Django 5.1.3 on 2024-12-14 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "dictionary",
            "0005_alter_dictionary_slug_alter_dictionaryentry_slug_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="dictionaryfolder",
            name="slug",
            field=models.SlugField(
                allow_unicode=True, unique=True, verbose_name="slug"
            ),
        ),
    ]
