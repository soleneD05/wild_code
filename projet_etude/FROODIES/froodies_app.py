import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import plotly.express as px
import plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
from datetime import datetime
import random

# Configuration de la page
st.set_page_config(
    page_title="FROODIES",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction pour charger les données
@st.cache_data
def load_data():
    """
    Charge les données des restaurants depuis le fichier CSV et gère les erreurs potentielles.
    
    Returns:
        DataFrame: Un DataFrame pandas contenant les données des restaurants.
    """
    try:
        # Charger le dataset avec les colonnes enrichies
        df = pd.read_csv("paris_restaurants_enrichi.csv")
        
        # Assurer que toutes les colonnes nécessaires existent
        required_columns = [
            'nom', 'adresse', 'prix_fourchette', 'type_cuisine', 'specialite',
            'ambiance', 'arrondissement', 'note_moyenne', 'nb_avis', 
            'latitude', 'longitude', 'jours_ouverture', 'horaires_ouverture',
            'avis', 'qualite_nourriture', 'reconnaissances'
        ]
        
        # Vérifier et créer des colonnes manquantes avec des valeurs par défaut
        for col in required_columns:
            if col not in df.columns:
                if col == 'jours_ouverture':
                    df[col] = df.apply(lambda x: ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"], axis=1)
                elif col == 'horaires_ouverture':
                    df[col] = df.apply(lambda x: json.dumps({"Lundi": ["12:00-14:30", "19:00-22:30"]}), axis=1)
                elif col == 'avis':
                    df[col] = df.apply(lambda x: json.dumps([]), axis=1)
                elif col == 'qualite_nourriture':
                    df[col] = df.apply(lambda x: [], axis=1)
                elif col == 'reconnaissances':
                    df[col] = df.apply(lambda x: json.dumps([]), axis=1)
                else:
                    df[col] = "Non spécifié"
        
        # Assurer que les valeurs numériques sont correctes
        df['note_moyenne'] = pd.to_numeric(df['note_moyenne'], errors='coerce').fillna(4.0)
        df['nb_avis'] = pd.to_numeric(df['nb_avis'], errors='coerce').fillna(0)
        
        # Ajouter un ID si non présent
        if 'id' not in df.columns:
            df['id'] = df.index
            
        # Conversion des colonnes JSON en objets Python si nécessaire
        try:
            for col in ['avis', 'horaires_ouverture', 'reconnaissances']:
                if col in df.columns and df[col].iloc[0] is not None and isinstance(df[col].iloc[0], str):
                    df[col] = df[col].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
        except Exception as e:
            st.warning(f"Problème lors de la conversion des données JSON: {e}")
            
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        # Retourner un DataFrame vide avec les colonnes requises
        return pd.DataFrame(columns=required_columns)

# Fonction pour charger les données utilisateur (historique, préférences, filtres personnalisés)
@st.cache_data
def load_user_data():
    """
    Charge les données de l'utilisateur depuis un fichier JSON ou crée un profil par défaut.
    
    Returns:
        dict: Les données utilisateur incluant l'historique, les favoris et les filtres personnalisés.
    """
    # Dans une vraie app, ceci viendrait d'une base de données
    # Pour ce prototype, nous utilisons un fichier JSON local
    if os.path.exists("user_data.json"):
        with open("user_data.json", "r") as f:
            return json.load(f)
    else:
        # Données utilisateur par défaut
        return {
            "search_history": [],
            "viewed_restaurants": [],
            "favorite_restaurants": [],
            "custom_filters": [
                {
                    "id": 1,
                    "name": "Dîner romantique",
                    "conditions": {
                        "ambiance": ["Romantique", "Intime"],
                        "prix_fourchette": ["30-50", "50-100"],
                        "note_moyenne": 4.5
                    }
                },
                {
                    "id": 2,
                    "name": "Déjeuner rapide",
                    "conditions": {
                        "ambiance": ["Décontracté"],
                        "prix_fourchette": ["10-20", "20-30"],
                        "jours_ouverture": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
                    }
                }
            ]
        }

# Fonction pour sauvegarder les données utilisateur
def save_user_data(user_data):
    """
    Sauvegarde les données utilisateur dans un fichier JSON.
    
    Args:
        user_data (dict): Les données utilisateur à sauvegarder.
    """
    with open("user_data.json", "w") as f:
        json.dump(user_data, f)

# Fonction pour enregistrer une recherche dans l'historique
def save_search(filters):
    """
    Sauvegarde les filtres de recherche utilisés dans l'historique de l'utilisateur.
    
    Args:
        filters (dict): Les filtres appliqués lors de la recherche.
    """
    user_data = load_user_data()
    user_data["search_history"].append({
        "timestamp": datetime.now().isoformat(),
        "filters": filters
    })
    # Garder seulement les 20 dernières recherches
    if len(user_data["search_history"]) > 20:
        user_data["search_history"] = user_data["search_history"][-20:]
    save_user_data(user_data)

# Fonction pour calculer les filtres les plus utilisés
def get_most_used_filters():
    """
    Analyse l'historique de recherche pour déterminer les filtres les plus utilisés.
    
    Returns:
        list: Liste triée des filtres avec leur fréquence d'utilisation.
    """
    user_data = load_user_data()
    
    # Comptage des filtres utilisés
    filter_counts = {}
    for search in user_data["search_history"]:
        for filter_name, filter_value in search["filters"].items():
            if filter_name not in filter_counts:
                filter_counts[filter_name] = {"count": 0, "values": {}}
            
            filter_counts[filter_name]["count"] += 1
            
            # Pour les valeurs des filtres (multi ou single)
            if isinstance(filter_value, list):
                for val in filter_value:
                    if val not in filter_counts[filter_name]["values"]:
                        filter_counts[filter_name]["values"][val] = 0
                    filter_counts[filter_name]["values"][val] += 1
            else:
                val = filter_value
                if val not in filter_counts[filter_name]["values"]:
                    filter_counts[filter_name]["values"][val] = 0
                filter_counts[filter_name]["values"][val] += 1
    
    # Tri par nombre d'utilisations
    sorted_filters = sorted(filter_counts.items(), key=lambda x: x[1]["count"], reverse=True)
    
    return sorted_filters

# Fonction pour suivre les restaurants consultés
def track_restaurant_view(restaurant_id, restaurant_name, user_data):
    """
    Ajoute un restaurant à l'historique de consultation de l'utilisateur.
    
    Args:
        restaurant_id (int): L'identifiant du restaurant consulté.
        restaurant_name (str): Le nom du restaurant.
        user_data (dict): Les données utilisateur à mettre à jour.
        
    Returns:
        dict: Les données utilisateur mises à jour.
    """
    # Ajouter à l'historique de consultation
    user_data["viewed_restaurants"].append({
        "restaurant_id": restaurant_id,
        "restaurant_name": restaurant_name,
        "timestamp": datetime.now().isoformat()
    })
    
    # Limiter la taille de l'historique (garder les 30 dernières consultations)
    if len(user_data["viewed_restaurants"]) > 30:
        user_data["viewed_restaurants"] = user_data["viewed_restaurants"][-30:]
        
    return user_data

# Système de recommandation basé sur le contenu
def content_based_recommendations(df, restaurant_id=None, user_preferences=None, top_n=5):
    """
    Génère des recommandations de restaurants basées sur la similarité.
    
    Args:
        df (DataFrame): Le dataset complet des restaurants.
        restaurant_id (int, optional): ID d'un restaurant spécifique pour recommandations similaires.
        user_preferences (dict, optional): Préférences utilisateur pour générer des recommandations.
        top_n (int): Nombre de recommandations à retourner.
        
    Returns:
        DataFrame: Les restaurants recommandés.
    """
    # Enrichir les caractéristiques des restaurants
    df['features'] = (
        df['type_cuisine'] + ' ' + 
        df['specialite'].fillna('') + ' ' + 
        df['ambiance'] + ' ' + 
        df['arrondissement'] + ' ' + 
        df['prix_fourchette'] + ' ' + 
        df['qualite_nourriture'].apply(lambda x: ' '.join(x) if isinstance(x, list) else '')
    )
    
    # Vectorisation
    tfidf = TfidfVectorizer(stop_words='french')
    tfidf_matrix = tfidf.fit_transform(df['features'])
    
    # Matrice de similarité
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    if restaurant_id is not None:
        # Recommandations basées sur un restaurant
        idx = df.index[df['id'] == restaurant_id].tolist()[0]
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:top_n+1]  # Exclut le restaurant lui-même
        restaurant_indices = [i[0] for i in sim_scores]
        return df.iloc[restaurant_indices]
    
    elif user_preferences is not None:
        # Création d'un "restaurant virtuel" basé sur les préférences
        virtual_features = ' '.join([
            user_preferences.get('type_cuisine', ''),
            user_preferences.get('specialite', ''),
            user_preferences.get('ambiance', ''),
            user_preferences.get('arrondissement', ''),
            user_preferences.get('prix_fourchette', ''),
            ' '.join(user_preferences.get('qualite_nourriture', []))
        ])
        
        # Vectoriser ce "restaurant virtuel"
        virtual_vec = tfidf.transform([virtual_features])
        
        # Calculer la similarité avec tous les restaurants
        sim_scores = cosine_similarity(virtual_vec, tfidf_matrix).flatten()
        
        # Trier par similarité
        sim_scores_with_idx = list(enumerate(sim_scores))
        sim_scores_with_idx = sorted(sim_scores_with_idx, key=lambda x: x[1], reverse=True)
        sim_scores_with_idx = sim_scores_with_idx[:top_n]
        restaurant_indices = [i[0] for i in sim_scores_with_idx]
        
        return df.iloc[restaurant_indices]
    
    else:
        # Si aucun paramètre n'est fourni, retourner les restaurants les mieux notés
        return df.sort_values('note_moyenne', ascending=False).head(top_n)

# Fonction pour créer la carte des restaurants
def create_restaurant_map(df_filtered):
    """
    Crée une carte interactive avec tous les restaurants filtrés.
    
    Args:
        df_filtered (DataFrame): DataFrame contenant les restaurants à afficher.
        
    Returns:
        folium.Map: Une carte Folium avec des marqueurs pour chaque restaurant.
    """
    # Création de la carte centrée sur Paris
    m = folium.Map(location=[48.8566, 2.3522], zoom_start=12)
    
    # Création d'un cluster de marqueurs
    marker_cluster = MarkerCluster().add_to(m)
    
    # Ajout des marqueurs pour chaque restaurant
    for idx, row in df_filtered.iterrows():
        # Déterminer les horaires d'aujourd'hui
        today = datetime.now().strftime("%A")
        today_fr = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", 
                    "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", 
                    "Sunday": "Dimanche"}[today]
        
        # Récupérer les horaires pour aujourd'hui si disponibles
        horaires_auj = "Non disponible"
        if isinstance(row.get('horaires_ouverture'), dict) and today_fr in row['horaires_ouverture']:
            horaires_auj = ", ".join(row['horaires_ouverture'][today_fr])
        
        # Informations sur les reconnaissances
        reconnaissances_html = ""
        if isinstance(row.get('reconnaissances'), list) and row['reconnaissances']:
            reconnaissances_html = "<p><b>Distinctions:</b><br>"
            for r in row['reconnaissances'][:2]:  # Limiter à 2 distinctions pour la clarté
                reconnaissances_html += f"• {r['guide']} {r['annee']} - {r['distinction']}<br>"
            reconnaissances_html += "</p>"
            
        # Informations sur la qualité
        qualite_html = ""
        if isinstance(row.get('qualite_nourriture'), list) and row['qualite_nourriture']:
            qualite_html = f"<p><b>Qualité:</b> {', '.join(row['qualite_nourriture'][:3])}</p>"
        
        html = f"""
            <div style='width: 250px'>
                <h4>{row['nom']}</h4>
                <p><b>Cuisine:</b> {row['type_cuisine']}</p>
                <p><b>Prix:</b> {row['prix_fourchette']}</p>
                <p><b>Note:</b> {row['note_moyenne']}/5 ({row['nb_avis']} avis)</p>
                <p><b>Adresse:</b> {row['adresse']}</p>
                <p><b>Aujourd'hui:</b> {horaires_auj}</p>
                {qualite_html}
                {reconnaissances_html}
            </div>
        """
        
        # Déterminer la couleur du marqueur
        # Rouge pour les restaurants avec reconnaissance, favoris en or, autres en bleu
        marker_color = 'blue'
        if row['nom'] in st.session_state.get('favorites', []):
            marker_color = 'orange'
        elif isinstance(row.get('reconnaissances'), list) and row['reconnaissances']:
            marker_color = 'red'
            
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(html, max_width=300),
            tooltip=row['nom'],
            icon=folium.Icon(color=marker_color)
        ).add_to(marker_cluster)
    
    return m

