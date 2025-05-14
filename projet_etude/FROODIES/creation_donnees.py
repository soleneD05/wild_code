import pandas as pd
import numpy as np
import random
from faker import Faker
import csv
import json
from datetime import time, datetime

# Configuration
fake = Faker('fr_FR')
Faker.seed(42)  # Pour la reproductibilité
random.seed(42)
np.random.seed(42)

# Constantes
ARRONDISSEMENTS = [f"750{i:02d}" for i in range(1, 21)]  # 75001 à 75020

CUISINE_DU_MONDE = [
    "Français", "Italien", "Japonais", "Chinois", "Indien", "Libanais", "Marocain", 
    "Espagnol", "Américain", "Mexicain", "Thaïlandais", "Vietnamien", "Coréen", 
    "Grecque", "Brésilien", "Africain", "Caribéen"
]

TYPES_CUISINE = [
    "Végétarien", "Végan", "Fruits de mer", "Burger", "Pizza",
    "Crêperie", "Bistrot", "Brasserie", "Gastronomique", "Street food", "Tapas",
    "Ramen", "Sushi"
]

PRIX_FOURCHETTE = [
    "10-20", "20-30", "30-50", "50-100", "100+"
]

CATEGORIE_PRIX = [
    "Bon marché", "Moyenne gamme", "Haut de gamme"
]

# Correspondance entre fourchette de prix et catégorie
PRIX_TO_CATEGORIE = {
    "10-20": "Bon marché",
    "20-30": "Moyenne gamme",
    "30-50": "Moyenne gamme",
    "50-100": "Haut de gamme",
    "100+": "Haut de gamme"
}

AMBIANCES = [
    "Romantique", "Familial", "Branché", "Cosy", "Élégant", "Décontracté", 
    "Animé", "Calme", "Traditionnel", "Moderne", "Festif", "Intime",
    "Terrasse", "Vue panoramique", "Authentique", "Historique", "Convivial"
]

NOMS_FRANCAIS = [
    "Le", "La", "Les", "Chez", "Au", "Aux", "L'Atelier", "L'Assiette", "Bistrot", "Brasserie",
    "Café", "Restaurant", "Auberge", "Relais", "Table", "Cuisine", "Maison"
]

ADJECTIFS_FRANCAIS = [
    "Petit", "Grand", "Vieux", "Nouveau", "Bon", "Délicieux", "Gourmand", "Savoureux",
    "Royal", "Impérial", "Parisien", "Traditionnel", "Authentique", "Moderne"
]

NOMS_SPECIFIQUES = [
    "du Marché", "de Paris", "du Chef", "Gourmand", "de la Tour", "de la Seine",
    "du Palais", "des Saveurs", "des Délices", "des Gourmets", "du Coin", "de la Place"
]

RUES_PARISIENNES = [
    "rue de Rivoli", "avenue des Champs-Élysées", "boulevard Saint-Germain",
    "rue de la Paix", "rue Saint-Honoré", "rue Montorgueil", "boulevard Haussmann",
    "rue Oberkampf", "rue Mouffetard", "rue Cler", "rue des Martyrs", "avenue Montaigne",
    "rue du Faubourg Saint-Antoine", "rue de Buci", "rue Lepic", "rue des Rosiers",
    "boulevard de Clichy", "rue de la Roquette", "rue Daguerre", "avenue de l'Opéra",
    "rue de Turbigo", "rue du Cherche-Midi", "avenue de Wagram", "place Vendôme",
    "boulevard Raspail", "rue de Passy", "rue de la Pompe", "rue de la Convention",
    "boulevard de Grenelle", "rue Didot", "rue de la Gaîté", "boulevard Barbès",
    "rue Caulaincourt", "avenue de Clichy", "rue du Commerce", "rue Vaugirard",
    "avenue Parmentier", "boulevard Voltaire", "rue Saint-Maur", "rue de Belleville",
    "boulevard de la Villette", "rue de Ménilmontant", "avenue de la République",
    "boulevard de Magenta", "rue du Temple", "rue de Bretagne", "rue Réaumur"
]

# Nouvelles constantes pour les colonnes ajoutées
JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

QUALITE_NOURRITURE = [
    "Fait maison", "Produits locaux", "Bio", "Produits de saison", "Label qualité", 
    "Producteurs locaux", "Circuit court", "Slow food", "Importation directe",
    "Produits fermiers", "Cuisine traditionnelle", "Spécialités maison"
]

