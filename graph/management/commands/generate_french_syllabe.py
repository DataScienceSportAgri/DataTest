from django.core.management.base import BaseCommand
from django.db.models import F, CharField
from tqdm import tqdm
import pyphen
from graph.models import Course, Coureur, FrenchSyllable

class Command(BaseCommand):
    help = 'Generates French syllables and their counts from Course and Coureur models'

    def separate_syllables(self, word):
        dic = pyphen.Pyphen(lang='fr_FR')
        return dic.inserted(word).split('-')

    def handle(self, *args, **options):
        # Récupérer tous les champs CharField des modèles Course et Coureur
        all_fields = []
        for model in [Course, Coureur]:
            char_fields = [f.name for f in model._meta.get_fields() if isinstance(f, CharField)]
            all_fields.extend([getattr(obj, field) for obj in model.objects.all() for field in char_fields])

        # Traiter chaque mot avec une barre de progression
        for word in tqdm(all_fields, desc="Processing words", unit="word"):
            syllables = self.separate_syllables(word)
            for syllable in syllables:
                french_syllable, created = FrenchSyllable.objects.get_or_create(content=syllable)
                if not created:
                    FrenchSyllable.objects.filter(id=french_syllable.id).update(count=F('count') + 1)

        self.stdout.write(self.style.SUCCESS('Successfully generated French syllables and their counts'))
