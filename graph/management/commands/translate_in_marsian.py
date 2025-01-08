from django.core.management.base import BaseCommand
from django.db.models import Q
from graph.models import Course, Coureur, FrenchSyllable, SyllablePair
from tqdm import tqdm
import pyphen
import re


class Command(BaseCommand):
    help = 'Traduit les noms des courses et coureurs en marsien'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dic = pyphen.Pyphen(lang='fr_FR')

    def handle(self, *args, **options):
        self.translate_model(Course, ['nom'])
        self.translate_model(Coureur, ['nom', 'prenom'])

        self.stdout.write(self.style.SUCCESS('Traduction terminée avec succès'))

    def translate_model(self, model, fields):
        objects = model.objects.all()
        with tqdm(total=objects.count(), desc=f"Traduction de {model.__name__}") as pbar:
            for obj in objects:
                for field in fields:
                    original_text = getattr(obj, field)
                    translated_text = self.translate_text(original_text)
                    setattr(obj, f'{field}_marsien', translated_text)
                obj.save()
                pbar.update(1)

    def translate_text(self, text):
        words = text.split()
        translated_words = []
        for word in words:
            syllables = self.dic.inserted(word).split('-')
            translated_syllables = []
            i = 0
            while i < len(syllables):
                if i + 1 < len(syllables):
                    pair_translation = self.translate_syllable_pair(syllables[i], syllables[i + 1])
                    if pair_translation:
                        translated_syllables.extend(pair_translation)
                        i += 2
                    else:
                        translated_syllables.append(self.translate_single_syllable(syllables[i]))
                        i += 1
                else:
                    translated_syllables.append(self.translate_single_syllable(syllables[i]))
                    i += 1
            translated_words.append(''.join(translated_syllables))
        return ' '.join(translated_words)

    def translate_syllable_pair(self, syl1, syl2):
        normalized_syl1 = self.normalize_syllable(syl1)
        normalized_syl2 = self.normalize_syllable(syl2)

        french_syl1 = FrenchSyllable.objects.filter(
            Q(content__iexact=normalized_syl1) | Q(content__iexact=syl1)).first()
        french_syl2 = FrenchSyllable.objects.filter(
            Q(content__iexact=normalized_syl2) | Q(content__iexact=syl2)).first()

        if french_syl1 and french_syl2:
            pair = SyllablePair.objects.filter(
                french_syllable1=french_syl1,
                french_syllable2=french_syl2
            ).first()
            if pair and pair.marsian_syllable1 and pair.marsian_syllable2:
                return [pair.marsian_syllable1.content, pair.marsian_syllable2.content]
        return None

    def translate_single_syllable(self, syl):
        normalized_syl = self.normalize_syllable(syl)
        french_syl = FrenchSyllable.objects.filter(Q(content__iexact=normalized_syl) | Q(content__iexact=syl)).first()
        if french_syl:
            pair = SyllablePair.objects.filter(french_syllable1=french_syl, french_syllable2__isnull=True).first()
            if pair and pair.marsian_syllable1:
                return pair.marsian_syllable1.content
        return syl  # Retourne la syllabe originale si aucune traduction n'est trouvée

    def normalize_syllable(self, syllable):
        return re.sub(r'[^a-záčďéěíňóřšťúůýž]', '', syllable.lower())
