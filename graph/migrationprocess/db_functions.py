import re

def remove_digits_from_prenom(prenom):
    return re.sub(r'\d+$', '', prenom)