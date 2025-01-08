from django.core.management.base import BaseCommand
from django.db.models import CharField
from graph.models import Course, Coureur, FrenchSyllable, MarsianSyllable, SyllablePair
from tqdm import tqdm
import pyphen
import random
import re
from django.db.models import Q

def normalize_syllable(syllable):
    return re.sub(r'[^a-záčďéěíňóřšťúůýž]', '', syllable.lower())

class Command(BaseCommand):
    help = 'Découpe les mots en syllabes et crée les paires de syllabes'

    def handle(self, *args, **options):
        dic = pyphen.Pyphen(lang='fr_FR')

        # Récupérer tous les champs CharField des modèles Course et Coureur
        all_fields = []
        for model in [Course, Coureur]:
            char_fields = [f.name for f in model._meta.get_fields() if isinstance(f, CharField)]
            all_fields.extend([getattr(obj, field) for obj in model.objects.all() for field in char_fields])

        # Séparer les chaînes en mots et obtenir les mots uniques
        all_words = set(word for text in all_fields for word in text.split())

        # Traiter chaque mot avec une barre de progression
        with tqdm(total=len(all_words), desc="Traitement des mots") as pbar:
            for word in all_words:
                syllables = dic.inserted(word).split('-')
                if len(syllables) > 1:
                    for i in range(0, len(syllables) - 1, 2):
                        # Dans votre méthode handle
                        try:
                            normalized_syl1 = normalize_syllable(syllables[i])
                            normalized_syl2 = normalize_syllable(syllables[i + 1])

                            syl1 = FrenchSyllable.objects.filter(
                                Q(content__iexact=normalized_syl1) | Q(content__iexact=syllables[i])).first()
                            syl2 = FrenchSyllable.objects.filter(
                                Q(content__iexact=normalized_syl2) | Q(content__iexact=syllables[i + 1])).first()

                            if not syl1 or not syl2:
                                continue  # Passer à la paire de syllabes suivante si l'une des syllabes n'est pas trouvée
                        except:
                            continue

                        # Vérifier si au moins une des syllabes a un count > 30
                        if syl1.count > 30 or syl2.count > 30:
                            # Vérifier si l'enchainement existe déjà
                            if not SyllablePair.objects.filter(french_syllable1=syl1, french_syllable2=syl2).exists():
                                # Créer un nouvel enchainement de syllabes marsiennes
                                marsian_pair = self.create_marsian_pair(syl1, syl2)
                                if marsian_pair:
                                    SyllablePair.objects.create(
                                        french_syllable1=syl1,
                                        french_syllable2=syl2,
                                        marsian_syllable1=marsian_pair[0],
                                        marsian_syllable2=marsian_pair[1]
                                    )
                pbar.update(1)

        # Associer chaque syllabe française unique à une syllabe marsienne unique
        self.associate_single_syllables()

        self.stdout.write(self.style.SUCCESS('Opération terminée avec succès'))

    def create_marsian_pair(self, french_syl1, french_syl2):
        french_pattern = french_syl1.cv_pattern + french_syl2.cv_pattern
        matching_marsian = MarsianSyllable.objects.filter(
            cv_pattern__in=[french_syl1.cv_pattern, french_syl2.cv_pattern])

        if len(matching_marsian) >= 2:
            return random.sample(list(matching_marsian), 2)
        return None

    def associate_single_syllables(self):
        french_syllables = FrenchSyllable.objects.all()
        marsian_syllables = list(MarsianSyllable.objects.all())

        with tqdm(total=french_syllables.count(), desc="Association des syllabes uniques") as pbar:
            for french_syl in french_syllables:
                # Vérifier si la syllabe française n'a pas déjà été associée
                if not SyllablePair.objects.filter(french_syllable1=french_syl, french_syllable2__isnull=True).exists():
                    matching_marsian = [m for m in marsian_syllables if m.cv_pattern == french_syl.cv_pattern]
                    if matching_marsian:
                        marsian_syl = random.choice(matching_marsian)
                        SyllablePair.objects.create(
                            french_syllable1=french_syl,
                            marsian_syllable1=marsian_syl
                        )
                        marsian_syllables.remove(marsian_syl)
                    else:
                        # Si aucune syllabe marsienne avec le même cv_pattern n'est disponible,
                        # on utilise une syllabe marsienne déjà utilisée avec le même cv_pattern
                        used_marsian = MarsianSyllable.objects.filter(cv_pattern=french_syl.cv_pattern).first()
                        if used_marsian:
                            SyllablePair.objects.create(
                                french_syllable1=french_syl,
                                marsian_syllable1=used_marsian
                            )
                pbar.update(1)