# Reconnaissances gastronomiques
RECONNAISSANCES = [
    {"nom": "Guide Michelin", "annees": ["2021", "2022", "2023", "2024"], "distinctions": ["Étoilé", "Bib Gourmand", "Assiette Michelin"]},
    {"nom": "Gault & Millau", "annees": ["2021", "2022", "2023", "2024"], "distinctions": ["Toques", "Jeune Talent", "Prix d'Excellence"]},
    {"nom": "La Liste", "annees": ["2022", "2023", "2024"], "distinctions": ["Top 1000", "Innovation Award"]},
    {"nom": "Fooding", "annees": ["2021", "2022", "2023", "2024"], "distinctions": ["Meilleure Table", "Meilleur Bistrot", "Prix Spécial"]},
    {"nom": "50 Best", "annees": ["2022", "2023", "2024"], "distinctions": ["Top 50", "Prix Spécial"]},
    {"nom": "Tables Remarquables", "annees": ["2022", "2023", "2024"], "distinctions": ["Sélection"]},
    {"nom": "Maître Restaurateur", "annees": ["2021", "2022", "2023", "2024"], "distinctions": ["Titre"]},
    {"nom": "Collège Culinaire de France", "annees": ["2021", "2022", "2023", "2024"], "distinctions": ["Restaurant de Qualité"]}
]

ASPECTS_COMMENTAIRES = [
    "service", "ambiance", "nourriture", "prix", "qualité", "portions", "décoration",
    "emplacement", "propreté", "rapidité", "originalité", "authenticité", "expérience"
]

# Aspects spécifiques pour les avis
ASPECTS_SERVICE = [
    "personnel", "service", "serveur", "serveuse", "accueil", "attention", 
    "attente", "réservation", "disponibilité", "efficacité"
]

ASPECTS_NOURRITURE = [
    "plat", "entrée", "dessert", "carte des vins", "menu", "présentation", 
    "saveur", "cuisson", "fraîcheur", "ingrédients", "goût", "portion"
]

ADJECTIFS_POSITIFS = [
    "excellent", "délicieux", "parfait", "exceptionnel", "savoureux", "succulent", 
    "incroyable", "fantastique", "remarquable", "superbe", "authentique", "chaleureux",
    "agréable", "attentionné", "efficace", "convivial", "impressionnant", "généreux"
]

ADJECTIFS_NEGATIFS = [
    "décevant", "médiocre", "insuffisant", "mauvais", "cher", "long", "bruyant",
    "froid", "fade", "petit", "ordinaire", "quelconque", "impersonnel", "négligé"
]

PHRASES_CONCLUSION_POSITIVES = [
    "Je recommande vivement !", "Un incontournable à Paris.", "J'y retournerai avec plaisir.",
    "Une excellente adresse.", "À découvrir absolument !", "Un vrai coup de cœur.",
    "Une valeur sûre.", "Un restaurant qui vaut le détour."
]

PHRASES_CONCLUSION_NEGATIVES = [
    "Je ne recommande pas.", "À éviter.", "Je ne reviendrai pas.", 
    "Il y a mieux ailleurs.", "Décevant dans l'ensemble.", "Pas à la hauteur de sa réputation.",
    "Trop cher pour ce que c'est.", "Une déception."
]

# Domaines communs pour les sites web de restaurants
DOMAINES_WEB = [
    "restaurantparis.fr", "bistro-paris.com", "restaurant-paris.fr", "mangerparis.fr", 
    "parisrestaurant.com", "labonnetable.fr", "restoparis.fr", "delicesparis.com", 
    "goutsdeparis.fr", "manger-paris.com", "saveursdeparis.fr"
]

# Constantes pour les attributs professionnels
NIVEAU_BRUIT = ["Calme", "Modéré", "Animé"]
CAPACITE_GROUPE = [0, 6, 8, 10, 15, 20, 30, 50]  # 0 signifie pas de grands groupes
DUREE_REPAS_AFFAIRES = ["Rapide (moins d'1h)", "Standard (1h-1h30)", "Long (plus d'1h30)"]
TYPE_ESPACE_PRIVE = ["Salon séparé", "Espace semi-privatif", "Étage entier", "Salle à part"]

# Fonction pour générer un nom de restaurant
def generer_nom_restaurant():
    # Différents formats de noms
    format_type = random.randint(1, 5)
    
    if format_type == 1:  # Format "Le/La + Nom"
        if random.random() < 0.7:  # Nom français
            article = random.choice(NOMS_FRANCAIS)
            nom = random.choice(ADJECTIFS_FRANCAIS) + " " + random.choice(NOMS_SPECIFIQUES)
            return f"{article} {nom}"
        else:  # Nom étranger
            return fake.company().split()[0]
    
    elif format_type == 2:  # Format "Chez + Prénom"
        return f"Chez {fake.first_name()}"
    
    elif format_type == 3:  # Format "Les + Nom de famille"
        return f"Les {fake.last_name()}"
    
    elif format_type == 4:  # Format nom propre
        return f"{fake.last_name()} & {fake.last_name()}"
    
    else:  # Format créatif
        mots = ["Saveur", "Délice", "Goût", "Assiette", "Table", "Cuisine", "Menu", "Palais"]
        mot1 = random.choice(mots)
        mot2 = random.choice(["de Paris", "d'Or", "Royal", "Impérial", "Parisien", "Français"])
        return f"{mot1} {mot2}"

