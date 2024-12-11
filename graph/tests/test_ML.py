from graph.utils.fusionner_coureurs.RechercheDesCoureursCoherentsParML import Optimizer

import pandas as pd
import random











# Utilisation
df_original = pd.DataFrame({
    'index': range(6),
    'Nom': ['Nom'] * 6,
    'Prénom': [f'Prénom{i}' for i in range(6)],
    'ID_Coureur': range(6),
    'Categorie': [random.choice(['A1B', 'C2D', 'E3F']) for _ in range(6)],
    'Ordre': [random.randint(1, 14) for _ in range(6)],
    'Année': [random.randint(2014, 2024) for _ in range(6)]
})
df_original_2 = pd.DataFrame({
    'index': range(23),
    'Nom': ['Nom2'] * 23,
    'Prénom': [f'Prénom{i}' for i in range(23)],
    'ID_Coureur': range(23),
    'Categorie': [random.choice(['A1B', 'C2D', 'E3F']) for _ in range(23)],
    'Ordre': [random.randint(1, 14) for _ in range(23)],
    'Année': [random.randint(2014, 2024) for _ in range(23)]
})
optimizer = Optimizer()

dataframes_list_1 = optimizer.generate_dataframes_list(df_original, itteration_max=400, selection_parmi=250, nb_list=120)


# Séparation des dataframes et des scores
dataframes_1 = []
scores_1 = []

for df, score in dataframes_list_1:
    dataframes_1.append(df)
    scores_1.append(score)

# Maintenant, vous avez deux listes séparées :
# - 'dataframes' contient tous les dataframes sélectionnés
# - 'scores' contient les scores correspondants

# Exemple d'utilisation
print(f"Nombre de dataframes parmi la liste 1 sélectionnés : {len(dataframes_1)}")
print(f"Scores correspondants : {scores_1}")

# Si vous voulez accéder à un dataframe spécifique et son score
for i, (df, score) in enumerate(zip(dataframes_1, scores_1)):
    print(f"Dataframe test un {i+1} - Score : {score}")
    print(df)  # Affiche les premières lignes du dataframe
    print("\n")


print("get all patterns", optimizer.get_all_patterns())
dataframes_list_2 = optimizer.generate_dataframes_list(df_original_2, itteration_max=400, selection_parmi=250, nb_list=120)
# Séparation des dataframes et des scores
dataframes_2 = []
scores_2 = []

for df, score in dataframes_list_2:
    dataframes_2.append(df)
    scores_2.append(score)

# Maintenant, vous avez deux listes séparées :
# - 'dataframes' contient tous les dataframes sélectionnés
# - 'scores' contient les scores correspondants

# Exemple d'utilisation
print(f"Nombre de dataframes parmi la liste deux sélectionnés : {len(dataframes_2)}")
print(f"Scores correspondants : {scores_2}")

# Si vous voulez accéder à un dataframe spécifique et son score
for i, (df, score) in enumerate(zip(dataframes_2, scores_2)):
    print(f"Dataframe test deux {i+1} - Score : {score}")
    print(df)  # Affiche les premières lignes du dataframe
    print("\n")


print("get all patterns", optimizer.get_all_patterns())
