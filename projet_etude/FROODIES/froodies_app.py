import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import plotly.express as px
import plotly.graph_objects as go
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
    Charge les données des restaurants depuis le fichier CSV.
    
    Returns:
        DataFrame: Un DataFrame pandas contenant les données des restaurants.
    """
    try:
        # Charger le dataset avec les colonnes enrichies
        df = pd.read_csv("paris_restaurants_enrichi.csv")
        
        # Assurer que toutes les colonnes nécessaires existent
        required_columns = [
            'nom', 'adresse', 'prix_fourchette', 'cuisine_du_monde', 'type_cuisine',
            'ambiance', 'arrondissement', 'note_moyenne', 'nb_avis', 
            'latitude', 'longitude', 'jours_ouverture', 'horaires_ouverture',
            'avis', 'qualite_nourriture', 'reconnaissances',
            # Colonnes pour l'aspect professionnel
            'adapte_repas_affaires', 'niveau_bruit', 'espace_prive', 'type_espace_prive',
            'wifi', 'prise_electrique', 'capacite_groupe', 'equipement_presentation',
            'duree_repas_affaires', 'service_facturation_entreprise', 'reservation_derniere_minute'
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
                # Colonnes professionnelles
                elif col == 'adapte_repas_affaires':
                    df[col] = False
                elif col == 'niveau_bruit':
                    df[col] = "Modéré"
                elif col == 'espace_prive':
                    df[col] = False
                elif col == 'type_espace_prive':
                    df[col] = None
                elif col == 'wifi':
                    df[col] = False
                elif col == 'prise_electrique':
                    df[col] = False
                elif col == 'capacite_groupe':
                    df[col] = 0
                elif col == 'equipement_presentation':
                    df[col] = False
                elif col == 'duree_repas_affaires':
                    df[col] = None
                elif col == 'service_facturation_entreprise':
                    df[col] = False
                elif col == 'reservation_derniere_minute':
                    df[col] = False
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

# Fonction pour charger les données utilisateur
@st.cache_data
def load_user_data():
    """
    Charge les données de l'utilisateur depuis un fichier JSON ou crée un profil par défaut.
    
    Returns:
        dict: Les données utilisateur incluant l'historique, les favoris et les filtres personnalisés.
    """
    # Dans une vraie app, ceci viendrait d'une base de données
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
                },
                {
                    "id": 3,
                    "name": "Repas d'affaires",
                    "conditions": {
                        "adapte_repas_affaires": True,
                        "niveau_bruit": "Calme",
                        "espace_prive": True,
                        "prix_fourchette": ["30-50", "50-100"],
                        "note_moyenne": 4.2
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
        
        # Informations professionnelles
        pro_html = ""
        if st.session_state.mode == "professionnel":
            adapte = "Oui" if row.get('adapte_repas_affaires') else "Non"
            pro_html = f"""
                <p><b>Adapté aux repas d'affaires:</b> {adapte}</p>
                <p><b>Niveau sonore:</b> {row.get('niveau_bruit', 'Non spécifié')}</p>
            """
            
            if row.get('espace_prive'):
                pro_html += f"<p><b>Espace privé:</b> {row.get('type_espace_prive', 'Disponible')}</p>"
                
            if row.get('capacite_groupe', 0) > 0:
                pro_html += f"<p><b>Capacité de groupe:</b> jusqu'à {row.get('capacite_groupe')} personnes</p>"
                
            if row.get('duree_repas_affaires'):
                pro_html += f"<p><b>Durée typique:</b> {row.get('duree_repas_affaires')}</p>"
        
        html = f"""
            <div style='width: 250px'>
                <h4>{row['nom']}</h4>
                <p><b>Cuisine:</b> {row['cuisine_du_monde']}, {row['type_cuisine']}</p>
                <p><b>Prix:</b> {row['prix_fourchette']}</p>
                <p><b>Note:</b> {row['note_moyenne']}/5 ({row['nb_avis']} avis)</p>
                <p><b>Adresse:</b> {row['adresse']}</p>
                <p><b>Aujourd'hui:</b> {horaires_auj}</p>
                {qualite_html}
                {reconnaissances_html}
                {pro_html}
            </div>
        """
        
        # Déterminer la couleur du marqueur
        # Rouge pour les restaurants avec reconnaissance, favoris en or, autres en bleu
        marker_color = 'blue'
        if row['nom'] in st.session_state.get('favorites', []):
            marker_color = 'orange'
        elif isinstance(row.get('reconnaissances'), list) and row['reconnaissances']:
            marker_color = 'red'
            
        # Pour mode professionnel, changer la couleur pour les restaurants adaptés
        if st.session_state.mode == "professionnel" and row.get('adapte_repas_affaires'):
            marker_color = 'green'
            
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(html, max_width=300),
            tooltip=row['nom'],
            icon=folium.Icon(color=marker_color)
        ).add_to(marker_cluster)
    
    return m

# Fonction d'interface chatbot pour la recherche conversationnelle
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
            {"role": "assistant", "content": f"Bonjour ! Je suis FROODIES, votre assistant pour trouver le restaurant parfait à Paris. Je vous aiderai en mode {st.session_state.mode}. Que recherchez-vous aujourd'hui ?"}
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
        
        # Analyse de la requête pour détecter les filtres
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
        
        # Mots-clés spécifiques au mode professionnel
        if st.session_state.mode == "professionnel":
            professionnel_keywords = {
                "affaires": "adapte_repas_affaires", "business": "adapte_repas_affaires",
                "professionnel": "adapte_repas_affaires", "travail": "adapte_repas_affaires",
                "réunion": "adapte_repas_affaires", "client": "adapte_repas_affaires",
                "calme": "niveau_bruit", "silencieux": "niveau_bruit", "tranquille": "niveau_bruit",
                "privé": "espace_prive", "salon": "espace_prive", "confidentiel": "espace_prive",
                "groupe": "capacite_groupe", "équipe": "capacite_groupe", "collaborateurs": "capacite_groupe",
                "wifi": "wifi", "connexion": "wifi", "internet": "wifi",
                "prises": "prise_electrique", "électrique": "prise_electrique",
                "présentation": "equipement_presentation", "projeter": "equipement_presentation", 
                "facturation": "service_facturation_entreprise", "entreprise": "service_facturation_entreprise",
                "dernière minute": "reservation_derniere_minute", "urgence": "reservation_derniere_minute"
            }
        
        user_input_lower = user_input.lower()
        
        # Détection de type de cuisine
        for keyword, value in cuisine_keywords.items():
            if keyword in user_input_lower:
                if "cuisine_du_monde" not in filters:
                    filters["cuisine_du_monde"] = []
                filters["cuisine_du_monde"].append(value)
        
        # Détection de type spécifique
        for keyword, value in type_keywords.items():
            if keyword in user_input_lower:
                if "type_cuisine" not in filters:
                    filters["type_cuisine"] = []
                filters["type_cuisine"].append(value)
        
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
        
        # Détection de critères professionnels spécifiques 
        if st.session_state.mode == "professionnel":
            for keyword, field in professionnel_keywords.items():
                if keyword in user_input_lower:
                    if field == "niveau_bruit":
                        filters[field] = "Calme"
                    elif field == "capacite_groupe":
                        # Essayer de détecter un nombre de personnes
                        import re
                        numbers = re.findall(r'\d+', user_input_lower)
                        if numbers:
                            for num in numbers:
                                if 5 <= int(num) <= 50:  # Si un nombre entre 5 et 50 est mentionné
                                    filters[field] = int(num)
                                    break
                            else:
                                filters[field] = 10  # Valeur par défaut si nombre détecté hors limites
                        else:
                            filters[field] = 10  # Valeur par défaut si aucun nombre détecté
                    elif field in ["adapte_repas_affaires", "espace_prive", "wifi", 
                                "prise_electrique", "equipement_presentation", 
                                "service_facturation_entreprise", "reservation_derniere_minute"]:
                        filters[field] = True
        
        # Réponse du chatbot
        if filters:
            response = "D'après ce que je comprends, vous cherchez "
            parts = []
            
            if "cuisine_du_monde" in filters:
                parts.append(f"un restaurant {', '.join(filters['cuisine_du_monde'])}")
            
            if "type_cuisine" in filters:
                parts.append(f"spécialisé en {', '.join(filters['type_cuisine'])}")
            
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
            
            # Parties spécifiques au mode professionnel
            if st.session_state.mode == "professionnel":
                if "adapte_repas_affaires" in filters and filters["adapte_repas_affaires"]:
                    parts.append("adapté aux repas d'affaires")
                    
                if "niveau_bruit" in filters:
                    parts.append(f"avec une ambiance {filters['niveau_bruit'].lower()}")
                    
                if "espace_prive" in filters and filters["espace_prive"]:
                    parts.append("disposant d'un espace privé")
                    
                if "capacite_groupe" in filters:
                    parts.append(f"pouvant accueillir un groupe de {filters['capacite_groupe']} personnes")
                    
                if "wifi" in filters and filters["wifi"]:
                    parts.append("avec accès WiFi")
                    
                if "prise_electrique" in filters and filters["prise_electrique"]:
                    parts.append("équipé de prises électriques")
                    
                if "equipement_presentation" in filters and filters["equipement_presentation"]:
                    parts.append("avec équipement pour présentation")
                    
                if "service_facturation_entreprise" in filters and filters["service_facturation_entreprise"]:
                    parts.append("proposant un service de facturation pour entreprise")
                    
                if "reservation_derniere_minute" in filters and filters["reservation_derniere_minute"]:
                    parts.append("acceptant les réservations de dernière minute")
            
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
    
    # Initialiser le mode (personnel ou professionnel)
    if 'mode' not in st.session_state:
        st.session_state.mode = "personnel"
    
    # Chargement des données
    df = load_data()
    user_data = load_user_data()
    
    # En-tête principal
    st.title("🍕 FROODIES")
    st.markdown("### Trouvez votre restaurant idéal à Paris !")
    
    # Choix du mode (personnel ou professionnel)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🍽️ Mode personnel", 
                    type="primary" if st.session_state.mode == "personnel" else "secondary"):
            st.session_state.mode = "personnel"
            # Réinitialiser le chat quand on change de mode
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Bonjour ! Je suis FROODIES, votre assistant pour trouver le restaurant parfait à Paris pour vos sorties personnelles. Que recherchez-vous aujourd'hui ?"}
            ]
            st.rerun()
            
    with col2:
        if st.button("💼 Mode professionnel", 
                    type="primary" if st.session_state.mode == "professionnel" else "secondary"):
            st.session_state.mode = "professionnel"
            # Réinitialiser le chat quand on change de mode
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Bonjour ! Je suis FROODIES, votre assistant pour trouver le restaurant parfait à Paris pour vos repas d'affaires et rencontres professionnelles. Que recherchez-vous aujourd'hui ?"}
            ]
            st.rerun()
    
    # Légende de l'interface selon le mode
    if st.session_state.mode == "personnel":
        st.info("🍽️ **Mode personnel** - Recherchez des restaurants pour vos sorties en famille, entre amis ou en couple.")
    else:
        st.info("💼 **Mode professionnel** - Recherchez des restaurants adaptés pour vos repas d'affaires, rencontres clients ou réunions d'équipe.")
    
    # SIDEBAR: Filtres
    st.sidebar.title("🔍 Filtres de recherche")
    
    # Onglets dans la sidebar pour différents types de filtres
    sidebar_tab1, sidebar_tab2 = st.sidebar.tabs(["🔎 Filtres standards", "🌟 Filtres personnalisés"])
    
    # Filtres standards
    with sidebar_tab1:
        # Filtres standards communs
        price_filter = st.multiselect(
            "Budget",
            options=sorted(df['prix_fourchette'].unique()),
            default=[]
        )
        
        cuisine_monde_filter = st.multiselect(
            "Cuisine du monde",
            options=sorted(df['cuisine_du_monde'].unique()),
            default=[]
        )
        
        cuisine_filter = st.multiselect(
            "Type de cuisine",
            options=sorted([str(x) for x in df['type_cuisine'].unique() if pd.notna(x)]),
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
        
        # Nouveaux filtres communs
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
        
        # Filtres spécifiques au mode professionnel
        if st.session_state.mode == "professionnel":
            st.divider()
            st.subheader("Filtres professionnels")
            
            adapte_affaires = st.checkbox("Adapté aux repas d'affaires", value=False)
            
            niveau_bruit = st.radio(
                "Niveau sonore",
                options=["Tous", "Calme", "Modéré"],
                horizontal=True
            )
            
            espace_prive = st.checkbox("Avec espace privé", value=False)
            
            capacite_min = st.slider(
                "Capacité de groupe minimum",
                min_value=0,
                max_value=30,
                value=0,
                step=5
            )
            
            wifi = st.checkbox("Avec WiFi", value=False)
            
            equipement_presentation = st.checkbox("Équipement pour présentation", value=False)
            
            facturation_entreprise = st.checkbox("Facturation entreprise", value=False)
            
            reservation_derniere_minute = st.checkbox("Réservation dernière minute", value=False)
        
        # Filtrage des données
        mask = df['note_moyenne'] >= note_min
        
        if price_filter:
            mask &= df['prix_fourchette'].isin(price_filter)
        if cuisine_monde_filter:
            mask &= df['cuisine_du_monde'].isin(cuisine_monde_filter)
        if cuisine_filter:
            mask &= df['type_cuisine'].isin(cuisine_filter)
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
        
        # Filtres spécifiques au mode professionnel
        if st.session_state.mode == "professionnel":
            if adapte_affaires:
                mask &= df['adapte_repas_affaires'] == True
                
            if niveau_bruit != "Tous":
                mask &= df['niveau_bruit'] == niveau_bruit
                
            if espace_prive:
                mask &= df['espace_prive'] == True
                
            if capacite_min > 0:
                mask &= df['capacite_groupe'] >= capacite_min
                
            if wifi:
                mask &= df['wifi'] == True
                
            if equipement_presentation:
                mask &= df['equipement_presentation'] == True
                
            if facturation_entreprise:
                mask &= df['service_facturation_entreprise'] == True
                
            if reservation_derniere_minute:
                mask &= df['reservation_derniere_minute'] == True
        
        df_filtered = df[mask]
        
        # Enregistrer cette recherche dans l'historique utilisateur
        current_filters = {}
        if price_filter:
            current_filters["prix_fourchette"] = price_filter
        if cuisine_monde_filter:
            current_filters["cuisine_du_monde"] = cuisine_monde_filter
        if cuisine_filter:
            current_filters["type_cuisine"] = cuisine_filter
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
            
        # Filtres professionnels dans l'historique
        if st.session_state.mode == "professionnel":
            if adapte_affaires:
                current_filters["adapte_repas_affaires"] = True
            if niveau_bruit != "Tous":
                current_filters["niveau_bruit"] = niveau_bruit
            if espace_prive:
                current_filters["espace_prive"] = True
            if capacite_min > 0:
                current_filters["capacite_groupe"] = capacite_min
            if wifi:
                current_filters["wifi"] = True
            if equipement_presentation:
                current_filters["equipement_presentation"] = True
            if facturation_entreprise:
                current_filters["service_facturation_entreprise"] = True
            if reservation_derniere_minute:
                current_filters["reservation_derniere_minute"] = True
        
        if current_filters:
            save_search(current_filters)
    
    # Filtres personnalisés
    with sidebar_tab2:
        st.subheader("Mes filtres personnalisés")
        
        # Afficher les filtres personnalisés enregistrés
        for custom_filter in user_data.get("custom_filters", []):
            if (st.session_state.mode == "professionnel" and "adapte_repas_affaires" in custom_filter.get("conditions", {})) or \
               (st.session_state.mode == "personnel" and "adapte_repas_affaires" not in custom_filter.get("conditions", {})):
                if st.button(f"📌 {custom_filter['name']}", key=f"custom_{custom_filter['id']}"):
                    # Appliquer ce filtre personnalisé
                    conditions = custom_filter.get("conditions", {})
                    st.session_state.chat_filters = conditions
                    st.session_state.show_results = True
                    st.rerun()
                st.caption(f"_{', '.join([f'{k}: {v}' for k, v in custom_filter.get('conditions', {}).items() if k not in ['id', 'name']][:3])}_")
                st.divider()
        
        # Option pour créer un nouveau filtre personnalisé
        with st.expander("✨ Créer un nouveau filtre personnalisé"):
            filter_name = st.text_input("Nom du filtre")
            
            # Afficher les filtres actuellement appliqués
            st.markdown("**Filtres actuels :**")
            applied_filters = []
            
            if price_filter:
                applied_filters.append(f"Budget: {', '.join(price_filter)}")
            if cuisine_monde_filter:
                applied_filters.append(f"Cuisine: {', '.join(cuisine_monde_filter)}")
            if cuisine_filter:
                applied_filters.append(f"Type: {', '.join(cuisine_filter)}")
            if arrond_filter:
                applied_filters.append(f"Arrondissement: {', '.join(arrond_filter)}")
            if ambiance_filter:
                applied_filters.append(f"Ambiance: {', '.join(ambiance_filter)}")
            if qualite_filter:
                applied_filters.append(f"Qualité: {', '.join(qualite_filter)}")
            if has_recognition:
                applied_filters.append("Restaurants récompensés")
                
            # Filtres professionnels le cas échéant
            if st.session_state.mode == "professionnel":
                if adapte_affaires:
                    applied_filters.append("Adapté aux repas d'affaires")
                if niveau_bruit != "Tous":
                    applied_filters.append(f"Niveau sonore: {niveau_bruit}")
                if espace_prive:
                    applied_filters.append("Avec espace privé")
                if capacite_min > 0:
                    applied_filters.append(f"Capacité min: {capacite_min}")
                if wifi:
                    applied_filters.append("Avec WiFi")
                if equipement_presentation:
                    applied_filters.append("Avec équipement présentation")
                if facturation_entreprise:
                    applied_filters.append("Facturation entreprise")
                if reservation_derniere_minute:
                    applied_filters.append("Réservation dernière minute")
            
            if applied_filters:
                for f in applied_filters:
                    st.markdown(f"- {f}")
            else:
                st.markdown("_Aucun filtre appliqué actuellement_")
                
            if filter_name and applied_filters and st.button("Enregistrer ce filtre"):
                new_filter = {
                    "id": len(user_data.get("custom_filters", [])) + 1,
                    "name": filter_name,
                    "conditions": current_filters
                }
                
                if "custom_filters" not in user_data:
                    user_data["custom_filters"] = []
                    
                user_data["custom_filters"].append(new_filter)
                save_user_data(user_data)
                st.success(f"Filtre '{filter_name}' enregistré avec succès !")
                st.rerun()
    
    # Interface principale
    # Interface chatbot
    filters_from_chat = chatbot_interface(df)
    
    if filters_from_chat:
        # Mise à jour des filtres selon l'entrée du chatbot
        st.session_state.chat_filters = filters_from_chat
    
    # Vérifier si des filtres manuels sont activés (à partir de la sidebar)
    has_manual_filters = any([price_filter, cuisine_monde_filter, cuisine_filter, arrond_filter, ambiance_filter, 
                            qualite_filter, jours_filter, has_recognition]) or note_min > 4.0
                            
    # Filtres professionnels
    if st.session_state.mode == "professionnel":
        has_manual_filters = has_manual_filters or any([
            adapte_affaires, niveau_bruit != "Tous", espace_prive, capacite_min > 0,
            wifi, equipement_presentation, facturation_entreprise, reservation_derniere_minute
        ])
    
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
            
            if "cuisine_du_monde" in st.session_state.chat_filters:
                chat_mask &= df['cuisine_du_monde'].isin(st.session_state.chat_filters["cuisine_du_monde"])
                
            if "type_cuisine" in st.session_state.chat_filters:
                chat_mask &= df['type_cuisine'].isin(st.session_state.chat_filters["type_cuisine"])
            
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
            
            # Filtres professionnels depuis le chatbot
            if st.session_state.mode == "professionnel":
                if "adapte_repas_affaires" in st.session_state.chat_filters:
                    chat_mask &= df['adapte_repas_affaires'] == st.session_state.chat_filters["adapte_repas_affaires"]
                
                if "niveau_bruit" in st.session_state.chat_filters:
                    chat_mask &= df['niveau_bruit'] == st.session_state.chat_filters["niveau_bruit"]
                
                if "espace_prive" in st.session_state.chat_filters:
                    chat_mask &= df['espace_prive'] == st.session_state.chat_filters["espace_prive"]
                
                if "capacite_groupe" in st.session_state.chat_filters:
                    chat_mask &= df['capacite_groupe'] >= st.session_state.chat_filters["capacite_groupe"]
                
                if "wifi" in st.session_state.chat_filters:
                    chat_mask &= df['wifi'] == st.session_state.chat_filters["wifi"]
                
                if "prise_electrique" in st.session_state.chat_filters:
                    chat_mask &= df['prise_electrique'] == st.session_state.chat_filters["prise_electrique"]
                
                if "equipement_presentation" in st.session_state.chat_filters:
                    chat_mask &= df['equipement_presentation'] == st.session_state.chat_filters["equipement_presentation"]
                
                if "service_facturation_entreprise" in st.session_state.chat_filters:
                    chat_mask &= df['service_facturation_entreprise'] == st.session_state.chat_filters["service_facturation_entreprise"]
                
                if "reservation_derniere_minute" in st.session_state.chat_filters:
                    chat_mask &= df['reservation_derniere_minute'] == st.session_state.chat_filters["reservation_derniere_minute"]
            
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
            if st.session_state.mode == "professionnel":
                pct_adapte = (filtered_data['adapte_repas_affaires'] == True).sum() / len(filtered_data) * 100 if not filtered_data.empty else 0
                st.metric("% Adapté affaires", f"{pct_adapte:.0f}%")
            else:
                st.metric("Cuisines différentes", filtered_data['cuisine_du_monde'].nunique() if not filtered_data.empty else "N/A")
        
        # Onglets pour différentes vues
        if st.session_state.mode == "professionnel":
            tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Carte", "📊 Statistiques pro", "📋 Liste", "⭐ Distinctions"])
        else:
            tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Carte", "📊 Statistiques", "📋 Liste", "⭐ Distinctions"])
        
        # Onglet Carte
        with tab1:
            if not filtered_data.empty:
                map_fig = create_restaurant_map(filtered_data)
                folium_static(map_fig, width=1000, height=600)
                
                if st.session_state.mode == "professionnel":
                    st.info("🟢 Vert = Adapté aux repas d'affaires | 🔴 Rouge = Récompenses gastronomiques | 🟠 Orange = Favoris")
            else:
                st.warning("Aucun restaurant ne correspond à vos critères")
        
        # Onglet Statistiques
        with tab2:
            if not filtered_data.empty:
                if st.session_state.mode == "professionnel":
                    # Statistiques spécifiques au mode professionnel
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Distribution des niveaux de bruit
                        fig_bruit = px.pie(
                            filtered_data, 
                            names='niveau_bruit', 
                            title="Répartition par niveau sonore",
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.warning("Aucun restaurant ne correspond à vos critères pour générer des statistiques")
        
        # Onglet Liste
        with tab3:
            if not filtered_data.empty:
                # Filtres d'affichage
                sort_options = ["Note (décroissant)", "Prix (croissant)", "Prix (décroissant)", "Nombre d'avis"]
                if st.session_state.mode == "professionnel":
                    sort_options.append("Capacité groupe (décroissant)")
                
                sort_by = st.selectbox("Trier par", options=sort_options)
                
                # Appliquer le tri
                if sort_by == "Note (décroissant)":
                    filtered_data = filtered_data.sort_values(by='note_moyenne', ascending=False)
                elif sort_by == "Prix (croissant)":
                    # Définir un ordre personnalisé pour les fourchettes de prix
                    prix_order = {"10-20": 1, "20-30": 2, "30-50": 3, "50-100": 4, "100+": 5}
                    filtered_data['prix_ordre'] = filtered_data['prix_fourchette'].map(prix_order)
                    filtered_data = filtered_data.sort_values(by='prix_ordre')
                    filtered_data = filtered_data.drop('prix_ordre', axis=1)
                elif sort_by == "Prix (décroissant)":
                    prix_order = {"10-20": 1, "20-30": 2, "30-50": 3, "50-100": 4, "100+": 5}
                    filtered_data['prix_ordre'] = filtered_data['prix_fourchette'].map(prix_order)
                    filtered_data = filtered_data.sort_values(by='prix_ordre', ascending=False)
                    filtered_data = filtered_data.drop('prix_ordre', axis=1)
                elif sort_by == "Nombre d'avis":
                    filtered_data = filtered_data.sort_values(by='nb_avis', ascending=False)
                elif sort_by == "Capacité groupe (décroissant)":
                    filtered_data = filtered_data.sort_values(by='capacite_groupe', ascending=False)
                
                # Pagination
                items_per_page = 10
                total_pages = (len(filtered_data) + items_per_page - 1) // items_per_page
                
                if 'current_page' not in st.session_state:
                    st.session_state.current_page = 1
                
                # Boutons pagination
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    if st.button("⬅️ Précédent") and st.session_state.current_page > 1:
                        st.session_state.current_page -= 1
                        st.rerun()
                
                with col2:
                    st.markdown(f"**Page {st.session_state.current_page}/{total_pages}**")
                
                with col3:
                    if st.button("Suivant ➡️") and st.session_state.current_page < total_pages:
                        st.session_state.current_page += 1
                        st.rerun()
                
                # Calculer l'index de début et de fin pour la pagination
                start_idx = (st.session_state.current_page - 1) * items_per_page
                end_idx = min(start_idx + items_per_page, len(filtered_data))
                
                # Afficher les restaurants pour la page courante
                for idx, resto in filtered_data.iloc[start_idx:end_idx].iterrows():
                    with st.container():
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.subheader(resto['nom'])
                            st.markdown(f"_{resto['cuisine_du_monde']}, {resto['type_cuisine']} • {resto['prix_fourchette']}_")
                            st.markdown(f"⭐ {resto['note_moyenne']}/5 ({resto['nb_avis']} avis)")
                            
                            # Afficher les distinctions si présentes
                            if isinstance(resto.get('reconnaissances'), list) and resto['reconnaissances']:
                                reco_texts = []
                                for reco in resto['reconnaissances'][:2]:  # Limiter à 2 pour la clarté
                                    reco_texts.append(f"{reco['guide']} {reco['annee']} - {reco['distinction']}")
                                st.markdown(f"🏆 {' | '.join(reco_texts)}")
                            
                            # Informations sur la qualité de la nourriture
                            if isinstance(resto.get('qualite_nourriture'), list) and resto['qualite_nourriture']:
                                st.markdown(f"✨ {', '.join(resto['qualite_nourriture'][:3])}")
                                
                            st.markdown(f"📍 {resto['adresse']}")
                            
                            # Informations spécifiques au mode professionnel
                            if st.session_state.mode == "professionnel":
                                pro_infos = []
                                
                                if resto.get('adapte_repas_affaires'):
                                    pro_infos.append("✅ Adapté aux repas d'affaires")
                                
                                pro_infos.append(f"🔊 Niveau sonore: {resto.get('niveau_bruit', 'Non spécifié')}")
                                
                                if resto.get('espace_prive'):
                                    pro_infos.append(f"🚪 Espace privé: {resto.get('type_espace_prive', 'Disponible')}")
                                
                                if resto.get('capacite_groupe', 0) > 0:
                                    pro_infos.append(f"👥 Capacité groupe: {resto.get('capacite_groupe')} personnes")
                                
                                if resto.get('wifi'):
                                    pro_infos.append("📶 WiFi disponible")
                                
                                if resto.get('equipement_presentation'):
                                    pro_infos.append("📊 Équipement présentation disponible")
                                
                                if pro_infos:
                                    st.markdown(' | '.join(pro_infos[:3]))  # Limiter pour éviter de surcharger
                                    
                                    if len(pro_infos) > 3:
                                        st.markdown(' | '.join(pro_infos[3:]))
                        
                        with col2:
                            # Favoris et détails
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                # Vérifie si ce restaurant est dans les favoris
                                is_favorite = resto['nom'] in st.session_state.favorites
                                
                                # Bouton pour ajouter/retirer des favoris
                                if is_favorite:
                                    if st.button("❤️ Retirer", key=f"fav_{idx}"):
                                        st.session_state.favorites.remove(resto['nom'])
                                        st.rerun()
                                else:
                                    if st.button("🤍 Favori", key=f"fav_{idx}"):
                                        st.session_state.favorites.append(resto['nom'])
                                        st.rerun()
                            
                            with col_b:
                                # Bouton pour voir plus de détails
                                if st.button("Détails", key=f"details_{idx}"):
                                    st.session_state.selected_restaurant = resto['id']
                                    user_data = track_restaurant_view(resto['id'], resto['nom'], user_data)
                                    save_user_data(user_data)
                                    st.rerun()
                        
                        st.divider()
                
                # Rappel des boutons de pagination en bas de page
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    if st.button("⬅️ Précédent", key="prev_bot") and st.session_state.current_page > 1:
                        st.session_state.current_page -= 1
                        st.rerun()
                
                with col2:
                    st.markdown(f"**Page {st.session_state.current_page}/{total_pages}**")
                
                with col3:
                    if st.button("Suivant ➡️", key="next_bot") and st.session_state.current_page < total_pages:
                        st.session_state.current_page += 1
                        st.rerun()
            else:
                st.warning("Aucun restaurant ne correspond à vos critères")
        
        # Onglet Distinctions
        with tab4:
            if not filtered_data.empty:
                # Filtrer les restaurants avec distinctions
                restaurants_with_distinctions = filtered_data[filtered_data['reconnaissances'].apply(
                    lambda x: isinstance(x, list) and len(x) > 0)]
                
                if not restaurants_with_distinctions.empty:
                    # Tri par prestigieusité des reconnaissances (priorité aux étoilés Michelin)
                    def prestige_score(reconnaissances):
                        score = 0
                        if not isinstance(reconnaissances, list):
                            return 0
                        for r in reconnaissances:
                            guide = r.get('guide', '')
                            distinction = r.get('distinction', '')
                            
                            if guide == 'Guide Michelin' and distinction == 'Étoilé':
                                score += 100
                            elif guide == 'Guide Michelin' and distinction == 'Bib Gourmand':
                                score += 70
                            elif guide == 'Guide Michelin':
                                score += 50
                            elif guide == 'Gault & Millau' and 'Toques' in distinction:
                                # Extraire le nombre de toques si spécifié
                                try:
                                    toques = int(distinction.split()[0])
                                    score += 40 + toques * 5
                                except:
                                    score += 40
                            elif guide == 'Gault & Millau':
                                score += 30
                            elif guide == '50 Best':
                                score += 45
                            else:
                                score += 20
                        return score
                    
                    restaurants_with_distinctions['prestige_score'] = restaurants_with_distinctions['reconnaissances'].apply(prestige_score)
                    restaurants_with_distinctions = restaurants_with_distinctions.sort_values(by='prestige_score', ascending=False)
                    
                    # Organisation par guide gastronomique
                    guides = {}
                    for idx, resto in restaurants_with_distinctions.iterrows():
                        for reco in resto['reconnaissances']:
                            guide = reco.get('guide', 'Autre')
                            if guide not in guides:
                                guides[guide] = []
                            
                            guides[guide].append({
                                'restaurant': resto,
                                'distinction': reco.get('distinction', ''),
                                'annee': reco.get('annee', '')
                            })
                    
                    # Affichage par guide
                    for guide, restaurants in guides.items():
                        st.subheader(f"🏆 {guide}")
                        
                        # Nombre de restaurants par distinction dans ce guide
                        distinctions_count = {}
                        for r in restaurants:
                            distinction = r['distinction']
                            if distinction not in distinctions_count:
                                distinctions_count[distinction] = 0
                            distinctions_count[distinction] += 1
                        
                        # Afficher les compteurs de distinctions
                        distinction_text = ", ".join([f"{count} {distinction}" for distinction, count in distinctions_count.items()])
                        st.markdown(f"_{distinction_text}_")
                        
                        # Afficher les restaurants pour ce guide
                        for item in restaurants:
                            resto = item['restaurant']
                            distinction = item['distinction']
                            annee = item['annee']
                            
                            with st.container():
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.markdown(f"**{resto['nom']}** - _{distinction} ({annee})_")
                                    st.markdown(f"_{resto['cuisine_du_monde']}, {resto['type_cuisine']} • {resto['prix_fourchette']}_")
                                    st.markdown(f"⭐ {resto['note_moyenne']}/5 ({resto['nb_avis']} avis)")
                                    st.markdown(f"📍 {resto['adresse']}")
                                
                                with col2:
                                    if st.button("Voir détails", key=f"reco_{resto['id']}_{annee}"):
                                        st.session_state.selected_restaurant = resto['id']
                                        user_data = track_restaurant_view(resto['id'], resto['nom'], user_data)
                                        save_user_data(user_data)
                                        st.rerun()
                            
                            st.divider()
                else:
                    st.info("Aucun restaurant récompensé ne correspond à vos critères de recherche.")
            else:
                st.warning("Aucun restaurant ne correspond à vos critères")
    else:
        # Section Recommandations (visible uniquement si pas de filtres actifs)
        st.divider()
        st.subheader("✨ Recommandations pour vous")
        
        # Restaurants populaires (toujours affichés)
        if st.session_state.mode == "professionnel":
            st.markdown("### Les plus adaptés aux repas d'affaires")
            business_df = df[df['adapte_repas_affaires'] == True].sort_values(by=['note_moyenne'], ascending=False).head(3)
        else:
            st.markdown("### Les plus populaires à Paris")
            business_df = df.sort_values(by=['note_moyenne', 'nb_avis'], ascending=False).head(3)
        
        if not business_df.empty:
            cols = st.columns(3)
            for i, (idx, resto) in enumerate(business_df.iterrows()):
                with cols[i]:
                    st.markdown(f"**{resto['nom']}**")
                    st.markdown(f"_{resto['cuisine_du_monde']}, {resto['type_cuisine']} • {resto['prix_fourchette']}_")
                    st.markdown(f"⭐ {resto['note_moyenne']}/5 ({resto['nb_avis']} avis)")
                    
                    # Afficher les reconnaissances s'il y en a
                    if isinstance(resto.get('reconnaissances'), list) and resto['reconnaissances']:
                        for reco in resto['reconnaissances'][:1]:  # Limiter à 1 pour la compacité
                            st.markdown(f"🏆 {reco['guide']} - {reco['distinction']}")
                    
                    st.markdown(f"🏙️ {resto['arrondissement']}")
                    
                    # En mode professionnel, afficher des infos supplémentaires
                    if st.session_state.mode == "professionnel":
                        pro_infos = []
                        if resto.get('espace_prive'):
                            pro_infos.append(f"🚪 Espace privé")
                        if resto.get('wifi'):
                            pro_infos.append("📶 WiFi")
                        if resto.get('niveau_bruit') == "Calme":
                            pro_infos.append("🔊 Calme")
                        
                        if pro_infos:
                            st.markdown(' | '.join(pro_infos))
                    
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
                        st.markdown(f"_{resto['cuisine_du_monde']}, {resto['type_cuisine']} • {resto['prix_fourchette']}_")
                        
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
        
        # Section spécifique au mode professionnel
        if st.session_state.mode == "professionnel":
            st.markdown("### Idéal pour des présentations")
            presentation_df = df[(df['equipement_presentation'] == True) & (df['wifi'] == True)].sort_values(by=['note_moyenne'], ascending=False).head(3)
            
            if not presentation_df.empty:
                cols = st.columns(3)
                for i, (idx, resto) in enumerate(presentation_df.iterrows()):
                    with cols[i]:
                        st.markdown(f"**{resto['nom']}**")
                        st.markdown(f"_{resto['cuisine_du_monde']}, {resto['type_cuisine']} • {resto['prix_fourchette']}_")
                        st.markdown(f"⭐ {resto['note_moyenne']}/5")
                        
                        # Infos professionnelles
                        pro_infos = []
                        pro_infos.append("📊 Équipement présentation")
                        pro_infos.append("📶 WiFi disponible")
                        if resto.get('prise_electrique'):
                            pro_infos.append("🔌 Prises électriques")
                        
                        st.markdown(' | '.join(pro_infos[:3]))
                        
                        if resto.get('capacite_groupe', 0) > 0:
                            st.markdown(f"👥 Capacité groupe: {resto.get('capacite_groupe')} personnes")
                        
                        # Bouton pour voir plus de détails
                        if st.button("Voir plus", key=f"pres_{idx}"):
                            st.session_state.selected_restaurant = resto['id']
                            user_data = track_restaurant_view(resto['id'], resto['nom'], user_data)
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
                },
                {
                    "id": 3,
                    "name": "Repas d'affaires important",
                    "conditions": {
                        "adapte_repas_affaires": True,
                        "niveau_bruit": "Calme",
                        "espace_prive": True,
                        "note_moyenne": 4.5,
                        "prix_fourchette": ["50-100"]
                    }
                },
                {
                    "id": 4,
                    "name": "Réunion d'équipe",
                    "conditions": {
                        "adapte_repas_affaires": True,
                        "wifi": True,
                        "capacite_groupe": 10,
                        "prix_fourchette": ["20-30", "30-50"]
                    }
                }
            ]
        }
        with open("user_data.json", "w") as f:
            json.dump(default_user_data, f)
    main()