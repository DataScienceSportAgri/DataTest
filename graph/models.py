from django.db import models
import uuid



class CategorieCoureur(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom

class Coureur(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    categorie = models.ForeignKey(CategorieCoureur, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"

class Course(models.Model):
    nom = models.CharField(max_length=255)
    date = models.DateField()
    distance = models.FloatField()

    def __str__(self):
        return f"{self.nom} ({self.date})"

class ResultatCourse(models.Model):
    coureur = models.ForeignKey(Coureur, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    temps = models.DurationField()
    temps2 = models.DurationField()
    Vitesse = models.FloatField()
    position = models.IntegerField()

    class Meta:
        unique_together = ('coureur', 'course')

    def __str__(self):
        return f"{self.coureur} - {self.course}"