# Fonction pour générer un numéro de rue
def generer_numero_rue():
    return str(random.randint(1, 150))

# Fonction pour générer une adresse complète
def generer_adresse():
    numero = generer_numero_rue()
    rue = random.choice(RUES_PARISIENNES)
    arrondissement = random.choice(ARRONDISSEMENTS)
    return f"{numero} {rue}, {arrondissement} Paris"

# Fonction pour générer une note moyenne
def generer_note():
    # Distribution biaisée vers les bonnes notes pour plus de réalisme
    return round(random.uniform(3.0, 5.0), 1)

# Fonction pour générer un numéro de téléphone français mobile (06 ou 07 + 8 chiffres)
def generer_telephone():
    prefixe = random.choice(["06", "07"])
    return f"{prefixe}{random.randint(10000000, 99999999)}"

# Fonction pour générer un site web
def generer_site_web(nom_restaurant):
    # Simplifier le nom pour le site web
    nom_simple = nom_restaurant.lower().replace(' ', '').replace("'", "").replace("-", "")
    # Tronquer si trop long
    if len(nom_simple) > 15:
        nom_simple = nom_simple[:15]
    # Ajouter un domaine
    domaine = random.choice(DOMAINES_WEB)
    return f"https://www.{nom_simple}.{domaine}"

# Fonction pour générer un lien vers la carte
def generer_lien_carte(site_web):
    suffixes = ["menu", "carte", "notre-carte", "la-carte", "nos-plats"]
    suffixe = random.choice(suffixes)
    return f"{site_web}/{suffixe}"

# Fonction pour générer des jours d'ouverture
def generer_jours_ouverture():
    # La plupart des restaurants ont une fermeture hebdomadaire
    if random.random() < 0.7:  # 70% des restaurants ferment au moins un jour
        jours_ouverts = JOURS_SEMAINE.copy()
        nombre_jours_fermes = random.choices([1, 2], weights=[0.8, 0.2])[0]  # La plupart ferment 1 jour
        jours_fermes = random.sample(JOURS_SEMAINE, nombre_jours_fermes)
        for jour in jours_fermes:
            jours_ouverts.remove(jour)
        return jours_ouverts
    else:
        return JOURS_SEMAINE  # 30% des restaurants ouverts tous les jours

# Fonction pour formater l'heure (HH:MM)
def formater_heure(h, m):
    return f"{h:02d}:{m:02d}"

# Fonction pour générer des horaires d'ouverture (midi et soir) en fonction des jours d'ouverture
def generer_horaires_ouverture(jours_ouverture):
    horaires = {}
    
    for jour in JOURS_SEMAINE:
        if jour in jours_ouverture:
            # Horaire du midi (variations possibles)
            heure_debut_midi = random.randint(11, 12)
            minute_debut_midi = random.choice([0, 15, 30])
            heure_fin_midi = random.randint(14, 15)
            minute_fin_midi = random.choice([0, 15, 30, 45])
            
            # Horaire du soir (variations possibles)
            heure_debut_soir = random.randint(18, 19)
            minute_debut_soir = random.choice([0, 15, 30])
            heure_fin_soir = random.randint(22, 23)
            minute_fin_soir = random.choice([0, 15, 30, 45])
            
            # Certains restaurants n'ouvrent que le midi ou que le soir
            service_midi = random.random() < 0.95  # 95% ouvrent le midi
            service_soir = random.random() < 0.98  # 98% ouvrent le soir
            
            # Si ni midi ni soir, on force l'un des deux (éviter fermeture totale un jour d'ouverture)
            if not service_midi and not service_soir:
                if random.random() < 0.5:
                    service_midi = True
                else:
                    service_soir = True
            
            plages_horaires = []
            if service_midi:
                plages_horaires.append(f"{formater_heure(heure_debut_midi, minute_debut_midi)}-{formater_heure(heure_fin_midi, minute_fin_midi)}")
            if service_soir:
                plages_horaires.append(f"{formater_heure(heure_debut_soir, minute_debut_soir)}-{formater_heure(heure_fin_soir, minute_fin_soir)}")
            
            horaires[jour] = plages_horaires
        else:
            horaires[jour] = ["Fermé"]
    
    return horaires

