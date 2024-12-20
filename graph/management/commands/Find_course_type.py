from django.core.management.base import BaseCommand
from django.db.models import Count
from collections import Counter
import re
from your_app.models import Course, Type  # Remplacez 'your_app' par le nom de votre application


class Command(BaseCommand):
    help = 'Analyse les noms de courses et met à jour les types'

    def handle(self, *args, **options):
        # Récupérer tous les noms de courses
        course_names = Course.objects.values_list('name', flat=True)

        # Analyser les mots dans les noms de courses
        word_counter = Counter()
        for name in course_names:
            words = re.findall(r'\b\w+\b', name.lower())
            word_counter.update(words)

        # Filtrer les mots pertinents
        relevant_words = [word for word, count in word_counter.items()
                          if count > 5 and len(word) > 3]

        # Liste de mots à exclure (lieux, communes, départements)
        excluded_words = set(['paris', 'lyon', 'marseille'])  # Ajoutez d'autres mots si nécessaire

        # Créer ou récupérer les types de course
        road_type, _ = Type.objects.get_or_create(name='Course sur route')
        duathlon_type, _ = Type.objects.get_or_create(name='Duathlon')

        # Mettre à jour les types de course
        for course in Course.objects.all():
            course_words = set(re.findall(r'\b\w+\b', course.name.lower()))

            if 'duathlon' in course_words:
                course.type = duathlon_type
            else:
                matching_words = course_words.intersection(set(relevant_words)) - excluded_words
                if matching_words:
                    new_type, _ = Type.objects.get_or_create(name=f"Nouveau type: {', '.join(matching_words)}")
                    course.type = new_type
                else:
                    course.type = road_type

            course.save()

        self.stdout.write(self.style.SUCCESS('Mise à jour des types de course terminée'))
