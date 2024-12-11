def separer_noms_prenoms(nom_complet):
    parties = nom_complet.split()
    nom = []
    prenom = []
    particules = ['de', 'du', 'des', 'le', 'la', 'les', 'von', 'van', 'der', 'ten', 'ter', 'den', 'da', 'di']

    def a_deux_majuscules_consecutives(mot):
        return any(c1.isupper() and c2.isupper() for c1, c2 in zip(mot, mot[1:]))

    prenom_commence = False
    i = 0
    while i < len(parties):
        partie = parties[i]
        partie_lower = partie.lower()

        if prenom_commence:
            prenom.append(partie)
        elif partie.isupper() or a_deux_majuscules_consecutives(partie):
            nom.append(partie)
        elif partie_lower in particules:
            # Si c'est une particule, on l'ajoute au nom et on continue avec la partie suivante
            nom.append(partie)
            if i + 1 < len(parties):
                nom.append(parties[i + 1])
                i += 1
        elif partie == 'El':
            nom.append(partie)
        else:
            prenom_commence = True
            prenom.append(partie)

        i += 1

    nom_separe = ' '.join(nom)
    prenom_separe = ' '.join(prenom)

    return nom_separe, prenom_separe

