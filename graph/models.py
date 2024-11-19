from django.db import models
import uuid



class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom

class Coureur(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    
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
        unique_together = ('coureur', 'annee')  # Un coureur ne peut avoir qu'une catégorie par an

    def __str__(self):
        return f"{self.coureur} - {self.categorie} ({self.annee})"

