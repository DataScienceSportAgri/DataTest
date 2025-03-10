# Generated by Django 5.1.4 on 2025-01-29 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('graph', '0005_categorie_id_categoriesimplifie'),
    ]

    operations = [
        migrations.CreateModel(
            name='GraphCategorieSimplifiee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sexe', models.CharField(choices=[('M', 'Masculin'), ('F', 'Féminin'), ('X', 'Mixte ou Inconnu')], max_length=1)),
                ('age', models.CharField(max_length=50)),
                ('nom', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Catégorie simplifiée',
                'verbose_name_plural': 'Catégories simplifiées',
            },
        ),
    ]
