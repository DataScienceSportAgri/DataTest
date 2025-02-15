import math
import numpy as np
def log_scale(x):
    if x <= 0.5:
        return 0.2
    elif x >= 5:
        return 0
    else:
        # Calculer la valeur logarithmique
        log_value = math.log(x / 0.5) / math.log(5 / 0.5)
        # Inverser et ajuster l'échelle
        return 0.2 * (1 - log_value)

# Exemples d'utilisation
print(log_scale(5))    # Devrait afficher 0
print(log_scale(0.5))  # Devrait afficher 0.2
print(log_scale(1))    # Valeur intermédiaire
print(log_scale(2))    # Valeur intermédiaire

def calculate_trustability_score(normalized_nom, normalized_prenom):
    # Calculer une version ajustée de combined_value
    adjusted_nom = (normalized_nom / 25) * 0.6
    adjusted_prenom = (normalized_prenom / 50) * 0.4

    combined_value = (normalized_nom + 0.5 * normalized_prenom) * 0.6 + adjusted_nom + adjusted_prenom

    # Calculer le score final
    score = 0.7 - (np.log10(combined_value + 0.001) / np.log10(100 + 0.001)) * 0.7
    return max(0.0, min(0.7, score))

print('ici',calculate_trustability_score(1, 207))    # Devrait afficher 0
print(calculate_trustability_score(0.5, 0.2))  # Devrait afficher 0.2
print(calculate_trustability_score(1, 1))    # Valeur intermédiaire
print(calculate_trustability_score(2, 2))