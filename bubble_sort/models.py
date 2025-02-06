from django.db import models
from django.contrib.auth.models import User


class ColorPreset(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color_code = models.CharField(max_length=7, unique=True)  # Format hexadécimal

    class Meta:
        verbose_name = "Préréglage de couleur"
        verbose_name_plural = "Préréglages de couleurs"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.color_code})"

class ClassementBubble(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classements')
    created_at = models.DateTimeField(auto_now_add=True)
    color_start = models.ForeignKey(
        ColorPreset,
        on_delete=models.PROTECT,  # Plus nullable
        related_name='start_color_classements',
        verbose_name="Couleur de début",
        default=1
    )
    color_end = models.ForeignKey(
        ColorPreset,
        on_delete=models.PROTECT,  # Plus nullable
        related_name='end_color_classements',
        verbose_name="Couleur de fin",
        default=2
    )
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)  # Nouveau champ pour définir si le classement est public

    def __str__(self):
        return f"{self.name} (by {self.user.username})"

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # Afficher mes classements + ceux qui sont publics
            return ClassementBubble.objects.filter(models.Q(user=user) | models.Q(is_public=True))
        else:
            # Afficher uniquement les classements publics pour les utilisateurs non connectés
            return ClassementBubble.objects.filter(is_public=True)

class Bubble(models.Model):
    classement = models.ForeignKey(
        ClassementBubble,
        on_delete=models.CASCADE,
        related_name='bubbles',
        null=True,  # Permettre temporairement des valeurs nulles
        default=None  # Valeur par défaut temporaire
    )
    content = models.TextField()
    title = models.CharField(max_length=200, default='Nouvelle Bulle')  # Nouveau champ
    position = models.IntegerField(default=0)
    width = models.IntegerField(default=1000)  # Nouveau champ
    height = models.IntegerField(default=150) # Nouveau champ

    class Meta:
        ordering = ['position']
        app_label = 'bubble_sort'
        verbose_name = "Bulle"
        verbose_name_plural = "Bulles"

    def __str__(self):
        return f"Bubble {self.id}: {self.content[:20]}"


