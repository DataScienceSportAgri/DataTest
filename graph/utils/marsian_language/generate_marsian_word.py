import pyphen
from graph.models import *

def separate_syllables(word):
    dic = pyphen.Pyphen(lang='fr_FR')
    return dic.inserted(word).split('-')


def generate_marsian_word(french_word):
    french_syllables = separate_syllables(french_word)
    marsian_syllables = []

    for i in range(0, len(french_syllables) - 1, 2):
        pair = SyllablePair.objects.filter(
            french_syllable1__content=french_syllables[i],
            french_syllable2__content=french_syllables[i + 1]
        ).first()

        if pair:
            marsian_syllables.append(pair.marsian_syllable1.content)
            marsian_syllables.append(pair.marsian_syllable2.content)

    # Gestion de la dernière syllabe si le nombre de syllabes est impair
    if len(french_syllables) % 2 != 0:
        last_french_syllable = french_syllables[-1]
        last_marsian_syllable = MarsianSyllable.objects.filter(
            content=last_french_syllable
        ).first()
        if last_marsian_syllable:
            marsian_syllables.append(last_marsian_syllable.content)

    return ''.join(marsian_syllables)