import os
import requests
import pandas as pd
from datetime import datetime
import json

class RestaurantDataCollector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.content.tripadvisor.com/api/v1/"
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def search_location(self, query="Paris"):
        """
        Recherche un lieu sur TripAdvisor
        """
        search_params = {
            "searchQuery": query,
            "language": "fr",
            "category": "restaurants"
        }
        
        try:
            response = requests.get(
                self.base_url + "location/search",
                headers=self.headers,
                params=search_params
            )
            response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP
            
            search_data = response.json()
            if "data" in search_data and search_data["data"]:
                return search_data["data"][0]["location_id"]
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la recherche du lieu : {e}")
            return None

    def get_restaurants(self, location_id, limit=50):
        """
        Récupère les informations des restaurants pour un lieu donné
        """
        restaurant_params = {
            "location_id": location_id,
            "language": "fr",
            "limit": limit
        }
        
        try:
            response = requests.get(
                f"{self.base_url}location/{location_id}/restaurants",
                headers=self.headers,
                params=restaurant_params
            )
            response.raise_for_status()
            
            return response.json().get("data", [])
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des restaurants : {e}")
            return []

    def process_restaurant_data(self, restaurants):
        """
        Traite les données des restaurants pour créer un DataFrame
        """
        restaurant_list = []
        for resto in restaurants:
            restaurant_info = {
                "nom": resto.get("name"),
                "adresse": resto.get("address_obj", {}).get("address_string"),
                "prix": resto.get("price_level"),
                "cuisine": ", ".join([c.get("name", "") for c in resto.get("cuisine", [])]),
                "note": resto.get("rating"),
                "nombre_avis": resto.get("num_reviews"),
                "url": resto.get("web_url"),
                "latitude": resto.get("latitude"),
                "longitude": resto.get("longitude"),
                "arrondissement": self._extract_arrondissement(
                    resto.get("address_obj", {}).get("address_string", "")
                )
            }
            restaurant_list.append(restaurant_info)
        
        return pd.DataFrame(restaurant_list)

    def _extract_arrondissement(self, address):
        """
        Extrait l'arrondissement d'une adresse parisienne
        """
        if not address:
            return None
            
        import re
        match = re.search(r'750(\d{2})', address)
        return match.group(1) if match else None

    def save_data(self, df, filename=None):
        """
        Sauvegarde les données dans un fichier CSV
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"restaurants_paris_{timestamp}.csv"
            
        try:
            df.to_csv(filename, index=False, encoding="utf-8")
            print(f"Données sauvegardées dans {filename}")
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde : {e}")
            return False

def main():
    # Récupération de la clé API depuis une variable d'environnement
    api_key = os.getenv("TRIPADVISOR_API_KEY")
    if not api_key:
        print("Erreur : La clé API TripAdvisor n'est pas définie")
        return

    # Création du collecteur de données
    collector = RestaurantDataCollector(api_key)
    
    # Recherche de Paris
    print("Recherche de Paris...")
    location_id = collector.search_location()
    if not location_id:
        print("Impossible de trouver Paris dans TripAdvisor")
        return

    # Récupération des restaurants
    print("Récupération des restaurants...")
    restaurants = collector.get_restaurants(location_id)
    if not restaurants:
        print("Aucun restaurant trouvé")
        return

    # Traitement des données
    print("Traitement des données...")
    df = collector.process_restaurant_data(restaurants)
    
    # Affichage des statistiques
    print("\nStatistiques :")
    print(f"Nombre de restaurants collectés : {len(df)}")
    print("\nDistribution par arrondissement :")
    print(df['arrondissement'].value_counts())
    print("\nDistribution par type de cuisine :")
    print(df['cuisine'].value_counts().head())
    
    # Sauvegarde des données
    collector.save_data(df)

if __name__ == "__main__":
    main()