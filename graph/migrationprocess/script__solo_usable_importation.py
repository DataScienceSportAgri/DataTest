import sqlite3

try:
    # Connexion aux bases de données
    source_conn = sqlite3.connect('C:/Users/33682/Desktop/Backup/db.sqlite3')
    target_conn = sqlite3.connect('C:/Users/33682/PycharmProjects/DataTest/db.sqlite3')

    # Création de la nouvelle table dans la base cible
    target_conn.execute('''
        CREATE TABLE IF NOT EXISTS nouvelle_table (
            id INTEGER PRIMARY KEY,
            annee INTEGER,
            categorie_id INTEGER,
            coureur_id INTEGER,
            nom TEXT,
            prenom TEXT
        )
    ''')

    # Insertion des données de la source dans la nouvelle table de la cible
    source_cursor = source_conn.cursor()
    source_cursor.execute('''
        SELECT graph_coureurcategorie.id, graph_coureurcategorie.annee, graph_coureurcategorie.categorie_id,
               graph_coureurcategorie.coureur_id, graph_coureur.nom, graph_coureur.prenom
        FROM graph_coureur
        INNER JOIN graph_coureurcategorie ON graph_coureurcategorie.coureur_id = graph_coureur.id
    ''')

    rows = source_cursor.fetchall()

    # Insérer les données dans la nouvelle table
    target_cursor = target_conn.cursor()
    target_cursor.executemany('''
        INSERT INTO nouvelle_table (id, annee, categorie_id, coureur_id, nom, prenom)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', rows)

    # Valider les changements
    target_conn.commit()

except sqlite3.Error as e:
    print(f"Une erreur s'est produite : {e}")

finally:
    # Fermeture des connexions
    if source_conn:
        source_conn.close()
    if target_conn:
        target_conn.close()