# Fonction pour suggérer des filtres personnalisés basés sur l'historique
def suggest_custom_filters(df):
    """
    Analyse l'historique de recherche pour suggérer des filtres personnalisés.
    
    Args:
        df (DataFrame): Le dataset des restaurants.
        
    Returns:
        list: Suggestions de filtres personnalisés.
    """
    user_data = load_user_data()
    search_history = user_data["search_history"]
    
    if len(search_history) < 3:
        return []  # Pas assez d'historique pour faire des suggestions
    
    # Compter les combinaisons de filtres
    filter_combos = {}
    for search in search_history:
        # Créer une signature de cette recherche (combinaison de filtres)
        combo_key = []
        for k, v in search["filters"].items():
            if isinstance(v, list):
                combo_key.append(f"{k}:{','.join(sorted(v))}")
            else:
                combo_key.append(f"{k}:{v}")
        
        combo_key = "||".join(sorted(combo_key))
        
        if combo_key not in filter_combos:
            filter_combos[combo_key] = {
                "count": 0,
                "filters": search["filters"]
            }
        
        filter_combos[combo_key]["count"] += 1
    
    # Trouver les combinaisons fréquentes qui ne sont pas déjà des filtres personnalisés
    existing_filter_names = [f["name"].lower() for f in user_data["custom_filters"]]
    suggestions = []
    
    for combo, data in filter_combos.items():
        if data["count"] >= 3:  # Utilisé au moins 3 fois
            # Générer un nom pour ce filtre
            filter_name = generate_filter_name(data["filters"], df)
            
            if filter_name.lower() not in existing_filter_names:
                suggestions.append({
                    "name": filter_name,
                    "conditions": data["filters"],
                    "usage_count": data["count"],
                    "confidence": min(data["count"] * 10, 95)  # Score de confiance basé sur la fréquence
                })
    
    # Trier par fréquence d'utilisation
    suggestions = sorted(suggestions, key=lambda x: x["usage_count"], reverse=True)
    
    return suggestions[:3]  # Limiter à 3 suggestions

