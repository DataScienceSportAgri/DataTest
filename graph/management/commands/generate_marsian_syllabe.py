from django.core.management.base import BaseCommand
from graph.models import FrenchSyllable, MarsianSyllable
from tqdm import tqdm
import random
import pyphen
import csv
import re
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Command(BaseCommand):
    help = 'Crée des syllabes marsiennes basées sur les syllabes françaises'

    def handle(self, *args, **options):
        # Initialiser les découpeurs de syllabes
        czech_dict = pyphen.Pyphen(lang='cs_CZ')
        norwegian_dict = pyphen.Pyphen(lang='nb_NO')

        # Charger les corpus tchèque et norvégien
        czech_words = self.load_czech_corpus()
        norwegian_words = self.load_norwegian_corpus()

        def get_czech_syllables(word):
            return czech_dict.inserted(word).split('-')

        def get_norwegian_syllables(word):
            return norwegian_dict.inserted(word).split('-')

        def is_consonant(char):
            return char.lower() not in 'aeiouáéíóúůýěāēīōū'

        def get_cv_pattern(syllable):
            return ''.join(['C' if is_consonant(c) else 'V' for c in syllable])

        def generate_marsian_syllable(french_syllable):
            structure = get_cv_pattern(french_syllable)

            czech_syllables = [syl for word in random.sample(czech_words, 50) for syl in get_czech_syllables(word)]
            norwegian_syllables = [syl for word in random.sample(norwegian_words, 50) for syl in
                                   get_norwegian_syllables(word)]

            syllable_pool = czech_syllables + norwegian_syllables

            marsian_syllable = ''
            for char in structure:
                if char == 'C':
                    marsian_syllable += random.choice([s[0] for s in syllable_pool if s and is_consonant(s[0])])
                else:
                    marsian_syllable += random.choice(
                        [s[1] for s in syllable_pool if len(s) > 1 and not is_consonant(s[1])])
            return marsian_syllable

        french_syllables = FrenchSyllable.objects.all()
        total_syllables = french_syllables.count()

        with tqdm(total=total_syllables, desc="Création des syllabes marsiennes") as pbar:
            for french_syllable in french_syllables:
                cv_pattern = get_cv_pattern(french_syllable.content)
                french_syllable.cv_pattern = cv_pattern
                french_syllable.save()

                marsian_syllable = generate_marsian_syllable(french_syllable.content)
                marsian_obj, created = MarsianSyllable.objects.get_or_create(content=marsian_syllable)
                marsian_obj.cv_pattern = cv_pattern
                marsian_obj.save()

                pbar.update(1)

        self.stdout.write(self.style.SUCCESS('Syllabes marsiennes créées avec succès'))

    def load_czech_corpus(self):
        file_path = r"C:\Users\33682\Documents\czech.csv"
        words = []

        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')

                # Obtenir le nom de la première colonne
                headers = next(reader)
                first_column_name = headers[0] if headers else None

                if not first_column_name:
                    raise ValueError("Le fichier CSV est vide ou mal formaté.")

                print(f"Utilisation de la première colonne : '{first_column_name}'")

                total_rows = sum(1 for row in reader)  # Compter les lignes pour tqdm
                csvfile.seek(0)  # Réinitialiser le pointeur du fichier
                next(reader)  # Sauter la ligne d'en-tête

                with tqdm(total=total_rows, desc="Processing Czech words") as pbar:
                    for row in reader:
                        if row:  # Vérifier que la ligne n'est pas vide
                            word = row[0]  # Prendre le premier élément de chaque ligne
                            # Supprimer les caractères alphanumériques mais conserver les caractères spéciaux tchèques
                            cleaned_word = re.sub(r'[^a-zA-ZáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]', '', word)
                            if cleaned_word:
                                words.append(cleaned_word)
                        pbar.update(1)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing Czech corpus: {str(e)}"))

        return words

    def load_norwegian_corpus(self):
        file_path = r"C:\Users\33682\Documents\norvegien.txt"

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            soup = BeautifulSoup(content, 'html.parser')
            word_list = soup.find_all('a')

            words = []
            with tqdm(total=len(word_list), desc="Traitement du corpus norvégien") as progress_bar:
                for word_tag in word_list:
                    word = word_tag.text.strip()
                    if word:
                        words.append(word)
                    progress_bar.update(1)

            return words

        except Exception as e:
            print(f"Erreur lors du chargement du corpus norvégien : {str(e)}")
            return []
