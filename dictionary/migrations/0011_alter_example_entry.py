# Generated by Django 5.1.3 on 2024-12-19 13:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dictionary", "0010_remove_dictionaryentry_examples_example_entry"),
    ]

    operations = [
        migrations.AlterField(
            model_name="example",
            name="entry",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="examples",
                to="dictionary.dictionaryentry",
            ),
        ),
    ]