# Fonction pour générer un nom de filtre basé sur ses conditions
def generate_filter_name(filter_conditions, df):
    """
    Génère un nom descriptif pour un filtre basé sur ses conditions.
    
    Args:
        filter_conditions (dict): Les conditions du filtre.
        df (DataFrame): Le dataset des restaurants.
        
    Returns:
        str: Un nom descriptif pour le filtre.
    """
    name_parts = []
    
    # Vérifier les principales conditions
    if "type_cuisine" in filter_conditions:
        cuisines = filter_conditions["type_cuisine"]
        if isinstance(cuisines, list) and len(cuisines) == 1:
            name_parts.append(f"Cuisine {cuisines[0]}")
        elif isinstance(cuisines, str):
            name_parts.append(f"Cuisine {cuisines}")
    
    if "prix_fourchette" in filter_conditions:
        prix = filter_conditions["prix_fourchette"]
        if isinstance(prix, list) and len(prix) == 1:
            if "10-20" in prix:
                name_parts.append("Bon marché")
            elif "50-100" in prix or "100+" in prix:
                name_parts.append("Gastronomique")
        elif isinstance(prix, str):
            if "10-20" == prix:
                name_parts.append("Bon marché")
            elif "50-100" == prix or "100+" == prix:
                name_parts.append("Gastronomique")
    
    if "ambiance" in filter_conditions:
        ambiance = filter_conditions["ambiance"]
        if isinstance(ambiance, list) and len(ambiance) == 1:
            name_parts.append(f"{ambiance[0]}")
        elif isinstance(ambiance, str):
            name_parts.append(f"{ambiance}")
    
    if "arrondissement" in filter_conditions:
        arr = filter_conditions["arrondissement"]
        if isinstance(arr, list) and len(arr) == 1:
            name_parts.append(f"dans le {arr[0]}")
        elif isinstance(arr, str):
            name_parts.append(f"dans le {arr}")
            
    if "qualite_nourriture" in filter_conditions:
        qualite = filter_conditions["qualite_nourriture"]
        if isinstance(qualite, list) and len(qualite) == 1:
            name_parts.append(f"{qualite[0]}")
        elif isinstance(qualite, str):
            name_parts.append(f"{qualite}")
    
    # Si nous avons des parties de nom, les assembler
    if name_parts:
        return " ".join(name_parts)
    else:
        # Nom par défaut
        return f"Mes préférences ({len(filter_conditions)} critères)"

# Fonction pour extraire les avis les plus pertinents
def get_relevant_reviews(reviews, n=3):
    """
    Sélectionne les n avis les plus pertinents d'un restaurant.
    
    Args:
        reviews (list): Liste des avis du restaurant.
        n (int): Nombre d'avis à sélectionner.
        
    Returns:
        list: Les n avis les plus pertinents.
    """
    if not reviews or not isinstance(reviews, list):
        return []
        
    # Trier par note (privilégier les avis extrêmes, très positifs ou très négatifs)
    # puis les plus récents
    relevant = sorted(reviews, key=lambda x: (abs(x.get('note', 3) - 3), x.get('date', '')), reverse=True)
    
    return relevant[:n]

# Fonction d'interface chatbot pour la recherche
def chatbot_interface(df):
    """
    Interface de chat pour rechercher des restaurants de façon conversationnelle.
    
    Args:
        df (DataFrame): Le dataset des restaurants.
        
    Returns:
        dict: Les filtres détectés dans la conversation.
    """
    st.subheader("💬 Discutez avec FROODIES")
    
    # Initialiser l'historique du chat s'il n'existe pas
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Bonjour ! Je suis FROODIES, votre assistant pour trouver le restaurant parfait à Paris. Que recherchez-vous aujourd'hui ?"}
        ]
    
    # Afficher l'historique du chat
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            st.chat_message("assistant").write(message["content"])
    
    # Champ de saisie pour le chat
    user_input = st.chat_input("Que recherchez-vous comme restaurant ?")
    
    if user_input:
        # Ajouter le message de l'utilisateur à l'historique
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Afficher le message de l'utilisateur
        st.chat_message("user").write(user_input)
        
        # Simuler une analyse de la requête
        # Dans une vraie implémentation, cela utiliserait NLP ou une IA
        filters = {}
        
        # Mots-clés à rechercher
        cuisine_keywords = {
            "français": "Français", "italien": "Italien", "japonais": "Japonais", 
            "chinois": "Chinois", "indien": "Indien", "libanais": "Libanais",
            "marocain": "Marocain", "espagnol": "Espagnol", "américain": "Américain",
            "mexicain": "Mexicain", "thaï": "Thaïlandais", "vietnamien": "Vietnamien",
            "coréen": "Coréen", "grec": "Grecque", "méditerranéen": "Méditerranéen"
        }
        
        type_keywords = {
            "végétarien": "Végétarien", "végan": "Végan", "vegan": "Végan",
            "burger": "Burger", "pizza": "Pizza", "fruits de mer": "Fruits de mer",
            "crêpe": "Crêperie", "bistrot": "Bistrot", "brasserie": "Brasserie",
            "gastro": "Gastronomique", "street food": "Street food", "tapas": "Tapas",
            "ramen": "Ramen", "sushi": "Sushi"
        }
        
        prix_keywords = {
            "pas cher": "10-20", "abordable": "20-30", "économique": "10-20",
            "moyen": "20-30", "intermédiaire": "30-50",
            "luxe": "50-100", "gastronomique": "50-100", "haut de gamme": "50-100",
            "cher": "50-100", "très cher": "100+"
        }
        
        arrond_keywords = {
            "centre": "75001", "louvre": "75001", "opéra": "75002", "bourse": "75002",
            "marais": "75004", "quartier latin": "75005", "saint-germain": "75006",
            "invalides": "75007", "tour eiffel": "75007", "champs-élysées": "75008",
            "pigalle": "75009", "canal": "75010", "bastille": "75011", "bercy": "75012",
            "montparnasse": "75014", "vaugirard": "75015", "passy": "75016", 
            "batignolles": "75017", "montmartre": "75018", "buttes-chaumont": "75019", 
            "belleville": "75020"
        }
        
        ambiance_keywords = {
            "romantique": "Romantique", "familial": "Familial", "famille": "Familial",
            "branché": "Branché", "cosy": "Cosy", "élégant": "Élégant",
            "décontracté": "Décontracté", "calme": "Calme", "animé": "Animé",
            "festif": "Festif", "intime": "Intime", "terrasse": "Terrasse",
            "vue": "Vue panoramique", "traditionnel": "Traditionnel"
        }
        
        qualite_keywords = {
            "fait maison": "Fait maison", "bio": "Bio", "local": "Produits locaux",
            "saison": "Produits de saison", "fermier": "Produits fermiers",
            "circuit court": "Circuit court", "artisanal": "Fait maison"
        }
        
        reconnaissance_keywords = {
            "étoile": "Guide Michelin", "michelin": "Guide Michelin", 
            "gault": "Gault & Millau", "millau": "Gault & Millau",
            "récompense": None, "distinction": None, "reconnu": None
        }
        
        jours_keywords = {
            "lundi": "Lundi", "mardi": "Mardi", "mercredi": "Mercredi",
            "jeudi": "Jeudi", "vendredi": "Vendredi", "samedi": "Samedi",
            "dimanche": "Dimanche", "week-end": ["Samedi", "Dimanche"],
            "weekend": ["Samedi", "Dimanche"], "semaine": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"],
            "aujourd'hui": datetime.now().strftime("%A")
        }
        
        user_input_lower = user_input.lower()
        
        # Détection de type de cuisine
        for keyword, value in cuisine_keywords.items():
            if keyword in user_input_lower:
                if "type_cuisine" not in filters:
                    filters["type_cuisine"] = []
                filters["type_cuisine"].append(value)
        
        # Détection de type spécifique
        for keyword, value in type_keywords.items():
            if keyword in user_input_lower:
                if "specialite" not in filters:
                    filters["specialite"] = []
                filters["specialite"].append(value)
        
        # Détection de prix
        for keyword, value in prix_keywords.items():
            if keyword in user_input_lower:
                if "prix_fourchette" not in filters:
                    filters["prix_fourchette"] = []
                if isinstance(value, list):
                    filters["prix_fourchette"].extend(value)
                else:
                    filters["prix_fourchette"].append(value)
        
        # Détection d'arrondissement
        for keyword, value in arrond_keywords.items():
            if keyword in user_input_lower:
                if "arrondissement" not in filters:
                    filters["arrondissement"] = []
                if isinstance(value, list):
                    filters["arrondissement"].extend(value)
                else:
                    filters["arrondissement"].append(value)
        
        # Détection d'ambiance
        for keyword, value in ambiance_keywords.items():
            if keyword in user_input_lower:
                if "ambiance" not in filters:
                    filters["ambiance"] = []
                if isinstance(value, list):
                    filters["ambiance"].extend(value)
                else:
                    filters["ambiance"].append(value)

        # Détection de qualité
        for keyword, value in qualite_keywords.items():
            if keyword in user_input_lower:
                if "qualite_nourriture" not in filters:
                    filters["qualite_nourriture"] = []
                if isinstance(value, list):
                    filters["qualite_nourriture"].extend(value)
                else:
                    filters["qualite_nourriture"].append(value)
        
        # Détection de reconnaissance
        for keyword, value in reconnaissance_keywords.items():
            if keyword in user_input_lower:
                if "reconnaissances" not in filters:
                    filters["reconnaissances"] = True  # Flag pour filtrer sur la présence de reconnaissances
                    
        # Détection de jours d'ouverture
        for keyword, value in jours_keywords.items():
            if keyword in user_input_lower:
                if "jours_ouverture" not in filters:
                    filters["jours_ouverture"] = []
                if isinstance(value, list):
                    filters["jours_ouverture"].extend(value)
                else:
                    filters["jours_ouverture"].append(value)
        
        # Réponse du chatbot
        if filters:
            response = "D'après ce que je comprends, vous cherchez "
            parts = []
            
            if "type_cuisine" in filters:
                parts.append(f"un restaurant {', '.join(filters['type_cuisine'])}")
            
            if "specialite" in filters:
                parts.append(f"spécialisé en {', '.join(filters['specialite'])}")
            
            if "prix_fourchette" in filters:
                prix_labels = []
                for prix in filters["prix_fourchette"]:
                    if prix == "10-20":
                        prix_labels.append("bon marché")
                    elif prix == "20-30":
                        prix_labels.append("prix moyen")
                    elif prix == "30-50":
                        prix_labels.append("assez haut de gamme")
                    elif prix in ["50-100", "100+"]:
                        prix_labels.append("haut de gamme")
                parts.append(f"avec des prix {', '.join(prix_labels)}")
            
            if "arrondissement" in filters:
                parts.append(f"dans le(s) {', '.join(filters['arrondissement'])}")
            
            if "ambiance" in filters:
                parts.append(f"avec une ambiance {', '.join(filters['ambiance'])}")
                
            if "qualite_nourriture" in filters:
                parts.append(f"proposant {', '.join(filters['qualite_nourriture'])}")
                
            if "reconnaissances" in filters:
                parts.append("avec des distinctions ou récompenses gastronomiques")
                
            if "jours_ouverture" in filters:
                parts.append(f"ouvert le(s) {', '.join(filters['jours_ouverture'])}")
            
            if parts:
                response += " " + ", ".join(parts) + "."
                
                # Ajouter suggestion de filtrer
                response += "\n\nJe peux vous montrer des restaurants correspondant à ces critères. Souhaitez-vous affiner votre recherche ou voir les résultats maintenant ?"
                
                # Stocker les filtres dans la session
                st.session_state.chat_filters = filters
                
                # Ajouter la recherche à l'historique
                save_search(filters)
            else:
                response = "Je n'ai pas bien compris vos critères. Pourriez-vous préciser si vous cherchez un type de cuisine spécifique, dans un quartier particulier, ou avec un budget défini ?"
        else:
            response = "Je n'ai pas bien compris vos critères. Pourriez-vous préciser si vous cherchez un type de cuisine spécifique, dans un quartier particulier, ou avec un budget défini ?"
        
        # Ajouter la réponse à l'historique et l'afficher
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)
        
        # Ajout de boutons pour voir les résultats ou continuer la conversation
        if filters:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 Voir les résultats"):
                    st.session_state.show_results = True
                    st.rerun()
            with col2:
                if st.button("✏️ Affiner ma recherche"):
                    # Continuer la conversation pour affiner
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": "Comment puis-je affiner votre recherche ? Vous pouvez préciser le budget, l'ambiance, ou d'autres détails."
                    })
                    st.rerun()
                    
        return filters
    
    return None

