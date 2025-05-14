import pandas as pd
import numpy as np
from faker import Faker
import random

# Configuration
fake = Faker('fr_FR')
np.random.seed(42)

def generate_paris_address():
    arrondissements = [f"750{str(i).zfill(2)}" for i in range(1, 21)]
    streets = [
        "Rue de Rivoli", "Avenue des Champs-Élysées", "Rue Saint-Honoré",
        "Boulevard Saint-Germain", "Rue de la Paix", "Avenue Montaigne",
        "Rue du Faubourg Saint-Honoré", "Place Vendôme", "Rue de Rennes",
        "Boulevard Haussmann", "Rue de Passy", "Avenue Victor Hugo",
        "Rue Mouffetard", "Rue des Martyrs", "Rue Oberkampf",
        "Rue de Belleville", "Avenue de l'Opéra", "Rue Saint-Antoine",
        "Boulevard Voltaire", "Rue de la Roquette"
    ]
    return f"{random.randint(1, 150)} {random.choice(streets)}, {random.choice(arrondissements)} Paris"

def generate_restaurant_data(n_restaurants=500):
    # Données de base
    types_cuisine = {
        "Français": ["Bistrot", "Gastronomique", "Brasserie", "Traditionnel"],
        "Italien": ["Pizza", "Pasta", "Trattoria"],
        "Japonais": ["Sushi", "Ramen", "Izakaya"],
        "Chinois": ["Dim Sum", "Sichuan", "Cantonais"],
        "Indien": ["Nord-Indien", "Sud-Indien"],
        "Thaïlandais": ["Street food", "Traditionnel"],
        "Libanais": ["Mezze", "Grillades"],
        "Végétarien": ["Vegan", "Végétarien"],
        "Fusion": ["Asian Fusion", "Modern Fusion"],
        "Méditerranéen": ["Grec", "Espagnol", "Mezze"]
    }
    
    prix_categories = {
        "10-20": "Bon marché",
        "20-30": "Moyenne gamme",
        "30-50": "Moyenne gamme +",
        "50+": "Haut de gamme"
    }
    
    ambiances = [
        "Familial", "Romantique", "Branché", "Décontracté", "Élégant",
        "Traditionnel", "Modern", "Convivial", "Cosy", "Business"
    ]
    
    # Génération des données
    data = []
    existing_names = set()
    
    prefixes = ["Le", "La", "Les", "Chez", "Maison", "L'", "Au", "Aux"]
    suffixes = ["Bistrot", "Restaurant", "Table", "Cuisine", "Saveurs"]
    
    for _ in range(n_restaurants):
        # Génération d'un nom unique
        while True:
            if random.random() < 0.3:
                name = f"{random.choice(prefixes)} {fake.last_name()}"
            elif random.random() < 0.6:
                name = f"{random.choice(prefixes)} {fake.word().capitalize()}"
            else:
                name = f"{random.choice(prefixes)} {random.choice(suffixes)} {fake.last_name()}"
            if name not in existing_names:
                existing_names.add(name)
                break
        
        # Sélection du type de cuisine et sous-type
        cuisine_type = random.choice(list(types_cuisine.keys()))
        cuisine_subtype = random.choice(types_cuisine[cuisine_type])
        
        # Sélection du prix et de la catégorie
        prix = random.choice(list(prix_categories.keys()))
        categorie_prix = prix_categories[prix]
        
        # Génération de l'adresse
        adresse = generate_paris_address()
        arrondissement = adresse[-10:-6]  # Extrait le code postal
        
        # Coordonnées GPS (centrées sur Paris avec variation)
        latitude = 48.8566 + random.uniform(-0.05, 0.05)
        longitude = 2.3522 + random.uniform(-0.05, 0.05)
        
        # Génération de la note et du nombre d'avis
        note_base = random.uniform(3.5, 4.9)
        if categorie_prix == "Haut de gamme":
            note_base += 0.3
        note = min(5.0, round(note_base, 1))
        
        nb_avis = int(np.random.exponential(300)) + 10
        if categorie_prix == "Haut de gamme":
            nb_avis = int(nb_avis * 0.7)  # Moins d'avis pour les restaurants haut de gamme
        
        # Sélection des ambiances (1 à 3 maximum)
        nb_ambiances = random.randint(1, 3)
        selected_ambiances = ", ".join(random.sample(ambiances, nb_ambiances))
        
        restaurant = {
            "nom": name,
            "adresse": adresse,
            "arrondissement": arrondissement,
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
            "type_cuisine": cuisine_type,
            "specialite": cuisine_subtype,
            "prix_fourchette": prix,
            "categorie_prix": categorie_prix,
            "note_moyenne": note,
            "nb_avis": nb_avis,
            "ambiance": selected_ambiances,
            "telephone": f"01{str(random.randint(0, 99999999)).zfill(8)}",
            "vegetarien_friendly": random.choice([True, False]),
            "reservation_recommandee": random.choice([True, False]) if categorie_prix != "Bon marché" else False
        }
        data.append(restaurant)
    
    # Création du DataFrame
    df = pd.DataFrame(data)
    
    return df

if __name__ == "__main__":
    # Génération des données
    print("Génération du jeu de données des restaurants...")
    df_restaurants = generate_restaurant_data(500)
    
    # Sauvegarde en CSV
    filename = "restaurants_paris_dataset.csv"
    df_restaurants.to_csv(filename, index=False, encoding='utf-8')
    print(f"\nDataset sauvegardé dans {filename}")
    
    # Affichage des statistiques
    print("\nAperçu des données :")
    print(df_restaurants.head())
    
    print("\nStatistiques du dataset :")
    print("\nNombre de restaurants par type de cuisine :")
    print(df_restaurants['type_cuisine'].value_counts())
    
    print("\nNombre de restaurants par catégorie de prix :")
    print(df_restaurants['categorie_prix'].value_counts())
    
    print("\nDistribution des notes moyennes :")
    print(df_restaurants['note_moyenne'].describe())