# Fonction pour générer des avis (commentaires) d'utilisateurs
def generer_avis(note_moyenne, nb_avis, ambiance, type_cuisine, specialite=""):
    avis_complets = []
    # On génère un nombre réduit d'avis détaillés (pour ne pas surcharger le dataset)
    nb_avis_details = min(nb_avis, random.randint(5, 15))
    
    for i in range(nb_avis_details):
        # La note individuelle varie autour de la moyenne
        ecart = random.uniform(-1.0, 1.0)
        note_individuelle = max(1.0, min(5.0, note_moyenne + ecart))
        note_individuelle = round(note_individuelle, 1)
        
        date_avis = fake.date_between(start_date='-2y', end_date='today')
        
        # Ton général de l'avis (positif/négatif) en fonction de la note
        ton_positif = note_individuelle >= 3.5
        
        # Construction de l'avis
        paragraphes = []
        
        # Premier paragraphe - impression générale
        cuisine_mention = type_cuisine.lower() if type_cuisine else "variée"
        if specialite and type_cuisine:
            cuisine_mention = f"{type_cuisine.lower()} {specialite.lower()}"
            
        if ton_positif:
            debut = random.choice([
                f"J'ai adoré mon expérience à ce restaurant. ",
                f"Une très belle découverte! ",
                f"Excellente adresse dans le quartier. ",
                f"Je suis ravi(e) d'avoir testé ce restaurant. ",
                f"Un vrai coup de cœur pour ce restaurant {cuisine_mention}. ",
                f"Une belle surprise culinaire {cuisine_mention}. ",
                f"Un incontournable pour les amateurs de cuisine {cuisine_mention}. "
            ])
        else:
            debut = random.choice([
                f"Je suis déçu(e) de mon expérience dans ce restaurant. ",
                f"Ce restaurant n'a pas été à la hauteur de mes attentes. ",
                f"Je ne comprends pas les bonnes critiques de ce restaurant. ",
                f"Une expérience décevante dans l'ensemble. ",
                f"Ce restaurant {cuisine_mention} n'est pas à recommander. ",
                f"Malgré sa réputation, ce restaurant {cuisine_mention} m'a déçu. "
            ])
        
        paragraphes.append(debut)
        
        # Deuxième paragraphe - commentaire sur le service (presque toujours présent)
        if random.random() < 0.9:  # 90% de chance de commenter le service
            aspect_service = random.choice(ASPECTS_SERVICE)
            if ton_positif:
                adjectif = random.choice(ADJECTIFS_POSITIFS)
                commentaire = random.choice([
                    f"Le {aspect_service} était {adjectif}. ",
                    f"J'ai trouvé le {aspect_service} vraiment {adjectif}. ",
                    f"Un {aspect_service} {adjectif} qui fait la différence. ",
                    f"Le {aspect_service} est attentionné et professionnel. ",
                    f"Mention spéciale pour le {aspect_service}, {adjectif}! "
                ])
            else:
                adjectif = random.choice(ADJECTIFS_NEGATIFS)
                commentaire = random.choice([
                    f"Le {aspect_service} était {adjectif}. ",
                    f"J'ai trouvé le {aspect_service} plutôt {adjectif}. ",
                    f"Le {aspect_service} laisse à désirer, assez {adjectif}. ",
                    f"Point négatif: un {aspect_service} {adjectif}. ",
                    f"Le {aspect_service} manquait d'attention et de professionnalisme. "
                ])
            paragraphes.append(commentaire)
        
        # Troisième paragraphe - commentaire sur la nourriture (toujours présent)
        aspects_nourriture = random.sample(ASPECTS_NOURRITURE, random.randint(1, 3))
        commentaires_nourriture = []
        
        for aspect in aspects_nourriture:
            if ton_positif:
                adjectif = random.choice(ADJECTIFS_POSITIFS)
                commentaire = random.choice([
                    f"Le {aspect} était {adjectif}. ",
                    f"J'ai trouvé le {aspect} vraiment {adjectif}. ",
                    f"Un {aspect} {adjectif} qui mérite le détour. ",
                    f"Mention spéciale pour le {aspect}, {adjectif}! ",
                    f"Le {aspect} était parfaitement préparé et {adjectif}. "
                ])
            else:
                adjectif = random.choice(ADJECTIFS_NEGATIFS)
                commentaire = random.choice([
                    f"Le {aspect} était {adjectif}. ",
                    f"J'ai trouvé le {aspect} plutôt {adjectif}. ",
                    f"Le {aspect} laisse à désirer, assez {adjectif}. ",
                    f"Point négatif: un {aspect} {adjectif}. ",
                    f"Le {aspect} manquait de saveur et était plutôt {adjectif}. "
                ])
            commentaires_nourriture.append(commentaire)
        
        paragraphes.append("".join(commentaires_nourriture))
        
        # Quatrième paragraphe - autres aspects
        autres_aspects = [a for a in ASPECTS_COMMENTAIRES if a not in ASPECTS_SERVICE and a not in ASPECTS_NOURRITURE]
        aspects_a_commenter = random.sample(autres_aspects, random.randint(0, 2))
        
        if aspects_a_commenter:
            commentaires_autres = []
            for aspect in aspects_a_commenter:
                if ton_positif:
                    adjectif = random.choice(ADJECTIFS_POSITIFS)
                    commentaire = f"Le {aspect} était {adjectif}. "
                else:
                    adjectif = random.choice(ADJECTIFS_NEGATIFS)
                    commentaire = f"Le {aspect} était {adjectif}. "
                commentaires_autres.append(commentaire)
            
            paragraphes.append("".join(commentaires_autres))
        
        # Cinquième paragraphe - ambiance (souvent présent)
        if random.random() < 0.7:  # 70% de chance de mentionner l'ambiance
            if ton_positif:
                paragraphes.append(f"L'ambiance {ambiance.lower()} est vraiment agréable. ")
            else:
                paragraphes.append(f"L'ambiance se veut {ambiance.lower()} mais n'est pas convaincante. ")
        
        # Conclusion
        if ton_positif:
            conclusion = random.choice(PHRASES_CONCLUSION_POSITIVES)
        else:
            conclusion = random.choice(PHRASES_CONCLUSION_NEGATIVES)
        
        paragraphes.append(conclusion)
        
        # Assemblage de l'avis complet
        avis_texte = " ".join(paragraphes)
        
        # Plats spécifiques mentionnés
        plats_mentionnes = []
        if random.random() < 0.6:  # 60% de chance de mentionner un plat spécifique
            nb_plats = random.randint(1, 3)
            for _ in range(nb_plats):
                nom_plat = fake.word().capitalize()
                if type_cuisine in ["Français", "Italien", "Espagnol", "Méditerranéen"]:
                    suffixe = random.choice(["à la", "au", "aux", "du chef", "maison", "traditionnel"])
                    nom_plat += f" {suffixe}"
                elif type_cuisine in ["Japonais", "Chinois", "Thaïlandais", "Vietnamien", "Coréen"]:
                    suffixe = random.choice(["spécial", "traditionnel", "royal", "impérial", "authentique"])
                    nom_plat += f" {suffixe}"
                plats_mentionnes.append(nom_plat)
        
        avis = {
            "note": note_individuelle,
            "date": date_avis.strftime("%Y-%m-%d"),
            "auteur": fake.name(),
            "commentaire": avis_texte,
            "plats_mentionnes": plats_mentionnes
        }
        
        avis_complets.append(avis)
    
    return avis_complets