def main():
    """
    Fonction principale de l'application.
    Gère l'interface utilisateur et la logique d'application.
    """
    # Initialisation de l'état de session
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    
    if 'chat_filters' not in st.session_state:
        st.session_state.chat_filters = {}
    
    # Chargement des données
    df = load_data()
    user_data = load_user_data()
    
    # En-tête principal
    st.title("🍕 FROODIES")
    st.markdown("### Trouvez votre restaurant idéal à Paris !")
    
    # SIDEBAR: Filtres
    st.sidebar.title("🔍 Filtres de recherche")
    
    # Onglets dans la sidebar pour différents types de filtres
    sidebar_tab1, sidebar_tab2 = st.sidebar.tabs(["🔎 Filtres standards", "🌟 Filtres personnalisés"])
    
    # Filtres standards
    with sidebar_tab1:
        # Filtres standards
        price_filter = st.multiselect(
            "Budget",
            options=sorted(df['prix_fourchette'].unique()),
            default=[]
        )
        
        cuisine_filter = st.multiselect(
            "Type de cuisine",
            options=sorted(df['type_cuisine'].unique()),
            default=[]
        )
        
        specialite_filter = st.multiselect(
            "Spécialité",
            options=sorted([s for s in df['specialite'].unique() if pd.notna(s) and s != '']),
            default=[]
        )
        
        arrond_filter = st.multiselect(
            "Arrondissement",
            options=sorted(df['arrondissement'].unique()),
            default=[]
        )
        
        ambiance_filter = st.multiselect(
            "Ambiance",
            options=sorted(df['ambiance'].unique()),
            default=[]
        )
        
        # Nouveaux filtres
        qualite_options = []
        for qual_list in df['qualite_nourriture']:
            if isinstance(qual_list, list):
                qualite_options.extend(qual_list)
        qualite_options = sorted(list(set(qualite_options)))
        
        qualite_filter = st.multiselect(
            "Qualité de la nourriture",
            options=qualite_options,
            default=[]
        )
        
        # Filtre sur les jours d'ouverture
        jours_filter = st.multiselect(
            "Jours d'ouverture",
            options=["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
            default=[]
        )
        
        # Filtre sur les reconnaissances
        has_recognition = st.checkbox("Restaurants récompensés uniquement")
        
        note_min = st.slider(
            "Note minimum",
            min_value=float(df['note_moyenne'].min()),
            max_value=float(df['note_moyenne'].max()),
            value=4.0,
            step=0.1
        )
        
        # Séparateur
        st.sidebar.divider()
        
        # Affichage des filtres les plus utilisés
        st.sidebar.subheader("💡 Vos filtres fréquents")
        most_used_filters = get_most_used_filters()
        
        if most_used_filters:
            for filter_name, filter_data in most_used_filters[:3]:  # Top 3
                with st.sidebar.expander(f"{filter_name} ({filter_data['count']} utilisations)"):
                    # Afficher les valeurs les plus utilisées
                    top_values = sorted(filter_data["values"].items(), key=lambda x: x[1], reverse=True)[:3]
                    for value, count in top_values:
                        st.write(f"- {value}: {count} fois")
                        if st.button(f"Appliquer '{value}'", key=f"apply_{filter_name}_{value}"):
                            # Appliquer ce filtre
                            if filter_name == "prix_fourchette":
                                price_filter = [value]
                            elif filter_name == "type_cuisine":
                                cuisine_filter = [value]
                            elif filter_name == "specialite":
                                specialite_filter = [value]
                            elif filter_name == "arrondissement":
                                arrond_filter = [value]
                            elif filter_name == "ambiance":
                                ambiance_filter = [value]
                            elif filter_name == "qualite_nourriture":
                                qualite_filter = [value]
                            st.rerun()
        else:
            st.sidebar.info("Utilisez les filtres pour voir vos préférences fréquentes ici.")
    
    # Filtres personnalisés
    with sidebar_tab2:
        # Interface pour créer un nouveau filtre personnalisé
        st.sidebar.subheader("Créer un filtre personnalisé")
        
        filter_name = st.sidebar.text_input("Nom du filtre")
        
        st.sidebar.write("Sélectionnez les conditions:")
        save_price = st.sidebar.checkbox("Budget")
        save_cuisine = st.sidebar.checkbox("Type de cuisine")
        save_specialite = st.sidebar.checkbox("Spécialité")
        save_arrond = st.sidebar.checkbox("Arrondissement")
        save_ambiance = st.sidebar.checkbox("Ambiance")
        save_qualite = st.sidebar.checkbox("Qualité")
        save_jours = st.sidebar.checkbox("Jours d'ouverture")
        save_recognition = st.sidebar.checkbox("Récompenses")
        save_note = st.sidebar.checkbox("Note minimale")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Annuler"):
                st.sidebar.success("Création annulée")
        
        with col2:
            if st.button("Enregistrer"):
                # Vérifier que le nom n'est pas vide
                if not filter_name:
                    st.sidebar.error("Le nom du filtre ne peut pas être vide")
                else:
                    # Créer le filtre personnalisé
                    conditions = {}
                    
                    if save_price and price_filter:
                        conditions["prix_fourchette"] = price_filter
                    
                    if save_cuisine and cuisine_filter:
                        conditions["type_cuisine"] = cuisine_filter
                        
                    if save_specialite and specialite_filter:
                        conditions["specialite"] = specialite_filter
                    
                    if save_arrond and arrond_filter:
                        conditions["arrondissement"] = arrond_filter
                    
                    if save_ambiance and ambiance_filter:
                        conditions["ambiance"] = ambiance_filter
                        
                    if save_qualite and qualite_filter:
                        conditions["qualite_nourriture"] = qualite_filter
                        
                    if save_jours and jours_filter:
                        conditions["jours_ouverture"] = jours_filter
                        
                    if save_recognition and has_recognition:
                        conditions["reconnaissances"] = True
                    
                    if save_note:
                        conditions["note_moyenne"] = note_min
                    
                    # Si des conditions ont été sélectionnées
                    if conditions:
                        user_data["custom_filters"].append({
                            "id": len(user_data["custom_filters"]) + 1,
                            "name": filter_name,
                            "conditions": conditions
                        })
                        save_user_data(user_data)
                        st.sidebar.success(f"Filtre '{filter_name}' créé avec succès!")
                    else:
                        st.sidebar.error("Veuillez sélectionner au moins une condition")
        
        # Séparateur
        st.sidebar.divider()
        
        # Affichage des filtres personnalisés existants
        st.sidebar.subheader("Vos filtres personnalisés")
        
        if user_data["custom_filters"]:
            for custom_filter in user_data["custom_filters"]:
                with st.sidebar.expander(f"🔖 {custom_filter['name']}"):
                    # Afficher les conditions du filtre
                    for condition_name, condition_value in custom_filter["conditions"].items():
                        if isinstance(condition_value, list):
                            st.write(f"- {condition_name}: {', '.join(condition_value)}")
                        else:
                            st.write(f"- {condition_name}: {condition_value}")
                    
                    # Bouton pour appliquer ce filtre
                    if st.button(f"Appliquer", key=f"apply_custom_{custom_filter['id']}"):
                        # Appliquer les conditions de ce filtre
                        if "prix_fourchette" in custom_filter["conditions"]:
                            price_filter = custom_filter["conditions"]["prix_fourchette"] if isinstance(custom_filter["conditions"]["prix_fourchette"], list) else [custom_filter["conditions"]["prix_fourchette"]]
                        
                        if "type_cuisine" in custom_filter["conditions"]:
                            cuisine_filter = custom_filter["conditions"]["type_cuisine"] if isinstance(custom_filter["conditions"]["type_cuisine"], list) else [custom_filter["conditions"]["type_cuisine"]]
                            
                        if "specialite" in custom_filter["conditions"]:
                            specialite_filter = custom_filter["conditions"]["specialite"] if isinstance(custom_filter["conditions"]["specialite"], list) else [custom_filter["conditions"]["specialite"]]
                        
                        if "arrondissement" in custom_filter["conditions"]:
                            arrond_filter = custom_filter["conditions"]["arrondissement"] if isinstance(custom_filter["conditions"]["arrondissement"], list) else [custom_filter["conditions"]["arrondissement"]]
                        
                        if "ambiance" in custom_filter["conditions"]:
                            ambiance_filter = custom_filter["conditions"]["ambiance"] if isinstance(custom_filter["conditions"]["ambiance"], list) else [custom_filter["conditions"]["ambiance"]]
                            
                        if "qualite_nourriture" in custom_filter["conditions"]:
                            qualite_filter = custom_filter["conditions"]["qualite_nourriture"] if isinstance(custom_filter["conditions"]["qualite_nourriture"], list) else [custom_filter["conditions"]["qualite_nourriture"]]
                            
                        if "jours_ouverture" in custom_filter["conditions"]:
                            jours_filter = custom_filter["conditions"]["jours_ouverture"] if isinstance(custom_filter["conditions"]["jours_ouverture"], list) else [custom_filter["conditions"]["jours_ouverture"]]
                            
                        if "reconnaissances" in custom_filter["conditions"]:
                            has_recognition = True
                        
                        if "note_moyenne" in custom_filter["conditions"]:
                            note_min = float(custom_filter["conditions"]["note_moyenne"])
                        
                        st.rerun()
                    
                    # Bouton pour supprimer ce filtre
                    if st.button(f"Supprimer", key=f"delete_custom_{custom_filter['id']}"):
                        user_data["custom_filters"] = [f for f in user_data["custom_filters"] if f["id"] != custom_filter["id"]]
                        save_user_data(user_data)
                        st.success(f"Filtre '{custom_filter['name']}' supprimé.")
                        st.rerun()
        else:
            st.sidebar.info("Vous n'avez pas encore de filtres personnalisés. Créez-en un en haut de cette section.")
    
    # Filtrage des données
    mask = df['note_moyenne'] >= note_min
    
    if price_filter:
        mask &= df['prix_fourchette'].isin(price_filter)
    if cuisine_filter:
        mask &= df['type_cuisine'].isin(cuisine_filter)
    if specialite_filter:
        mask &= df['specialite'].isin(specialite_filter)
    if arrond_filter:
        mask &= df['arrondissement'].isin(arrond_filter)
    if ambiance_filter:
        mask &= df['ambiance'].isin(ambiance_filter)
        
    # Filtrage sur les nouvelles colonnes
    if qualite_filter:
        # Filtrer les restaurants dont la liste de qualité contient au moins un des éléments recherchés
        mask &= df['qualite_nourriture'].apply(lambda x: isinstance(x, list) and any(q in x for q in qualite_filter))
        
    if jours_filter:
        # Filtrer les restaurants ouverts les jours demandés
        mask &= df['jours_ouverture'].apply(lambda x: isinstance(x, list) and all(jour in x for jour in jours_filter))
        
    if has_recognition:
        # Filtrer pour ne garder que les restaurants avec des reconnaissances
        mask &= df['reconnaissances'].apply(lambda x: isinstance(x, list) and len(x) > 0)
    
    df_filtered = df[mask]
    
    # Enregistrer cette recherche dans l'historique utilisateur
    current_filters = {}
    if price_filter:
        current_filters["prix_fourchette"] = price_filter
    if cuisine_filter:
        current_filters["type_cuisine"] = cuisine_filter
    if specialite_filter:
        current_filters["specialite"] = specialite_filter
    if arrond_filter:
        current_filters["arrondissement"] = arrond_filter
    if ambiance_filter:
        current_filters["ambiance"] = ambiance_filter
    if qualite_filter:
        current_filters["qualite_nourriture"] = qualite_filter
    if jours_filter:
        current_filters["jours_ouverture"] = jours_filter
    if has_recognition:
        current_filters["reconnaissances"] = True
    if note_min > 4.0:  # Seulement si modifié par rapport à la valeur par défaut
        current_filters["note_moyenne"] = note_min
    
    if current_filters:
        save_search(current_filters)
    
    # Interface principale
    # Interface chatbot
    filters_from_chat = chatbot_interface(df)
    
    if filters_from_chat:
        # Mise à jour des filtres selon l'entrée du chatbot
        st.session_state.chat_filters = filters_from_chat
    
    # Vérifier si des filtres manuels sont activés (à partir de la sidebar)
    has_manual_filters = any([price_filter, cuisine_filter, specialite_filter, arrond_filter, ambiance_filter, 
                             qualite_filter, jours_filter, has_recognition]) or note_min > 4.0
    
    # Si des filtres sont appliqués via le chatbot OU des filtres manuels
    if (st.session_state.chat_filters and st.session_state.show_results) or has_manual_filters:
        # Déterminer quelle source de filtres utiliser
        if has_manual_filters:
            # Utiliser les filtres de la sidebar
            filtered_data = df_filtered
            filter_source = "sidebar"
        else:
            # Utiliser les filtres du chatbot
            chat_mask = df['note_moyenne'] >= note_min  # Conserver le filtre de note minimal
            
            if "prix_fourchette" in st.session_state.chat_filters:
                chat_mask &= df['prix_fourchette'].isin(st.session_state.chat_filters["prix_fourchette"])
            
            if "type_cuisine" in st.session_state.chat_filters:
                chat_mask &= df['type_cuisine'].isin(st.session_state.chat_filters["type_cuisine"])
            
            if "specialite" in st.session_state.chat_filters:
                chat_mask &= df['specialite'].isin(st.session_state.chat_filters["specialite"])
            
            if "arrondissement" in st.session_state.chat_filters:
                chat_mask &= df['arrondissement'].isin(st.session_state.chat_filters["arrondissement"])
            
            if "ambiance" in st.session_state.chat_filters:
                chat_mask &= df['ambiance'].isin(st.session_state.chat_filters["ambiance"])
                
            if "qualite_nourriture" in st.session_state.chat_filters:
                chat_mask &= df['qualite_nourriture'].apply(lambda x: isinstance(x, list) and 
                                                          any(q in x for q in st.session_state.chat_filters["qualite_nourriture"]))
                
            if "jours_ouverture" in st.session_state.chat_filters:
                chat_mask &= df['jours_ouverture'].apply(lambda x: isinstance(x, list) and 
                                                      all(jour in x for jour in st.session_state.chat_filters["jours_ouverture"]))
                
            if "reconnaissances" in st.session_state.chat_filters:
                chat_mask &= df['reconnaissances'].apply(lambda x: isinstance(x, list) and len(x) > 0)
            
            filtered_data = df[chat_mask]
            filter_source = "chatbot"
        
        # Afficher les résultats
        st.subheader("🔍 Résultats de votre recherche")
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Restaurants trouvés", len(filtered_data))
        with col2:
            st.metric("Note moyenne", f"{filtered_data['note_moyenne'].mean():.1f}/5" if not filtered_data.empty else "N/A")
        with col3:
            st.metric("Prix moyen", filtered_data['prix_fourchette'].mode()[0] if not filtered_data.empty else "N/A")
        with col4:
            st.metric("Cuisines différentes", filtered_data['type_cuisine'].nunique() if not filtered_data.empty else "N/A")
        
        # Onglets pour différentes vues
        tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Carte", "📊 Statistiques", "📋 Liste", "⭐ Distinctions"])
        
        # Onglet Carte
        with tab1:
            if not filtered_data.empty:
                map_fig = create_restaurant_map(filtered_data)
                folium_static(map_fig, width=1000, height=600)
            else:
                st.warning("Aucun restaurant ne correspond à vos critères")
        
        # Onglet Statistiques
        with tab2:
            if not filtered_data.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Distribution des types de cuisine
                    counts_cuisine = filtered_data['type_cuisine'].value_counts().reset_index()
                    counts_cuisine.columns = ['type_cuisine', 'count']  # Renommer explicitement les colonnes
                    
                    fig_cuisine = px.pie(
                        counts_cuisine,
                        values='count',
                        names='type_cuisine',
                        title='Répartition des types de cuisine'
                    )
                    st.plotly_chart(fig_cuisine)
                
                with col2:
                    # Distribution des prix
                    counts_prix = filtered_data['prix_fourchette'].value_counts().reset_index()
                    counts_prix.columns = ['prix_fourchette', 'count']
                    
                    fig_prix = px.bar(
                        counts_prix,
                        x='prix_fourchette',
                        y='count',
                        title='Distribution des fourchettes de prix'
                    )
                    st.plotly_chart(fig_prix)
                    
                # Nouvelle statistique: qualité de la nourriture
                qualite_counts = {}
                for idx, row in filtered_data.iterrows():
                    if isinstance(row['qualite_nourriture'], list):
                        for q in row['qualite_nourriture']:
                            if q not in qualite_counts:
                                qualite_counts[q] = 0
                            qualite_counts[q] += 1
                
                if qualite_counts:
                    # Convertir en DataFrame pour plotly
                    qualite_df = pd.DataFrame({
                        'qualite': list(qualite_counts.keys()),
                        'count': list(qualite_counts.values())
                    })
                    qualite_df = qualite_df.sort_values('count', ascending=False)
                    
                    fig_qualite = px.bar(
                        qualite_df,
                        x='qualite',
                        y='count',
                        title='Caractéristiques de qualité les plus présentes'
                    )
                    st.plotly_chart(fig_qualite)
                    
                # Notes moyennes par type de cuisine
                fig_notes = px.box(
                    filtered_data,
                    x='type_cuisine',
                    y='note_moyenne',
                    title='Distribution des notes par type de cuisine'
                )
                st.plotly_chart(fig_notes)
            else:
                st.warning("Aucun restaurant ne correspond à vos critères")
        
        # Onglet Liste
        with tab3:
            if not filtered_data.empty:
                for idx, resto in filtered_data.iterrows():
                    with st.expander(f"🍽️ {resto['nom']} - {resto['type_cuisine']} ({resto['prix_fourchette']})"):
                        cols = st.columns([2, 1])
                        
                        with cols[0]:
                            st.markdown(f"**Adresse:** {resto['adresse']}")
                            
                            if 'specialite' in resto and pd.notna(resto['specialite']) and resto['specialite'] != '':
                                st.markdown(f"**Spécialité:** {resto['specialite']}")
                                
                            st.markdown(f"**Ambiance:** {resto['ambiance']}")
                            
                            # Afficher les jours d'ouverture
                            jours_ouv = "Non disponible"
                            if isinstance(resto.get('jours_ouverture'), list):
                                jours_ouv = ", ".join(resto['jours_ouverture'])
                            st.markdown(f"**Jours d'ouverture:** {jours_ouv}")
                            
                            # Qualité de la nourriture
                            if isinstance(resto.get('qualite_nourriture'), list) and resto['qualite_nourriture']:
                                st.markdown(f"**Qualité:** {', '.join(resto['qualite_nourriture'])}")
                                
                            # Reconnaissances/distinctions 
                            if isinstance(resto.get('reconnaissances'), list) and resto['reconnaissances']:
                                st.markdown("**Distinctions:**")
                                for reco in resto['reconnaissances']:
                                    st.markdown(f"- {reco['guide']} {reco['annee']} - {reco['distinction']}")
                            
                            # Afficher quelques avis représentatifs
                            if isinstance(resto.get('avis'), list) and resto['avis']:
                                with st.expander("Voir les avis clients"):
                                    relevant_reviews = get_relevant_reviews(resto['avis'], 3)
                                    for review in relevant_reviews:
                                        st.markdown(f"**{review['note']}/5** - {review['auteur']} - {review['date']}")
                                        st.markdown(f"_{review['commentaire']}_")
                                        st.divider()
                            
                        with cols[1]:
                            st.metric("Note", f"{resto['note_moyenne']}/5")
                            st.metric("Nombre d'avis", resto['nb_avis'])
                            
                            # Horaires d'aujourd'hui
                            today = datetime.now().strftime("%A")
                            today_fr = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", 
                                      "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", 
                                      "Sunday": "Dimanche"}[today]
                            
                            horaires_auj = "Non disponible"
                            if isinstance(resto.get('horaires_ouverture'), dict) and today_fr in resto['horaires_ouverture']:
                                horaires_auj = ", ".join(resto['horaires_ouverture'][today_fr])
                            
                            st.metric("Horaires aujourd'hui", horaires_auj)
                            
                            # Bouton pour ajouter aux favoris
                            if resto['nom'] in st.session_state.favorites:
                                if st.button("❤️ Retirer des favoris", key=f"unfav_{idx}"):
                                    st.session_state.favorites.remove(resto['nom'])
                                    # Mettre à jour les favoris dans les données utilisateur
                                    user_data["favorite_restaurants"] = st.session_state.favorites
                                    save_user_data(user_data)
                                    st.rerun()
                            else:
                                if st.button("🤍 Ajouter aux favoris", key=f"fav_{idx}"):
                                    st.session_state.favorites.append(resto['nom'])
                                    # Mettre à jour les favoris dans les données utilisateur
                                    user_data["favorite_restaurants"] = st.session_state.favorites
                                    save_user_data(user_data)
                                    st.rerun()
            else:
                st.warning("Aucun restaurant ne correspond à vos critères")
        
        # Onglet Distinctions (nouveau)
        with tab4:
            if not filtered_data.empty:
                # Filtrer les restaurants qui ont des distinctions
                restaurants_avec_distinctions = filtered_data[filtered_data['reconnaissances'].apply(
                    lambda x: isinstance(x, list) and len(x) > 0)]
                
                if not restaurants_avec_distinctions.empty:
                    st.subheader(f"Restaurants récompensés ({len(restaurants_avec_distinctions)})")
                    
                    # Compter les distinctions par guide
                    guides_count = {}
                    for idx, resto in restaurants_avec_distinctions.iterrows():
                        for reco in resto['reconnaissances']:
                            guide = reco['guide']
                            if guide not in guides_count:
                                guides_count[guide] = 0
                            guides_count[guide] += 1
                    
                    # Afficher un graphique des guides
                    if guides_count:
                        guide_df = pd.DataFrame({
                            'guide': list(guides_count.keys()),
                            'count': list(guides_count.values())
                        }).sort_values('count', ascending=False)
                        
                        fig_guides = px.bar(
                            guide_df,
                            x='guide',
                            y='count',
                            title='Répartition des distinctions par guide gastronomique'
                        )
                        st.plotly_chart(fig_guides)
                    
                    # Afficher les restaurants par guide
                    guides_uniques = set()
                    for idx, resto in restaurants_avec_distinctions.iterrows():
                        for reco in resto['reconnaissances']:
                            guides_uniques.add(reco['guide'])
                    
                    guide_tabs = st.tabs(list(guides_uniques))
                    
                    for i, guide in enumerate(guides_uniques):
                        with guide_tabs[i]:
                            # Filtrer les restaurants ayant des distinctions de ce guide
                            restos_du_guide = []
                            for idx, resto in restaurants_avec_distinctions.iterrows():
                                for reco in resto['reconnaissances']:
                                    if reco['guide'] == guide:
                                        restos_du_guide.append({
                                            "id": resto['id'],
                                            "nom": resto['nom'],
                                            "distinction": reco['distinction'],
                                            "annee": reco['annee'],
                                            "type_cuisine": resto['type_cuisine'],
                                            "adresse": resto['adresse'],
                                            "note_moyenne": resto['note_moyenne']
                                        })
                            
                            # Afficher les restaurants de ce guide
                            if restos_du_guide:
                                for resto in restos_du_guide:
                                    with st.expander(f"{resto['nom']} - {resto['distinction']} ({resto['annee']})"):
                                        st.markdown(f"**Type de cuisine :** {resto['type_cuisine']}")
                                        st.markdown(f"**Adresse :** {resto['adresse']}")
                                        st.markdown(f"**Note :** {resto['note_moyenne']}/5")
                                        
                                        if st.button("Voir détails", key=f"guide_resto_{guide}_{resto['id']}"):
                                            st.session_state.selected_restaurant = resto['id']
                                            user_data = track_restaurant_view(resto['id'], resto['nom'], user_data)
                                            save_user_data(user_data)
                                            st.rerun()
                else:
                    st.info("Aucun restaurant avec des distinctions ne correspond à vos critères.")
    else:
        # Section Recommandations (visible uniquement si pas de filtres actifs)
        st.divider()
        st.subheader("✨ Recommandations pour vous")
    
    # Génération de recommandations
    if st.session_state.favorites:
        # Recommandations basées sur les favoris
        st.markdown("### Basé sur vos favoris")
        
        # Récupérer les IDs des restaurants favoris
        favorite_restaurants = df[df['nom'].isin(st.session_state.favorites)]
        
        if not favorite_restaurants.empty:
            favorite_id = favorite_restaurants.iloc[0]['id']  # Prendre le premier favori
            recommendations = content_based_recommendations(df, restaurant_id=favorite_id, top_n=3)
            
            if not recommendations.empty:
                cols = st.columns(3)
                for i, (idx, resto) in enumerate(recommendations.iterrows()):
                    with cols[i]:
                        st.markdown(f"**{resto['nom']}**")
                        st.markdown(f"_{resto['type_cuisine']} • {resto['prix_fourchette']}_")
                        st.markdown(f"⭐ {resto['note_moyenne']}/5")
                        
                        # Afficher les reconnaissances s'il y en a
                        if isinstance(resto.get('reconnaissances'), list) and resto['reconnaissances']:
                            for reco in resto['reconnaissances'][:1]:  # Limiter à 1 pour la compacité
                                st.markdown(f"🏆 {reco['guide']} - {reco['distinction']}")
                        
                        st.markdown(f"🏙️ {resto['arrondissement']}")
                        
                        # Bouton pour voir plus de détails
                        if st.button("Voir plus", key=f"fav_rec_{idx}"):
                            st.session_state.selected_restaurant = resto['id']
                            user_data = track_restaurant_view(resto['id'], resto['nom'], user_data)
                            save_user_data(user_data)
                            st.rerun()
    
    # Restaurants populaires (toujours affichés)
    st.markdown("### Les plus populaires à Paris")
    popular_df = df.sort_values(by=['note_moyenne', 'nb_avis'], ascending=False).head(3)
    
    if not popular_df.empty:
        cols = st.columns(3)
        for i, (idx, resto) in enumerate(popular_df.iterrows()):
            with cols[i]:
                st.markdown(f"**{resto['nom']}**")
                st.markdown(f"_{resto['type_cuisine']} • {resto['prix_fourchette']}_")
                st.markdown(f"⭐ {resto['note_moyenne']}/5 ({resto['nb_avis']} avis)")
                
                # Afficher les reconnaissances s'il y en a
                if isinstance(resto.get('reconnaissances'), list) and resto['reconnaissances']:
                    for reco in resto['reconnaissances'][:1]:  # Limiter à 1 pour la compacité
                        st.markdown(f"🏆 {reco['guide']} - {reco['distinction']}")
                
                st.markdown(f"🏙️ {resto['arrondissement']}")
                
                # Bouton pour voir plus de détails
                if st.button("Voir plus", key=f"pop_{idx}"):
                    st.session_state.selected_restaurant = resto['id']
                    user_data = track_restaurant_view(resto['id'], resto['nom'], user_data)
                    save_user_data(user_data)
                    st.rerun()
    
    # Restaurants avec reconnaissances (si pas déjà filtré par reconnaissances)
    if not has_recognition:
        st.markdown("### Restaurants récompensés")
        awarded_df = df[df['reconnaissances'].apply(lambda x: isinstance(x, list) and len(x) > 0)].head(3)
        
        if not awarded_df.empty:
            cols = st.columns(3)
            for i, (idx, resto) in enumerate(awarded_df.iterrows()):
                with cols[i]:
                    st.markdown(f"**{resto['nom']}**")
                    st.markdown(f"_{resto['type_cuisine']} • {resto['prix_fourchette']}_")
                    
                    # Afficher les reconnaissances
                    reconnaissances_text = []
                    for reco in resto['reconnaissances'][:2]:  # Limiter à 2
                        reconnaissances_text.append(f"{reco['guide']} {reco['annee']} - {reco['distinction']}")
                    
                    st.markdown(f"🏆 {' | '.join(reconnaissances_text)}")
                    st.markdown(f"⭐ {resto['note_moyenne']}/5")
                    
                    # Bouton pour voir plus de détails
                    if st.button("Voir plus", key=f"award_{idx}"):
                        st.session_state.selected_restaurant = resto['id']
                        user_data = track_restaurant_view(resto['id'], resto['nom'], user_data)
                        save_user_data(user_data)
                        st.rerun()
    
    # Si un restaurant spécifique est sélectionné
    if 'selected_restaurant' in st.session_state:
        selected_resto = df[df['id'] == st.session_state.selected_restaurant]
        
        if not selected_resto.empty:
            resto = selected_resto.iloc[0]
            
            st.divider()
            st.subheader(f"🍽️ {resto['nom']}")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Type de cuisine:** {resto['type_cuisine']}")
                if pd.notna(resto.get('specialite')) and resto['specialite']:
                    st.markdown(f"**Spécialité:** {resto['specialite']}")
                st.markdown(f"**Adresse:** {resto['adresse']}")
                st.markdown(f"**Arrondissement:** {resto['arrondissement']}")
                st.markdown(f"**Ambiance:** {resto['ambiance']}")
                
                # Afficher la qualité de la nourriture
                if isinstance(resto.get('qualite_nourriture'), list) and resto['qualite_nourriture']:
                    st.markdown(f"**Qualité:** {', '.join(resto['qualite_nourriture'])}")
                
                # Afficher les distinctions/reconnaissances
                if isinstance(resto.get('reconnaissances'), list) and resto['reconnaissances']:
                    st.markdown("**Distinctions:**")
                    for reco in resto['reconnaissances']:
                        st.markdown(f"- {reco['guide']} {reco['annee']} - {reco['distinction']}")
            
            with col2:
                st.metric("Note", f"{resto['note_moyenne']}/5")
                st.metric("Nombre d'avis", resto['nb_avis'])
                st.markdown(f"**Prix:** {resto['prix_fourchette']}")
                
                # Jours d'ouverture
                jours_ouv = "Non disponible"
                if isinstance(resto.get('jours_ouverture'), list):
                    jours_ouv = ", ".join(resto['jours_ouverture'])
                st.markdown(f"**Jours d'ouverture:** {jours_ouv}")
                
                # Horaires aujourd'hui
                today = datetime.now().strftime("%A")
                today_fr = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", 
                          "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", 
                          "Sunday": "Dimanche"}[today]
                
                horaires_auj = "Non disponible"
                if isinstance(resto.get('horaires_ouverture'), dict) and today_fr in resto['horaires_ouverture']:
                    horaires_auj = ", ".join(resto['horaires_ouverture'][today_fr])
                
                st.markdown(f"**Horaires aujourd'hui:** {horaires_auj}")
                
                # Bouton pour ajouter/retirer des favoris
                if resto['nom'] in st.session_state.favorites:
                    if st.button("❤️ Retirer des favoris"):
                        st.session_state.favorites.remove(resto['nom'])
                        user_data["favorite_restaurants"] = st.session_state.favorites
                        save_user_data(user_data)
                        st.rerun()
                else:
                    if st.button("🤍 Ajouter aux favoris"):
                        st.session_state.favorites.append(resto['nom'])
                        user_data["favorite_restaurants"] = st.session_state.favorites
                        save_user_data(user_data)
                        st.rerun()
            
            # Afficher les avis
            if isinstance(resto.get('avis'), list) and resto['avis']:
                st.subheader("💬 Avis des clients")
                best_review = next((r for r in sorted(resto['avis'], key=lambda x: x.get('note', 0), reverse=True)), None)
                worst_review = next((r for r in sorted(resto['avis'], key=lambda x: x.get('note', 5))), None)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if best_review:
                        st.markdown("#### Avis positif")
                        st.markdown(f"**{best_review['note']}/5** - {best_review['auteur']} - {best_review['date']}")
                        st.markdown(f"_{best_review['commentaire']}_")
                
                with col2:
                    if worst_review and worst_review['note'] < 4:  # Seulement si vraiment négatif
                        st.markdown("#### Avis critique")
                        st.markdown(f"**{worst_review['note']}/5** - {worst_review['auteur']} - {worst_review['date']}")
                        st.markdown(f"_{worst_review['commentaire']}_")
                
                # Voir tous les avis
                with st.expander("Voir tous les avis"):
                    for i, avis in enumerate(resto['avis']):
                        st.markdown(f"**{avis['note']}/5** - {avis['auteur']} - {avis['date']}")
                        st.markdown(f"_{avis['commentaire']}_")
                        
                        # Afficher les plats mentionnés s'il y en a
                        if 'plats_mentionnes' in avis and avis['plats_mentionnes']:
                            st.markdown(f"**Plats mentionnés:** {', '.join(avis['plats_mentionnes'])}")
                            
                        if i < len(resto['avis']) - 1:
                            st.divider()
            
            # Mini-carte pour voir l'emplacement du restaurant
            st.subheader("📍 Localisation")
            m = folium.Map(location=[resto['latitude'], resto['longitude']], zoom_start=15)
            
            # Déterminer couleur du marqueur
            marker_color = 'blue'
            if resto['nom'] in st.session_state.favorites:
                marker_color = 'orange'
            elif isinstance(resto.get('reconnaissances'), list) and resto['reconnaissances']:
                marker_color = 'red'
                
            folium.Marker(
                location=[resto['latitude'], resto['longitude']],
                popup=resto['nom'],
                tooltip=resto['nom'],
                icon=folium.Icon(color=marker_color)
            ).add_to(m)
            folium_static(m, width=700, height=300)
            
            # Restaurants similaires
            st.subheader("📋 Restaurants similaires")
            similar_restos = content_based_recommendations(df, restaurant_id=resto['id'], top_n=3)
            
            if not similar_restos.empty:
                cols = st.columns(3)
                for i, (idx, sim_resto) in enumerate(similar_restos.iterrows()):
                    with cols[i]:
                        st.markdown(f"**{sim_resto['nom']}**")
                        st.markdown(f"_{sim_resto['type_cuisine']} • {sim_resto['prix_fourchette']}_")
                        st.markdown(f"⭐ {sim_resto['note_moyenne']}/5")
                        
                        # Afficher les distinctions si présentes
                        if isinstance(sim_resto.get('reconnaissances'), list) and sim_resto['reconnaissances']:
                            for reco in sim_resto['reconnaissances'][:1]:
                                st.markdown(f"🏆 {reco['guide']} - {reco['distinction']}")
                        
                        if st.button("Voir plus", key=f"similar_{idx}"):
                            st.session_state.selected_restaurant = sim_resto['id']
                            user_data = track_restaurant_view(sim_resto['id'], sim_resto['nom'], user_data)
                            save_user_data(user_data)
                            st.rerun()

if __name__ == "__main__":
    # Vérifie si les données utilisateur existent, sinon les initialiser
    if not os.path.exists("user_data.json"):
        default_user_data = {
            "search_history": [],
            "viewed_restaurants": [],
            "favorite_restaurants": [],
            "custom_filters": [
                {
                    "id": 1,
                    "name": "Soirée romantique",
                    "conditions": {
                        "ambiance": ["Romantique", "Intime"],
                        "prix_fourchette": ["30-50"],
                        "note_moyenne": 4.2
                    }
                },
                {
                    "id": 2,
                    "name": "Déjeuner en famille",
                    "conditions": {
                        "ambiance": ["Familial"],
                        "prix_fourchette": ["20-30"],
                        "jours_ouverture": ["Samedi", "Dimanche"]
                    }
                }
            ]
        }
        with open("user_data.json", "w") as f:
            json.dump(default_user_data, f)
    
    main()