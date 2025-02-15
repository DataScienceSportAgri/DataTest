from django.core.management.base import BaseCommand
from collections import Counter, defaultdict
import re
from graph.models import Course, CourseType
import geonamescache
import spacy


def clean_first_element(string_list):
    if not string_list:
        return string_list

    # Motif regex pour correspondre aux caractères à supprimer au début de la chaîne
    pattern = r'^[.,;)(+]+\s*'
    special_chars_pattern = r'^[-,;:+()]+$'

    # Itérer sur les éléments de la liste
    for i in range(len(string_list)):
        # Nettoyer l'élément actuel
        string_list[i] = re.sub(pattern, '', string_list[i])

        # Si l'élément actuel n'est pas entièrement composé de caractères spéciaux, arrêter l'itération
        if not re.match(special_chars_pattern, string_list[i]):
            break

    return string_list

# Charger le modèle français
nlp = spacy.load('fr_core_news_sm')
def get_determiners():
    doc = nlp('le la les un une des du de la')
    determiners = [token.text for token in doc if token.pos_ == 'DET']
    return determiners


def check_and_modify_words(words):
    articles = ['le', 'la', 'les']
    prepositions = ['de', 'des']

    modified_words = []
    skip_next = False
    for i, word in enumerate(words):
        if skip_next:
            skip_next = False
            continue

        if word in articles and i + 1 < len(words) and words[i + 1] in prepositions:
            if word == 'le':
                modified_words.extend([word, 'challenge'])
            elif word == 'la':
                modified_words.extend([word, 'course'])
            elif word == 'les':
                modified_words.extend([word, 'foulées'])
            skip_next = True
        else:
            modified_words.append(word)

    return modified_words

def remove_repetitions(words, determiners):
    unique_words = []
    for word in words:
        if word in determiners or word not in unique_words:
            unique_words.append(word)
    return unique_words
# Exemple d'utilisation
determiners = get_determiners()

def capitalize_long_words(name):
    words = name.split()
    if words:
        # Mettre une majuscule au premier mot
        words[0] = words[0].capitalize()
        # Traiter les mots suivants
        capitalized_words = [word.capitalize() if len(word) >= 5 else word for word in words[1:]]
        return ' '.join([words[0]] + capitalized_words)
    return ''  # Retourner une chaîne vide si le nom est vide



import re

import re

def clean_digits(text, course_distance):
    # Liste des mois
    months = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
              'août', 'septembre', 'octobre', 'novembre', 'décembre']

    # Fonction pour traiter les correspondances
    def replace_match(match):
        if match.group(1):  # Si c'est un chiffre suivi de 'D' ou 'D+'
            return match.group(0)
        elif match.group(2):  # Si c'est suivi de 'n' ou 'ième'
            return match.group(0)
        elif match.group(3):  # Si c'est suivi d'un nom de mois
            return match.group(0)
        elif match.group(4) and int(match.group(4)) != course_distance:  # Si c'est un chiffre suivi de 'm' et différent de course.distance
            return match.group(0)
        elif match.group(5):  # Si c'est un chiffre devant "n°"
            return match.group(0)
        elif match.group(6):  # Si c'est entre parenthèses
            return match.group(0)
        else:
            return ''  # Supprimer dans les autres cas

    # Pattern pour trouver les cas à traiter
    pattern = (
        r'(\d+(?:\s*[Dd]\+?))'  # Chiffres suivis de 'D' ou 'D+' (avec ou sans espace)
        r'|(\d+(?:\s*(?:n|ième|eme|ème)))'  # Chiffres suivis de 'n' ou 'ième'
        r'|(\d+\s*(?:' + '|'.join(months) + '))'  # Chiffres suivis d'un nom de mois
        r'|(\d+)(?=\s*m)'  # Chiffres suivis de 'm'
        r'|(\d+\s*n°)'  # Chiffres suivis de "n°" (avec ou sans espace)
        r'|(\([^)]*\d+[^)]*\))'  # Tout contenu entre parenthèses contenant au moins un chiffre
        r'|(?<!\d)\d+'  # Autres chiffres isolés
    )

    cleaned_text = re.sub(pattern, replace_match, text)
    return cleaned_text



def to_singular(word):
    if word=='cross':
        return word
    if word.endswith('s'):
        return word[:-1]
    return word


