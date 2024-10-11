from django.db import models

class HalfMarathon(models.Model):
    # Définissez ici les champs correspondant à votre table
    # Par exemple :
    nom = models.CharField(max_length=100)
    temps = models.TimeField()
    # Ajoutez d'autres champs selon votre structure

    def __str__(self):
        return self.nom