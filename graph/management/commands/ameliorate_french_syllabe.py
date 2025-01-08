from django.core.management.base import BaseCommand
from django.db.models import F
from graph.models import FrenchSyllable
from tqdm import tqdm
import pyphen

class Command(BaseCommand):
    help = 'Nettoie et fusionne les syllabes françaises, puis traite les mots complets'

    def handle(self, *args, **options):
        self.clean_and_merge_syllables()
        self.process_full_words()
        self.stdout.write(self.style.SUCCESS('Opération terminée avec succès'))

    def clean_syllable(self, syllable):
        return ''.join(c.lower() for c in syllable if c.isalpha())

    def clean_and_merge_syllables(self):
        syllables = FrenchSyllable.objects.all()
        cleaned_syllables = {}

        for syllable in tqdm(syllables, desc="Nettoyage et fusion des syllabes"):
            cleaned = self.clean_syllable(syllable.content)
            if cleaned:
                if cleaned in cleaned_syllables:
                    cleaned_syllables[cleaned] += syllable.count
                else:
                    cleaned_syllables[cleaned] = syllable.count

        for cleaned, count in tqdm(cleaned_syllables.items(), desc="Mise à jour des syllabes"):
            FrenchSyllable.objects.update_or_create(
                content=cleaned,
                defaults={'count': count}
            )

        FrenchSyllable.objects.exclude(content__in=cleaned_syllables.keys()).delete()
        self.stdout.write(self.style.SUCCESS('Nettoyage et fusion des syllabes terminés'))

    def process_full_words(self):
        dic = pyphen.Pyphen(lang='fr_FR')
        full_words = FrenchSyllable.objects.filter(content__regex=r'^[a-z]{4,}$')

        for word in tqdm(full_words, desc="Traitement des mots complets"):
            syllables = dic.inserted(word.content).split('-')
            if len(syllables) > 1:
                for syllable in syllables:
                    obj, created = FrenchSyllable.objects.get_or_create(content=syllable)
                    if created:
                        obj.count = word.count
                    else:
                        obj.count += word.count
                    obj.save()
                word.delete()

        self.stdout.write(self.style.SUCCESS('Traitement des mots complets terminé'))
