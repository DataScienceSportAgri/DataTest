from django.db import models
from django.utils.timezone import now

from django.db import models
import uuid
import pickle
import base64


class TrainingConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country_code = models.CharField(max_length=2)
    parcelles = models.JSONField()  # Liste des parcelles sélectionnées
    mode = models.CharField(max_length=10)  # 'points' ou 'filter'
    filters = models.JSONField(null=True)  # {indice: 'NDVI', min: 0, max: 1, rendement_min: 0, rendement_max: 10000}
    points = models.JSONField(null=True)  # [{lat: 48.5, lon: 5.5}, ...]
    created_at = models.DateTimeField(auto_now_add=True)

    # Champs pour stocker le modèle ML
    model_binary = models.BinaryField(null=True)  # Modèle sérialisé
    model_metrics = models.JSONField(null=True)  # Métriques (R², RMSE, etc.)
    feature_importance = models.JSONField(null=True)  # Importance des variables

    def save_model(self, model_object):
        """Sérialise et sauvegarde un modèle scikit-learn"""
        self.model_binary = pickle.dumps(model_object)
        self.save()

    def load_model(self):
        """Charge le modèle scikit-learn sérialisé"""
        if self.model_binary:
            return pickle.loads(self.model_binary)
        return None


class SelectedPoint(models.Model):
    # Identifiants de session/utilisateur
    session_id = models.CharField(max_length=100)

    # Métadonnées de la sélection
    selection_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Informations sur la parcelle
    country_code = models.CharField(max_length=2)
    parcelle = models.CharField(max_length=100)

    # Coordonnées du point
    latitude = models.FloatField()
    longitude = models.FloatField()

    # Référence au dataframe d'origine
    dataframe_index = models.IntegerField(null=True)  # Index dans le dataframe original

    # Valeurs des indices (optionnel)
    rendement = models.FloatField(null=True)
    ndvi = models.FloatField(null=True)

    # Nouveau champ pour training/prediction
    training = models.BooleanField(
        null=True,
        verbose_name="Mode entraînement",
        help_text="True pour training, False pour prediction"
    )

    class Meta:
        # Éviter les doublons
        unique_together = ('session_id', 'country_code', 'parcelle', 'latitude', 'longitude', 'training')


# Fonction pour supprimer tous les enregistrements de SelectedPoint toutes les heures
def delete_all_points():
    SelectedPoint.objects.all().delete()
    print("Tous les points ont été supprimés de la table SelectedPoint.")

