from django.apps import AppConfig


class PollsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'polls'

class HalfmarathonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'halfmarathon'