# Fonction pour générer des informations sur la qualité de la nourriture
def generer_qualite_nourriture():
    # Nombre de labels/caractéristiques de qualité (entre 0 et 4)
    nb_qualites = random.choices([0, 1, 2, 3, 4], weights=[0.1, 0.3, 0.3, 0.2, 0.1])[0]
    
    if nb_qualites == 0:
        return []
    
    return random.sample(QUALITE_NOURRITURE, nb_qualites)

# Fonction pour générer des reconnaissances (guides, prix)
def generer_reconnaissances(categorie_prix, note_moyenne):
    reconnaissances = []
    
    # Plus le restaurant est cher et bien noté, plus il a de chances d'avoir des distinctions
    prob_base = 0
    if categorie_prix == "Moyenne gamme" and note_moyenne >= 4.0:
        prob_base = 0.10  # 10% de chance d'avoir une reconnaissance
    elif categorie_prix == "Haut de gamme" and note_moyenne >= 4.0:
        prob_base = 0.25  # 25% de chance d'avoir une reconnaissance
    elif categorie_prix == "Haut de gamme" and note_moyenne >= 4.5:
        prob_base = 0.40  # 40% de chance d'avoir une reconnaissance
    
    # Si le restaurant a une chance d'avoir une reconnaissance
    if random.random() < prob_base:
        # Pour chaque guide/reconnaissance possible
        for reconnaissance in RECONNAISSANCES:
            # Probabilité diminuée pour chaque guide supplémentaire
            if random.random() < prob_base * (0.7 ** len(reconnaissances)):
                # Choix de l'année
                annee = random.choice(reconnaissance["annees"])
                
                # Choix de la distinction en fonction du prix et de la note
                distinctions = reconnaissance["distinctions"]
                poids_distinctions = []
                
                # Pour le Guide Michelin
                if reconnaissance["nom"] == "Guide Michelin":
                    if categorie_prix == "Haut de gamme" and note_moyenne >= 4.7:
                        # Chance d'être étoilé
                        poids_distinctions = [0.1, 0.3, 0.6]  # Étoilé, Bib Gourmand, Assiette
                    elif note_moyenne >= 4.3:
                        # Plus de chance d'avoir un Bib Gourmand
                        poids_distinctions = [0.01, 0.5, 0.49]
                    else:
                        # Principalement des Assiettes
                        poids_distinctions = [0.0, 0.2, 0.8]
                # Pour les autres guides
                else:
                    # Distribution par défaut, favorisant légèrement les distinctions moins prestigieuses
                    poids_distinctions = [1.0/len(distinctions)] * len(distinctions)
                    # Ajustement pour favoriser légèrement la première distinction (souvent la plus prestigieuse)
                    if len(poids_distinctions) > 1:
                        poids_distinctions[0] *= 0.5
                
                # Normalisation des poids
                somme_poids = sum(poids_distinctions)
                poids_distinctions = [p/somme_poids for p in poids_distinctions]
                
                # Sélection de la distinction
                distinction = random.choices(distinctions, weights=poids_distinctions, k=1)[0]
                
                # Cas particulier pour les Toques de Gault & Millau
                if distinction == "Toques" and reconnaissance["nom"] == "Gault & Millau":
                    nb_toques = random.choices([1, 2, 3, 4, 5], weights=[0.40, 0.30, 0.20, 0.08, 0.02], k=1)[0]
                    distinction = f"{nb_toques} Toques"
                
                # Ajout de la reconnaissance
                reconnaissances.append({
                    "guide": reconnaissance["nom"],
                    "annee": annee,
                    "distinction": distinction
                })
    
    return reconnaissances

