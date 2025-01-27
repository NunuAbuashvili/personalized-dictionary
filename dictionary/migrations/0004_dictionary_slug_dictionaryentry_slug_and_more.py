# Generated by Django 5.1.3 on 2024-12-13 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dictionary", "0003_alter_language_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="dictionary",
            name="slug",
            field=models.SlugField(blank=True, verbose_name="slug"),
        ),
        migrations.AddField(
            model_name="dictionaryentry",
            name="slug",
            field=models.SlugField(blank=True, verbose_name="slug"),
        ),
        migrations.AddField(
            model_name="dictionaryfolder",
            name="slug",
            field=models.SlugField(blank=True, verbose_name="slug"),
        ),
        migrations.AddField(
            model_name="language",
            name="slug",
            field=models.SlugField(blank=True, verbose_name="slug"),
        ),
    ]
