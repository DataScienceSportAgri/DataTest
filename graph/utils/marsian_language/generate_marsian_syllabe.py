import epitran
import random

epi_cz = epitran.Epitran('ces-Latn')  # Czech
epi_no = epitran.Epitran('nob-Latn')  # Norwegian Bokmål

def is_vowel(phoneme):
    return phoneme in 'aeiouæøå'

def generate_marsian_syllable(french_syllable1, french_syllable2):
    structure1 = not is_vowel(french_syllable1[0])
    structure2 = not is_vowel(french_syllable2[0])

    czech_words = ["baba", "deda", "kolo", "maso", "pivo"]
    norwegian_words = ["hus", "bil", "bok", "mat", "sol"]

    czech_syllables = [epi_cz.transliterate(word)[:2] for word in czech_words]
    norwegian_syllables = [epi_no.transliterate(word)[:2] for word in norwegian_words]

    filtered_czech = [s for s in czech_syllables if (not is_vowel(s[0])) == structure1]
    filtered_norwegian = [s for s in norwegian_syllables if (not is_vowel(s[0])) == structure2]

    syllable_pool = filtered_czech + filtered_norwegian
    marsian_syllable1, marsian_syllable2 = random.sample(syllable_pool, 2)

    return marsian_syllable1, marsian_syllable2
