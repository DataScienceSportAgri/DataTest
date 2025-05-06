from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        # Dépend de la dernière migration existante (même si vide)
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                'DROP TABLE polls_question;',
                'DROP TABLE polls_choice;',
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
