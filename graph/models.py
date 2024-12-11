from django.db import models
import uuid
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.db import models

class Categorie(models.Model):
    nom = models.CharField(max_length=10)
    age = models.CharField(max_length=20, null=True, blank=True)
    sexe = models.CharField(max_length=10, null=True, blank=True)
    type = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.nom

class Coureur(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    score_de_viabilite = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"

class Course(models.Model):
    nom = models.CharField(max_length=255)
    annee = models.IntegerField()
    distance = models.FloatField()

    def __str__(self):
        return f"{self.nom} ({self.annee})"

class ResultatCourse(models.Model):
    coureur = models.ForeignKey(Coureur, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    temps = models.DurationField(null=True, blank=True)
    temps2 = models.DurationField(null=True, blank=True)
    position = models.IntegerField()

    class Meta:
        unique_together = ('coureur', 'course')

    def __str__(self):
        return f"{self.coureur} - {self.course}"

class CoureurCategorie(models.Model):
    coureur = models.ForeignKey(Coureur, on_delete=models.CASCADE)
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE)
    annee = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['coureur', 'categorie', 'annee'],
                name='unique_coureur_categorie_annee'
            )
        ]

    def clean(self):
        super().clean()
        # Vérifier le nombre de catégories par coureur et par année
        count = CoureurCategorie.objects.filter(
            coureur=self.coureur,
            annee=self.annee
        ).count()
        if count >= 2:
            raise ValidationError("Un coureur ne peut pas avoir plus de deux catégories par année.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.coureur} - {self.categorie} ({self.annee})"

