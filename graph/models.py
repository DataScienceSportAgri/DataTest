from django.db import models
import uuid
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.db import models

class CategorieSimplifiee(models.Model):
    nom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=[
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('X', 'Mixte ou Inconnu'),
    ])
    age_min = models.IntegerField(null=True, blank=True)
    age_max = models.IntegerField(null=True, blank=True)


    def __str__(self):
        return f"{self.nom} ({self.sexe}"


    class Meta:
        verbose_name = "Catégorie simplifiée"
        verbose_name_plural = "Catégories simplifiées"

class Categorie(models.Model):
    nom = models.CharField(max_length=10)
    age = models.CharField(max_length=20, null=True, blank=True)
    sexe = models.CharField(max_length=10, null=True, blank=True)
    type = models.CharField(max_length=20, null=True, blank=True)
    categoriesimplifiee = models.ForeignKey(CategorieSimplifiee, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.nom



class Coureur(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    nom_marsien = models.CharField(max_length=100, null=True, blank=True)
    prenom_marsien = models.CharField(max_length=100, null=True, blank=True)
    score_de_viabilite = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"

class CourseType(models.Model):
    nom = models.CharField(max_length=255)

class Course(models.Model):
    nom = models.CharField(max_length=255)
    nom_marsien = models.CharField(max_length=255, null=True, blank=True)
    annee = models.IntegerField()
    distance = models.FloatField()
    type = models.ForeignKey(CourseType, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.nom} ({self.annee})"



class ResultatCourse(models.Model):
    coureur = models.ForeignKey(Coureur, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    temps = models.DurationField(null=True, blank=True)
    temps2 = models.DurationField(null=True, blank=True)
    position = models.IntegerField()
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, null=True, blank=True)
    score_de_performance = models.FloatField(null=True, blank=True)

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


class FrenchSyllable(models.Model):
    content = models.CharField(max_length=20, unique=True)
    count = models.IntegerField(default=0)
    cv_pattern = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"{self.content} ({self.count})"

class MarsianSyllable(models.Model):
    content = models.CharField(max_length=20, unique=True)
    cv_pattern = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.content

class SyllablePair(models.Model):
    french_syllable1 = models.ForeignKey(FrenchSyllable, on_delete=models.CASCADE, related_name='first_french_syllable')
    french_syllable2 = models.ForeignKey(FrenchSyllable, on_delete=models.CASCADE, related_name='second_french_syllable', null=True, blank=True)
    marsian_syllable1 = models.ForeignKey(MarsianSyllable, on_delete=models.CASCADE, related_name='first_marsian_syllable')
    marsian_syllable2 = models.ForeignKey(MarsianSyllable, on_delete=models.CASCADE, related_name='second_marsian_syllable', null=True, blank=True)

    class Meta:
        unique_together = ('french_syllable1', 'french_syllable2')

    def __str__(self):
        if self.french_syllable2:
            return f"{self.french_syllable1}-{self.french_syllable2} -> {self.marsian_syllable1}-{self.marsian_syllable2}"
        return f"{self.french_syllable1} -> {self.marsian_syllable1}"

class ColorPreset(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color_code = models.CharField(max_length=7, unique=True)  # Format hexadécimal

    class Meta:
        verbose_name = "Préréglage de couleur"
        verbose_name_plural = "Préréglages de couleurs"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.color_code})"


class NormalisateurDistancesCategories(models.Model):
    DISTANCE_CHOICES = [
        ('0-7500', '0 à 7500 m'),
        ('7500-15000', '7500 à 15000 m'),
        ('15000-30000', '15000 à 30000 m'),
        ('30000-45000', '30000 à 45000 m'),
        ('45000+', 'Plus de 45000 m')
    ]

    distance_range = models.CharField(max_length=20, choices=DISTANCE_CHOICES)
    categorie = models.ForeignKey(CategorieSimplifiee, on_delete=models.PROTECT)
    vitesse_moyenne = models.FloatField(null=True, blank=True)
    multiplicateur = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('distance_range', 'categorie')


class NormalisateurTypeDeCourseNbParticipants(models.Model):
    course_type = models.ForeignKey(
        CourseType,
        on_delete=models.PROTECT,  # Empêche la suppression si utilisé
        related_name='normalisateurs',
        verbose_name="Type de course"
    )
    seuil_participants = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Seuil participant"
    )
    multiplicateur = models.FloatField(
        verbose_name="Coefficient multiplicateur",
        default=1.0
    )

    class Meta:
        unique_together = ('course_type', 'seuil_participants')
        verbose_name = "Normalisateur type de course"
        verbose_name_plural = "Normalisateurs types de course"

    def __str__(self):
        base = f"{self.course_type.nom} - "
        if self.seuil_participants:
            return base + f"Seuil {self.seuil_participants} (×{self.multiplicateur})"
        return base + f"Générique (×{self.multiplicateur})"