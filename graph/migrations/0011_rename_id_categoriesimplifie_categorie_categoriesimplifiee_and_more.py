# Generated by Django 5.1.4 on 2025-02-09 13:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('graph', '0010_alter_categorie_id_categoriesimplifie_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='categorie',
            old_name='id_categoriesimplifie',
            new_name='categoriesimplifiee',
        ),
        migrations.RenameField(
            model_name='resultatcourse',
            old_name='categorie_id',
            new_name='categorie',
        ),
    ]
