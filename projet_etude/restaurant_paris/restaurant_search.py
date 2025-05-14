import requests

# Ta clé API Google Places (remplace 'YOUR_API_KEY' par ta clé API)
API_KEY = 'xx'

# Coordonnées de Paris (latitude, longitude)
location = '48.8566,2.3522'  # Paris
radius = 1500  # Rayon de recherche en mètres (1.5 km)

# URL de l'API Google Places pour la recherche à proximité
url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type=restaurant&key={API_KEY}"

# Faire la requête
response = requests.get(url)

# Vérifier si la requête a réussi
if response.status_code == 200:
    # Récupérer les résultats au format JSON
    data = response.json()

    # Pour chaque restaurant, récupérer les détails supplémentaires
    for restaurant in data['results']:
        name = restaurant['name']
        address = restaurant.get('vicinity', 'Adresse non disponible')
        place_id = restaurant['place_id']  # ID du lieu pour la requête suivante
        
        # URL de l'API Google Places pour obtenir les détails d'un lieu
        details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={API_KEY}"

        # Faire la requête pour obtenir les détails du restaurant
        details_response = requests.get(details_url)

        if details_response.status_code == 200:
            details_data = details_response.json()

            # Récupérer les informations détaillées
            result = details_data['result']
            reviews = result.get('reviews', [])
            rating = result.get('rating', 'Non disponible')  # Note globale
            nationalities = result.get('types', [])
            
            # Affichage des informations
            print(f"Nom : {name}")
            print(f"Adresse : {address}")
            print(f"Note : {rating}")
            print(f"Nationalité/type de cuisine : {', '.join(nationalities)}")

            if reviews:
                print("Avis :")
                for review in reviews[:3]:  # Afficher seulement les 3 premiers avis
                    author = review.get('author_name', 'Anonyme')
                    text = review.get('text', 'Avis non disponible')
                    print(f"- {author}: {text}")
            print("\n")
        else:
            print(f"Erreur lors de la récupération des détails pour {name}: {details_response.status_code}")
else:
    print(f"Erreur lors de la récupération des restaurants : {response.status_code}")
