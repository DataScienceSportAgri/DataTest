# Generated by Django 5.1.4 on 2025-02-02 19:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bubble_sort', '0007_alter_classementbubble_color_end_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classementbubble',
            name='color_end',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.PROTECT, related_name='end_color_classements', to='bubble_sort.colorpreset', verbose_name='Couleur de fin'),
        ),
        migrations.AlterField(
            model_name='classementbubble',
            name='color_start',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='start_color_classements', to='bubble_sort.colorpreset', verbose_name='Couleur de début'),
        ),
    ]
