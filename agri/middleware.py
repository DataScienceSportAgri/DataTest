import hashlib
import uuid
from .models import GuestUser


class AnonymousStateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ne pas interférer avec les utilisateurs authentifiés
        if not request.user.is_authenticated:
            salt = str(uuid.uuid4())[:8]
            ip = self.get_client_ip(request)
            ip_hash = hashlib.sha256(f"{ip}{salt}".encode()).hexdigest()

            # Créer ou récupérer l'utilisateur anonyme
            guest_user, created = GuestUser.objects.get_or_create(
                ip_hash=ip_hash,
                defaults={'session_key': uuid.uuid4()}
            )

            # Attacher à la requête
            request.guest_user = guest_user

        return self.get_response(request)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')