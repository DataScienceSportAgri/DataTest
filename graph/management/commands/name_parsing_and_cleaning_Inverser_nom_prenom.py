from django.core.management.base import BaseCommand
from django.db import connection, transaction
from graph.models import Coureur
from django.db.models import F
from django.db.models.functions import Concat
class Command(BaseCommand):
    help = 'Remets correctement les nom et prénom'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("début de l'inversement des colonnes"))

        self.ivnerser_nom_prenom()

        self.stdout.write(self.style.SUCCESS("fin de l'inversement des colonnes"))
    def ivnerser_nom_prenom(self):
        Coureur.objects.update(
            prenom=F('nom'),
            nom=F('prenom')
        )