# Ajout de la fonction pour générer le code postal à partir de l'arrondissement
def generer_code_postal(arrondissement):
    """
    Génère un code postal à partir du code d'arrondissement.
    Par exemple, 75001 pour le 1er arrondissement.
    
    Args:
        arrondissement (str): Le code d'arrondissement (ex: "75001").
    
    Returns:
        str: Le code postal correspondant.
    """
    return arrondissement

# Fonction pour générer les attributs professionnels
def generer_attributs_professionnels(ambiance, categorie_prix):
    """
    Génère des attributs spécifiques pour les repas professionnels.
    
    Args:
        ambiance (str): L'ambiance du restaurant, qui influence certains attributs.
        categorie_prix (str): La catégorie de prix, qui influence certains attributs.
    
    Returns:
        dict: Un dictionnaire contenant les attributs professionnels générés.
         """
    # La probabilité d'être adapté aux repas d'affaires dépend de l'ambiance et du prix
    prob_adapte = 0.3  # Probabilité de base
    
    # Les restaurants calmes, élégants ou modernes ont plus de chances d'être adaptés
    if ambiance in ["Calme", "Élégant", "Moderne", "Intime", "Traditionnel"]:
        prob_adapte += 0.3
    
    # Les restaurants bruyants ou festifs ont moins de chances d'être adaptés
    if ambiance in ["Animé", "Festif", "Branché"]:
        prob_adapte -= 0.1
    
    # Les restaurants haut de gamme ont plus de chances d'être adaptés
    if categorie_prix == "Haut de gamme":
        prob_adapte += 0.2
    
    # Générer les attributs professionnels
    adapte_repas_affaires = random.random() < prob_adapte
    
    # Niveau de bruit corrélé avec l'ambiance
    if ambiance in ["Calme", "Intime", "Élégant"]:
        niveau_bruit_probs = [0.7, 0.25, 0.05]  # Calme, Modéré, Animé
    elif ambiance in ["Festif", "Animé", "Branché"]:
        niveau_bruit_probs = [0.05, 0.25, 0.7]  # Calme, Modéré, Animé
    else:
        niveau_bruit_probs = [0.25, 0.5, 0.25]  # Calme, Modéré, Animé
    
    niveau_bruit = random.choices(NIVEAU_BRUIT, weights=niveau_bruit_probs)[0]
    
    # Espace privé plus probable dans les restaurants haut de gamme
    espace_prive_prob = 0.1  # Probabilité de base
    if categorie_prix == "Haut de gamme":
        espace_prive_prob += 0.4
    elif categorie_prix == "Moyenne gamme":
        espace_prive_prob += 0.2
    
    espace_prive = random.random() < espace_prive_prob
    
    # WiFi et prises électriques
    wifi = random.random() < 0.7  # 70% des restaurants ont le WiFi
    prise_electrique = random.random() < 0.5  # 50% ont des prises accessibles
    
    # Capacité de groupe - plus élevée pour certaines ambiances
    if ambiance in ["Familial", "Convivial", "Traditionnel", "Décontracté"]:
        capacite_groupe_probs = [0.05, 0.1, 0.15, 0.2, 0.2, 0.15, 0.1, 0.05]  # Plus de chances d'avoir des capacités importantes
    elif ambiance in ["Intime", "Romantique"]:
        capacite_groupe_probs = [0.3, 0.3, 0.2, 0.1, 0.05, 0.03, 0.01, 0.01]  # Plus axé sur les petits groupes
    else:
        capacite_groupe_probs = [0.1, 0.15, 0.2, 0.2, 0.15, 0.1, 0.05, 0.05]  # Distribution équilibrée
    
    capacite_groupe = random.choices(CAPACITE_GROUPE, weights=capacite_groupe_probs)[0]
    
    # Équipement de présentation - surtout dans les restaurants adaptés aux repas d'affaires
    equipement_presentation_prob = 0.05  # Probabilité de base
    if adapte_repas_affaires:
        equipement_presentation_prob += 0.2
    if categorie_prix == "Haut de gamme":
        equipement_presentation_prob += 0.1
    
    equipement_presentation = random.random() < equipement_presentation_prob
    
    # Type d'espace privé (si disponible)
    type_espace_prive = None
    if espace_prive:
        type_espace_prive = random.choice(TYPE_ESPACE_PRIVE)
    
    # Durée typique recommandée pour repas d'affaires
    if adapte_repas_affaires:
        if ambiance in ["Calme", "Élégant"] and categorie_prix == "Haut de gamme":
            duree_repas_affaires = random.choices(DUREE_REPAS_AFFAIRES, weights=[0.1, 0.3, 0.6])[0]
        elif ambiance in ["Décontracté", "Branché"]:
            duree_repas_affaires = random.choices(DUREE_REPAS_AFFAIRES, weights=[0.5, 0.4, 0.1])[0]
        else:
            duree_repas_affaires = random.choices(DUREE_REPAS_AFFAIRES, weights=[0.3, 0.5, 0.2])[0]
    else:
        duree_repas_affaires = None
    
    # Services business spécifiques
    service_facturation_entreprise = random.random() < 0.4  # 40% proposent de la facturation pour entreprises
    reservation_derniere_minute = random.random() < 0.3  # 30% acceptent les réservations de dernière minute pour groupes
    
    # Retourner un dictionnaire avec tous les attributs professionnels
    return {
        "adapte_repas_affaires": adapte_repas_affaires,
        "niveau_bruit": niveau_bruit,
        "espace_prive": espace_prive,
        "type_espace_prive": type_espace_prive,
        "wifi": wifi,
        "prise_electrique": prise_electrique,
        "capacite_groupe": capacite_groupe,
        "equipement_presentation": equipement_presentation,
        "duree_repas_affaires": duree_repas_affaires,
        "service_facturation_entreprise": service_facturation_entreprise,
        "reservation_derniere_minute": reservation_derniere_minute
    }

