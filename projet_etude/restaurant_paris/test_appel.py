import requests
import pandas as pd
from typing import Dict, List
import time

class TripAdvisorScraper:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.content.tripadvisor.com/api/v1"

    def search_location_id(self, query: str = "Paris, France") -> List[Dict]:
        """
        Première étape : rechercher les locationIds pour Paris
        """
        search_url = f"{self.base_url}/locations/search"
        
        params = {
            "key": self.api_key,
            "searchQuery": query,
            "language": "fr"
        }
        
        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            print("Réponse de recherche:", response.json())  # Pour debug
            return response.json().get("data", [])
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la recherche: {e}")
            return []

    def search_restaurants(self, location_id: str) -> List[Dict]:
        """
        Deuxième étape : rechercher les restaurants pour un locationId donné
        """
        restaurants_url = f"{self.base_url}/location/{location_id}/restaurants"
        
        params = {
            "key": self.api_key,
            "language": "fr"
        }
        
        try:
            response = requests.get(restaurants_url, params=params)
            response.raise_for_status()
            print(f"Restaurants trouvés pour location {location_id}:", response.json())  # Pour debug
            return response.json().get("data", [])
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la recherche des restaurants: {e}")
            return []

    def get_restaurant_details(self, location_id: str) -> Dict:
        """
        Troisième étape : obtenir les détails d'un restaurant spécifique
        """
        details_url = f"{self.base_url}/location/{location_id}/details"
        
        params = {
            "key": self.api_key,
            "language": "fr",
            "currency": "EUR"
        }
        
        try:
            response = requests.get(details_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des détails: {e}")
            return {}

    def collect_restaurant_data(self):
        """
        Processus complet de collecte des données
        """
        # 1. Obtenir le locationId de Paris
        paris_locations = self.search_location_id("Paris, France")
        if not paris_locations:
            print("Aucun location ID trouvé pour Paris")
            return pd.DataFrame()

        # Prendre le premier résultat pour Paris
        paris_id = paris_locations[0].get("location_id")
        print(f"Location ID pour Paris: {paris_id}")

        # 2. Obtenir la liste des restaurants
        restaurants = self.search_restaurants(paris_id)
        print(f"Nombre de restaurants trouvés: {len(restaurants)}")

        # 3. Collecter les détails pour chaque restaurant
        data = []
        for restaurant in restaurants[:50]:  # Limiter à 50 restaurants pour l'exemple
            rest_id = restaurant.get("location_id")
            if rest_id:
                details = self.get_restaurant_details(rest_id)
                if details:
                    data.append({
                        "nom": details.get("name", ""),
                        "adresse": details.get("address", ""),
                        "prix": details.get("price_level", ""),
                        "cuisine": details.get("cuisine", []),
                        "note_moyenne": details.get("rating", ""),
                        "nb_avis": details.get("num_reviews", 0),
                        "telephone": details.get("phone", ""),
                        "site_web": details.get("website", ""),
                        "latitude": details.get("latitude", ""),
                        "longitude": details.get("longitude", "")
                    })
                time.sleep(1)  # Pause pour respecter les limites de l'API

        return pd.DataFrame(data)

# Exemple d'utilisation
if __name__ == "__main__":
    API_KEY = "VOTRE_CLE_API"
    scraper = TripAdvisorScraper(API_KEY)
    
    # Lancer la collecte de données
    print("Début de la collecte des données...")
    df_restaurants = scraper.collect_restaurant_data()
    
    # Sauvegarder les résultats
    if not df_restaurants.empty:
        df_restaurants.to_csv("restaurants_paris.csv", index=False, encoding="utf-8")
        print("Données sauvegardées avec succès!")
    else:
        print("Aucune donnée n'a été collectée.")