class Command(BaseCommand):
    help = 'Analyse les noms de courses, met à jour les types et nettoie les noms'

    def handle(self, *args, **options):
        """
        Handles the script to identify and clean race names, classify races by type, and create or update race types in the
        database. The process involves multiple stages, including identifying city names, country names, and other common
        strings to exclude from race names, as well as generating relevant race types based on frequency analysis.

        :param args: Positional arguments passed to the management command. Not used in the current implementation.
        :type args: tuple
        :param options: Keyword arguments passed to the management command. Not used in the current implementation.
        :type options: dict
        :return: None
        """
        # Récupérer tous les noms de courses
        courses = Course.objects.all().order_by('annee')

        gc = geonamescache.GeonamesCache()

        # Obtenir les villes
        cities = gc.get_cities()
        excluded_words = set(city['name'].lower() for city in cities.values())

        # Ajouter les pays
        countries = gc.get_countries()
        excluded_words.update(country['name'].lower() for country in countries.values())

        # Ajouter les continents
        continents = gc.get_continents()
        excluded_words.update(continent['name'].lower() for continent in continents.values())

        # Ajouter les états américains
        us_states = gc.get_us_states()
        excluded_words.update(state['name'].lower() for state in us_states.values())
        excluded_words.update(['semi', 'marathon', 'km', 'vins', 'village', 'villages', 'vin', 'course', 'saint', 'rives'
                                  , 'pour', 'tout', 'tous', 'courir', 'verte', 'puits', 'citrouille', 'courses', 'indien', 'vallee', 'gois',
                               'vigneron', 'juine', 'ronde', 'soldat', 'marne', 'russy', 'foret', 'parempuyre', 'decales', 'cisse', 'vignerons',
                               'solidaire', 'souffle', 'sancerre', 'abraysiennes', 'meudonnaise', 'remparts', 'blanquefortaises'])

        # Créer ou récupérer les types de course de base
        road_type, _ = CourseType.objects.get_or_create(nom='Course sur route')
        duathlon_type, _ = CourseType.objects.get_or_create(nom='Duathlon')
        marche_nordique_type, _ = CourseType.objects.get_or_create(nom='Marche nordique')
        marche_type, _ = CourseType.objects.get_or_create(nom='Marche')
        nocturne_type, _ = CourseType.objects.get_or_create(nom='Nocturne')
        rando_type, _ = CourseType.objects.get_or_create(nom='Randonnée')
        trail_type, _ = CourseType.objects.get_or_create(nom='Trail')

        # Première passe : identifier et créer les types de course
        word_counter = Counter()
        for course in courses:
            # Remplacer uniquement les tirets qui ne sont pas entre parenthèses
            words = re.findall(r'\b\w+\b',
                               re.sub(r'\((.*?)\)', lambda m: m.group(0).replace('-', ''), course.nom.lower()))
            word_counter.update(words)

        relevant_words = [word for word, count in word_counter.items()
                          if count >= 15 and len(word) > 3 and word.lower() not in excluded_words and not re.search(r'\d', word)]

        relevant_words = [to_singular(word) for word in relevant_words]

        for word in relevant_words:
            CourseType.objects.get_or_create(nom=word.capitalize())

        # Récupérer tous les types de course pour la suppression dans les noms
        all_course_types = CourseType.objects.values_list('nom', flat=True)
        type_names = set(course_type.lower() for course_type in all_course_types)

        # Deuxième passe : nettoyer les noms et assigner les types
        for course in courses:
            # Nettoyer le nom de la course
            cleaned_name = course.nom.lower()
            distance = course.distance

            # Supprimer les chiffres successifs sauf ceux précédant "ième" ou "n"
            cleaned_name = clean_digits(cleaned_name, distance)
            cleaned_name = re.sub(r'\b\d{1,2}(?=km\b)', '', cleaned_name)
            cleaned_name = re.sub(r'\b\d{1,2}(?=kms\b)', '', cleaned_name)

            # Remplacer les tirets par des espaces sauf après "saint"
            cleaned_name = re.sub(r'(?<!saint)-', ' ', cleaned_name)

            cleaned_name = re.sub(r'\b\w*km(s)?\w*\b', '', cleaned_name)
            # Déterminer le type de la course
            course_words = set(cleaned_name.split())
            course_words_list = list(course_words)
            course_words = {to_singular(word) for word in course_words}
            if 'duathlon' in course_words:
                course.type = duathlon_type
            for i, word in enumerate(course_words_list):
                if word=='marche':
                    try:
                        newt_word = course_words_list[i+1]
                        if newt_word=='nordique':
                            course.type = marche_nordique_type
                        else:
                            course.type = marche_type
                            break
                    except:
                        course.type = marche_type
                        break
            if 'randonnée' in course_words:
                course.type = rando_type
            if 'nocturne' in course_words:
                course.type = nocturne_type
            if any('trail' in word.lower() for word in course_words):
                course.type = trail_type
            else:
                matching_words = course_words.intersection(type_names)
                if matching_words:
                    type_word = max(matching_words, key=len)  # Prendre le plus long mot correspondant
                    course.type = CourseType.objects.get(nom__iexact=type_word)
                else:
                    course.type = road_type

            # Supprimer les mots liés au type (insensible à la casse)
            words_to_remove = {'foulée', 'boucle'}
            type_names = {word for word in type_names if word not in words_to_remove}

            # Diviser le nom nettoyé en mots
            words = cleaned_name.split()

            # Filtrer les mots
            filtered_words = []
            for i, word in enumerate(words):
                if word.lower() not in type_names or (word.lower() == 'trail' and i < 2):
                    filtered_words.append(word)
                elif word.lower() == 'trail' and i >= 2:
                    continue  # Ignorer 'trail' s'il n'est pas en première ou deuxième position

            cleaned_name = ' '.join(filtered_words)

            # Supprimer les répétitions de mots
            words = cleaned_name.split()

            unique_words = remove_repetitions(words, determiners)
            modified_words = check_and_modify_words(unique_words)
            modified_words = clean_first_element(modified_words)
            cleaned_name = ' '.join(modified_words)

            # Mettre en majuscule les mots de 5 caractères ou plus
            cleaned_name = capitalize_long_words(cleaned_name)

            # Mettre à jour le nom nettoyé dans l'objet course
            course.nom = cleaned_name
            course.save()

        self.stdout.write(self.style.SUCCESS('Mise à jour des types et des noms de courses terminée'))