# Génération du dataset complet
def generer_dataset_restaurants(nombre_restaurants=500):
    """
    Génère un dataset complet de restaurants parisiens avec toutes les caractéristiques.
    
    Args:
        nombre_restaurants (int): Le nombre de restaurants à générer. Par défaut 500.
        
    Returns:
        pandas.DataFrame: Un DataFrame contenant tous les restaurants générés.
    """
    restaurants = []
    noms_utilises = set()  # Pour éviter les doublons

    for _ in range(nombre_restaurants):
        # Génération d'un nom unique
        nom = generer_nom_restaurant()
        while nom in noms_utilises:
            nom = generer_nom_restaurant()
        noms_utilises.add(nom)
        
        adresse = generer_adresse()
        arrondissement = adresse.split(',')[1].strip().split()[0]
        code_postal = generer_code_postal(arrondissement)
        
        # Type de cuisine est maintenant toujours une nationalité (CUISINE_DU_MONDE)
        cuisine_du_monde = random.choice(CUISINE_DU_MONDE)
        
        # Spécialité est maintenant toujours un type de cuisine (TYPES_CUISINE)
        # 70% de chance d'avoir une spécialité
        if random.random() < 0.7:
            type_cuisine = random.choice(TYPES_CUISINE)
        else:
            type_cuisine = ""
        
        # Prix
        prix_fourchette = random.choice(PRIX_FOURCHETTE)
        categorie_prix = PRIX_TO_CATEGORIE[prix_fourchette]
        
        note_moyenne = generer_note()
        nb_avis = random.randint(10, 1000)
        
        # Ambiance
        ambiance = random.choice(AMBIANCES)
        
        # Téléphone (maintenant mobile 06 ou 07)
        telephone = generer_telephone()
        
        # Site web et lien vers la carte
        site_web = generer_site_web(nom)
        lien_carte = generer_lien_carte(site_web)
        
        # Options supplémentaires
        reservation_recommandee = random.random() < 0.5  # 50% de chance que la réservation soit recommandée
        
        # Coordonnées géographiques approximatives pour Paris
        latitude = round(48.8 + random.uniform(0, 0.17), 6)
        longitude = round(2.25 + random.uniform(0, 0.17), 6)
        
        # Jours d'ouverture et horaires cohérents
        jours_ouverture = generer_jours_ouverture()
        horaires_ouverture = generer_horaires_ouverture(jours_ouverture)
        
        # Nouvelles données
        avis = generer_avis(note_moyenne, nb_avis, ambiance, cuisine_du_monde, type_cuisine)
        qualite_nourriture = generer_qualite_nourriture()
        reconnaissances = generer_reconnaissances(categorie_prix, note_moyenne)
        
        # Attributs professionnels
        attributs_pro = generer_attributs_professionnels(ambiance, categorie_prix)
        
        # Construction du dictionnaire restaurant
        restaurant = {
            "nom": nom,
            "adresse": adresse,
            "arrondissement": arrondissement,
            "code_postal": code_postal,
            "latitude": latitude,
            "longitude": longitude,
            "cuisine_du_monde": cuisine_du_monde,
            "type_cuisine": type_cuisine,
            "prix_fourchette": prix_fourchette,
            "categorie_prix": categorie_prix,
            "note_moyenne": note_moyenne,
            "nb_avis": nb_avis,
            "ambiance": ambiance,
            "telephone": telephone,
            "site_web": site_web,
            "lien_carte": lien_carte,
            "reservation_recommandee": str(reservation_recommandee).lower(),
            "jours_ouverture": jours_ouverture,
            "horaires_ouverture": json.dumps(horaires_ouverture, ensure_ascii=False),
            "avis": json.dumps(avis, ensure_ascii=False),
            "qualite_nourriture": qualite_nourriture,
            "reconnaissances": json.dumps(reconnaissances, ensure_ascii=False)
        }
        
        # Ajout des attributs professionnels
        for key, value in attributs_pro.items():
            restaurant[key] = value
        
        restaurants.append(restaurant)

    # Création du DataFrame
    df = pd.DataFrame(restaurants)
    
    return df

