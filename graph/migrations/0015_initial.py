from django.db import migrations
from ..import_script import import_data  # Placez votre logique d'importation dans un fichier séparé

def import_data_wrapper(apps, schema_editor):
    # Utilisez les modèles fournis par `apps` pour l'importation
    Course = apps.get_model('graph', 'Course')
    ResultatCourse = apps.get_model('graph', 'ResultatCourse')
    Categorie = apps.get_model('graph', 'Categorie')
    Coureur = apps.get_model('graph', 'Coureur')
    CoureurCategorie = apps.get_model('graph', 'CoureurCategorie')

    import_data(Course, ResultatCourse, Categorie, Coureur, CoureurCategorie)

class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ('graph', '0001_initial'),  # Assurez-vous que cela pointe vers votre migration initiale
    ]

    operations = [
        migrations.RunPython(import_data_wrapper),
    ]