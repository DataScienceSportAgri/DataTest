# services/ml_service.py
import joblib
from django.core.cache import cache
from .models import MLModelState


class MLModelManager:

    @classmethod
    def save_model(cls, session_id, model, features):
        # Persistance dans la base
        model_bytes = joblib.dumps(model)
        MLModelState.objects.update_or_create(
            session_key=session_id,
            defaults={
                'model_data': model_bytes,
                'feature_data': features
            }
        )

        # Cache mémoire
        cache.set(
            f'model_{session_id}',
            {'model': model, 'features': features},
            timeout=3600
        )

    @classmethod
    def load_model(cls, session_id):
        # Vérification cache
        cached = cache.get(f'model_{session_id}')
        if cached:
            return cached['model'], cached['features']

        # Fallback base de données
        try:
            state = MLModelState.objects.get(session_key=session_id)
            model = joblib.loads(state.model_data)
            return model, state.feature_data
        except MLModelState.DoesNotExist:
            return None, None