# Fonction principale qui orchestre la génération du dataset et l'exportation
def main():
    """
    Fonction principale qui génère le dataset et l'exporte au format CSV.
    Affiche également quelques statistiques sur le dataset.
    """
    print("Début de la génération du dataset des restaurants parisiens...")
    
    # Génération du dataset complet
    nb_restaurants = 500  # Vous pouvez ajuster ce nombre selon vos besoins
    df = generer_dataset_restaurants(nb_restaurants)
    
    print(f"Dataset généré avec succès : {len(df)} restaurants.")
    
    # Export en CSV
    fichier_csv = "paris_restaurants_enrichi.csv"
    df.to_csv(fichier_csv, index=False, encoding='utf-8')
    print(f"Dataset exporté avec succès dans le fichier : {fichier_csv}")
    
    # Affichage des premières lignes pour vérification
    print("\nAperçu des premières lignes :")
    print(df[["nom", "adresse", "cuisine_du_monde", "type_cuisine", "prix_fourchette", "note_moyenne", "site_web"]].head())
    
    # Statistiques sur le dataset
    print("\nStatistiques sur le dataset :")
    
    # Répartition par arrondissement
    repartition_arr = df['arrondissement'].value_counts()
    print(f"Nombre d'arrondissements représentés : {len(repartition_arr)}")
    
    # Répartition par type de cuisine
    print("\nRépartition par cuisine du monde :")
    print(df['cuisine_du_monde'].value_counts().head(5))
    
    # Répartition par spécialité
    if 'type_cuisine' in df.columns:
        print("\nRépartition par type de cuisine (spécialité) :")
        print(df['type_cuisine'].value_counts().head(5))
    
    # Répartition par catégorie de prix
    print("\nRépartition par catégorie de prix :")
    print(df['categorie_prix'].value_counts())
    
    # Répartition par ambiance
    print("\nRépartition par ambiance :")
    print(df['ambiance'].value_counts().head(5))
    
    # Statistiques sur les notes
    print(f"\nNote moyenne globale : {df['note_moyenne'].mean():.2f}")
    print(f"Note médiane : {df['note_moyenne'].median():.2f}")
    print(f"Note minimale : {df['note_moyenne'].min()}")
    print(f"Note maximale : {df['note_moyenne'].max()}")
    
    # Vérifier le pourcentage de restaurants avec des reconnaissances
    restaurants_avec_reconnaissances = df[df["reconnaissances"] != "[]"].shape[0]
    pourcentage = (restaurants_avec_reconnaissances / len(df)) * 100
    print(f"\nPourcentage de restaurants avec reconnaissances: {pourcentage:.1f}%")
    
    # Distribution des guides
    guides_distribution = {}
    for i, reconnaissances in enumerate(df["reconnaissances"]):
        reco_list = json.loads(reconnaissances) if reconnaissances != "[]" else []
        for reco in reco_list:
            guide = reco.get("guide")
            if guide not in guides_distribution:
                guides_distribution[guide] = 0
            guides_distribution[guide] += 1
    
    if guides_distribution:
        print("\nDistribution des reconnaissances par guide:")
        for guide, count in sorted(guides_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"- {guide}: {count} restaurants")
    
    # Export d'un échantillon au format JSON pour plus de lisibilité
    sample_json = df.head(3).to_json(orient='records', force_ascii=False, indent=4)
    with open('sample_restaurants.json', 'w', encoding='utf-8') as f:
        f.write(sample_json)
    print("\nÉchantillon de 3 restaurants exporté au format JSON dans le fichier 'sample_restaurants.json'")

# Point d'entrée pour l'exécution du script
if __name__ == "__main__":
    main()