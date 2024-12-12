# Generated by Django 5.1.3 on 2024-12-12 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dictionary", "0002_alter_language_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="language",
            name="name",
            field=models.CharField(
                choices=[
                    ("English", "English"),
                    ("Georgian", "Georgian"),
                    ("Korean", "Korean"),
                ],
                max_length=15,
            ),
        ),
    ]
