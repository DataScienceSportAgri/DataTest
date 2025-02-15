import sqlite3
import os

# Chemin vers votre base de données SQLite
db_path = 'C:/Users/33682/Desktop/db.sqlite3'


# Vérifier si le fichier de base de données existe
if not os.path.exists(db_path):
    print(f"La base de données n'a pas été trouvée à l'emplacement : {db_path}")
    exit()

# Connexion à la base de données
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
try:
    # Créer la nouvelle table avec les entrées non existantes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coureurs_non_existants AS
    SELECT nt.*
    FROM nouvelle_table nt
    LEFT JOIN graph_coureur gc ON nt.coureur_id = gc.id
    WHERE gc.id IS NULL
    """)

    # Valider les changements
    conn.commit()

    print("Table 'coureurs_non_existants' créée avec succès.")

    # Afficher le nombre d'entrées dans la nouvelle table
    cursor.execute("SELECT COUNT(*) FROM coureurs_non_existants")
    count = cursor.fetchone()[0]
    print(f"Nombre d'entrées dans la table 'coureurs_non_existants': {count}")

except sqlite3.Error as e:
    print(f"Une erreur SQLite s'est produite : {e}")

finally:
    # Fermer la connexion
    conn.close()