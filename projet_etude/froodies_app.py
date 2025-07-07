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
    df = pd.read_csv("restaurants_paris_dataset.csv")
    return df

# Fonction pour charger les données utilisateur (historique, préférences, filtres personnalisés)
@st.cache_data
def load_user_data():
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
                        "prix_fourchette": ["€€-€€€", "€€€-€€€€"],
                        "note_moyenne": 4.5
                    }
                },
                {
                    "id": 2,
                    "name": "Déjeuner rapide",
                    "conditions": {
                        "ambiance": ["Décontracté"],
                        "prix_fourchette": ["€-€€"],
                        "temps_service": "Rapide"
                    }
                }
            ]
        }

# Fonction pour sauvegarder les données utilisateur
def save_user_data(user_data):
    with open("user_data.json", "w") as f:
        json.dump(user_data, f)

# Fonction pour enregistrer une recherche dans l'historique
def save_search(filters):
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

# Fonction pour créer la carte des restaurants
def create_restaurant_map(df_filtered):
    # Création de la carte centrée sur Paris
    m = folium.Map(location=[48.8566, 2.3522], zoom_start=12)
    
    # Création d'un cluster de marqueurs
    marker_cluster = MarkerCluster().add_to(m)
    
    # Ajout des marqueurs pour chaque restaurant
    for idx, row in df_filtered.iterrows():
        html = f"""
            <div style='width: 200px'>
                <h4>{row['nom']}</h4>
                <p><b>Cuisine:</b> {row['type_cuisine']}</p>
                <p><b>Prix:</b> {row['prix_fourchette']}</p>
                <p><b>Note:</b> {row['note_moyenne']}/5 ({row['nb_avis']} avis)</p>
                <p><b>Adresse:</b> {row['adresse']}</p>
            </div>
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(html, max_width=300),
            tooltip=row['nom'],
            icon=folium.Icon(color='red' if row['nom'] in st.session_state.get('favorites', []) else 'blue')
        ).add_to(marker_cluster)
    
    return m

# Système de recommandation basé sur le contenu
def content_based_recommendations(df, restaurant_id=None, user_preferences=None, top_n=5):
    """
    Génère des recommandations basées sur:
    - un restaurant spécifique (si restaurant_id est fourni)
    - les préférences de l'utilisateur (si user_preferences est fourni)
    """
    # Enrichir les caractéristiques des restaurants
    df['features'] = df['type_cuisine'] + ' ' + df['ambiance'] + ' ' + df['arrondissement'] + ' ' + df['prix_fourchette']
    
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
            user_preferences.get('ambiance', ''),
            user_preferences.get('arrondissement', ''),
            user_preferences.get('prix_fourchette', '')
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

# Fonction pour suggérer des filtres personnalisés basés sur l'historique
def suggest_custom_filters(df):
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
    """Génère un nom descriptif pour un filtre basé sur ses conditions"""
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
            if "€-€€" in prix:
                name_parts.append("Bon marché")
            elif "€€€-€€€€" in prix:
                name_parts.append("Gastronomique")
        elif isinstance(prix, str):
            if "€-€€" == prix:
                name_parts.append("Bon marché")
            elif "€€€-€€€€" == prix:
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
    
    # Si nous avons des parties de nom, les assembler
    if name_parts:
        return " ".join(name_parts)
    else:
        # Nom par défaut
        return f"Mes préférences {len(filter_conditions)} critères"

def main():
    # Initialisation de l'état de session
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    
    # Chargement des données
    df = load_data()
    user_data = load_user_data()
    
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
        
        note_min = st.slider(
            "Note minimum",
            min_value=float(df['note_moyenne'].min()),
            max_value=float(df['note_moyenne'].max()),
            value=4.0,
            step=0.1
        )
        
        # Affichage des filtres les plus utilisés
        most_used_filters = get_most_used_filters()
        if most_used_filters:
            st.subheader("💡 Vos filtres fréquents")
            for filter_name, filter_data in most_used_filters[:3]:  # Top 3
                with st.expander(f"{filter_name} ({filter_data['count']} utilisations)"):
                    # Afficher les valeurs les plus utilisées
                    top_values = sorted(filter_data["values"].items(), key=lambda x: x[1], reverse=True)[:3]
                    for value, count in top_values:
                        st.write(f"- {value}: {count} fois")
    
    # Filtres personnalisés
    with sidebar_tab2:
        # Affichage des filtres personnalisés
        if user_data["custom_filters"]:
            for custom_filter in user_data["custom_filters"]:
                if st.button(f"🔍 {custom_filter['name']}", key=f"filter_{custom_filter['id']}"):
                    # Appliquer ce filtre personnalisé
                    # (Ceci est une simplification, l'application réelle serait plus complexe)
                    if "prix_fourchette" in custom_filter["conditions"]:
                        price_filter = custom_filter["conditions"]["prix_fourchette"] if isinstance(custom_filter["conditions"]["prix_fourchette"], list) else [custom_filter["conditions"]["prix_fourchette"]]
                    
                    if "type_cuisine" in custom_filter["conditions"]:
                        cuisine_filter = custom_filter["conditions"]["type_cuisine"] if isinstance(custom_filter["conditions"]["type_cuisine"], list) else [custom_filter["conditions"]["type_cuisine"]]
                    
                    if "arrondissement" in custom_filter["conditions"]:
                        arrond_filter = custom_filter["conditions"]["arrondissement"] if isinstance(custom_filter["conditions"]["arrondissement"], list) else [custom_filter["conditions"]["arrondissement"]]
                    
                    if "ambiance" in custom_filter["conditions"]:
                        ambiance_filter = custom_filter["conditions"]["ambiance"] if isinstance(custom_filter["conditions"]["ambiance"], list) else [custom_filter["conditions"]["ambiance"]]
                    
                    if "note_moyenne" in custom_filter["conditions"]:
                        note_min = float(custom_filter["conditions"]["note_moyenne"])
        else:
            st.info("Vous n'avez pas encore de filtres personnalisés")
        
        # Bouton pour créer un nouveau filtre personnalisé
        if st.button("➕ Créer un filtre personnalisé"):
            st.session_state.creating_filter = True
        
        # Affichage des suggestions de filtres personnalisés
        suggested_filters = suggest_custom_filters(df)
        if suggested_filters:
            st.subheader("💡 Suggestions IA")
            for suggestion in suggested_filters:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{suggestion['name']}** ({suggestion['confidence']}% confiance)")
                with col2:
                    if st.button("Ajouter", key=f"add_suggestion_{suggestion['name']}"):
                        # Ajouter cette suggestion aux filtres personnalisés
                        user_data["custom_filters"].append({
                            "id": len(user_data["custom_filters"]) + 1,
                            "name": suggestion["name"],
                            "conditions": suggestion["conditions"]
                        })
                        save_user_data(user_data)
                        st.rerun()
            
        # Si l'utilisateur n'a ni préférences ni favoris
        else:
            st.write("Découvertes populaires :")
            
            # Obtenir les restaurants les mieux notés
            popular_df = df.sort_values(by=['note_moyenne', 'nb_avis'], ascending=False).head(5)
            
            for i, (idx, resto) in enumerate(popular_df.iterrows()):
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    st.write(f"**#{i+1}**")
                
                with col2:
                    st.write(f"**{resto['nom']}** - {resto['type_cuisine']}")
                    st.write(f"🏙️ {resto['arrondissement']} • 💰 {resto['prix_fourchette']} • ⭐ {resto['note_moyenne']}/5")
                    st.write(f"🌈 {resto['ambiance']}")
                
                with col3:
                    # Bouton pour ajouter aux favoris
                    if resto['nom'] in st.session_state.favorites:
                        if st.button("❤️", key=f"rec_sim_unfav_{idx}"):
                            st.session_state.favorites.remove(resto['nom'])
                            user_data["favorite_restaurants"] = st.session_state.favorites
                            save_user_data(user_data)
                            st.rerun()
                    else:
                        if st.button("🤍", key=f"rec_sim_fav_{idx}"):
                            st.session_state.favorites.append(resto['nom'])
                            user_data["favorite_restaurants"] = st.session_state.favorites
                            save_user_data(user_data)
                            st.rerun()
    
    # Interface pour créer un nouveau filtre personnalisé
    if st.session_state.get("creating_filter", False):
        st.sidebar.subheader("Créer un filtre personnalisé")
        
        filter_name = st.sidebar.text_input("Nom du filtre")
        
        st.sidebar.write("Sélectionnez les conditions:")
        save_price = st.sidebar.checkbox("Inclure le budget actuel")
        save_cuisine = st.sidebar.checkbox("Inclure le type de cuisine actuel")
        save_arrond = st.sidebar.checkbox("Inclure l'arrondissement actuel")
        save_ambiance = st.sidebar.checkbox("Inclure l'ambiance actuelle")
        save_note = st.sidebar.checkbox("Inclure la note minimale actuelle")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Annuler"):
                st.session_state.creating_filter = False
                st.rerun()
        
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
                    
                    if save_arrond and arrond_filter:
                        conditions["arrondissement"] = arrond_filter
                    
                    if save_ambiance and ambiance_filter:
                        conditions["ambiance"] = ambiance_filter
                    
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
                        st.session_state.creating_filter = False
                        st.rerun()
                    else:
                        st.sidebar.error("Veuillez sélectionner au moins une condition")
    
    # Filtrage des données
    mask = df['note_moyenne'] >= note_min
    
    if price_filter:
        mask &= df['prix_fourchette'].isin(price_filter)
    if cuisine_filter:
        mask &= df['type_cuisine'].isin(cuisine_filter)
    if arrond_filter:
        mask &= df['arrondissement'].isin(arrond_filter)
    if ambiance_filter:
        mask &= df['ambiance'].isin(ambiance_filter)
    
    df_filtered = df[mask]
    
    # Enregistrer cette recherche dans l'historique utilisateur
    current_filters = {}
    if price_filter:
        current_filters["prix_fourchette"] = price_filter
    if cuisine_filter:
        current_filters["type_cuisine"] = cuisine_filter
    if arrond_filter:
        current_filters["arrondissement"] = arrond_filter
    if ambiance_filter:
        current_filters["ambiance"] = ambiance_filter
    if note_min > 4.0:  # Seulement si modifié par rapport à la valeur par défaut
        current_filters["note_moyenne"] = note_min
    
    if current_filters:
        save_search(current_filters)
    
    # Interface principale
    st.title("🍕 FROODIES")
    st.markdown("Trouve ton resto préféré à Paris !")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Restaurants trouvés", len(df_filtered))
    with col2:
        st.metric("Note moyenne", f"{df_filtered['note_moyenne'].mean():.1f}/5" if not df_filtered.empty else "N/A")
    with col3:
        st.metric("Prix moyen", df_filtered['prix_fourchette'].mode()[0] if not df_filtered.empty else "N/A")
    with col4:
        st.metric("Cuisines différentes", df_filtered['type_cuisine'].nunique() if not df_filtered.empty else "N/A")
    
    # Onglets pour différentes vues
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Carte", "📊 Statistiques", "📋 Liste", "✨ Recommandations"])
    
    # Onglet Carte
    with tab1:
        st.subheader("Carte des restaurants")
        if not df_filtered.empty:
            map_fig = create_restaurant_map(df_filtered)
            folium_static(map_fig, width=1200)
        else:
            st.warning("Aucun restaurant ne correspond à vos critères")
    
    # Onglet Statistiques©
    with tab2:
        if not df_filtered.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribution des types de cuisine
                counts_df = df_filtered['type_cuisine'].value_counts().reset_index()
                # Vérifier le nom réel de la colonne de comptage
                print(counts_df.columns)  # Pour savoir quel est le nom exact

                fig_cuisine = px.pie(
                    counts_df,
                    values=counts_df.columns[1],  # Utiliser le second nom de colonne, quel qu'il soit
                    names='index',  # La colonne 'index' contient les valeurs de 'type_cuisine'
                    title='Répartition des types de cuisine'
                )
                st.plotly_chart(fig_cuisine)
            
            with col2:
                # Distribution des prix
                fig_prix = px.histogram(
                    df_filtered,
                    x='prix_fourchette',
                    title='Distribution des fourchettes de prix'
                )
                st.plotly_chart(fig_prix)
                
            # Notes moyennes par type de cuisine
            fig_notes = px.box(
                df_filtered,
                x='type_cuisine',
                y='note_moyenne',
                title='Distribution des notes par type de cuisine'
            )
            st.plotly_chart(fig_notes)
        else:
            st.warning("Aucun restaurant ne correspond à vos critères")
    
    # Onglet Liste
    with tab3:
        if not df_filtered.empty:
            for idx, resto in df_filtered.iterrows():
                with st.expander(f"🍽️ {resto['nom']} - {resto['type_cuisine']}"):
                    col1, col2 = st.columns([2,1])
                    
                    with col1:
                        st.markdown(f"**Adresse:** {resto['adresse']}")
                        st.markdown(f"**Spécialité:** {resto['specialite']}")
                        st.markdown(f"**Ambiance:** {resto['ambiance']}")
                        if resto.get('vegetarien_friendly', False):
                            st.markdown("✅ Options végétariennes")
                        if resto.get('reservation_recommandee', False):
                            st.markdown("📞 Réservation recommandée")
                    
                    with col2:
                        st.metric("Note", f"{resto['note_moyenne']}/5")
                        st.metric("Nombre d'avis", resto['nb_avis'])
                        st.markdown(f"**Prix:** {resto['prix_fourchette']}")
                        
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
    
    # Onglet Recommandations
    with tab4:
        st.subheader("Restaurants recommandés pour vous")
        
        # Générer des recommandations basées sur les préférences
        user_preferences = {}
        if cuisine_filter:
            user_preferences["type_cuisine"] = cuisine_filter[0] if len(cuisine_filter) == 1 else " ".join(cuisine_filter)
        if price_filter:
            user_preferences["prix_fourchette"] = price_filter[0] if len(price_filter) == 1 else " ".join(price_filter)
        if ambiance_filter:
            user_preferences["ambiance"] = ambiance_filter[0] if len(ambiance_filter) == 1 else " ".join(ambiance_filter)
        if arrond_filter:
            user_preferences["arrondissement"] = arrond_filter[0] if len(arrond_filter) == 1 else " ".join(arrond_filter)
        
        # Si l'utilisateur a spécifié des préférences
        if user_preferences:
            recommended_df = content_based_recommendations(df, user_preferences=user_preferences, top_n=5)
            
            if not recommended_df.empty:
                st.write("Basés sur vos filtres actuels:")
                
                for i, (idx, resto) in enumerate(recommended_df.iterrows()):
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        st.write(f"**#{i+1}**")
                    
                    with col2:
                        st.write(f"**{resto['nom']}** - {resto['type_cuisine']}")
                        st.write(f"🏙️ {resto['arrondissement']} • 💰 {resto['prix_fourchette']} • ⭐ {resto['note_moyenne']}/5")
                        st.write(f"🌈 {resto['ambiance']}")
                    
                    with col3:
                        # Bouton pour ajouter aux favoris
                        if resto['nom'] in st.session_state.favorites:
                            if st.button("❤️", key=f"rec_sim_unfav_{idx}"):
                                st.session_state.favorites.remove(resto['nom'])
                                user_data["favorite_restaurants"] = st.session_state.favorites
                                save_user_data(user_data)
                                st.rerun()
                        else:
                            if st.button("🤍", key=f"rec_sim_fav_{idx}"):
                                st.session_state.favorites.append(resto['nom'])
                                user_data["favorite_restaurants"] = st.session_state.favorites
                                save_user_data(user_data)
                                st.rerun()
                        if resto['nom'] in st.session_state.favorites:
                            if st.button("❤️", key=f"rec_unfav_{idx}"):
                                st.session_state.favorites.remove(resto['nom'])
                                user_data["favorite_restaurants"] = st.session_state.favorites
                                save_user_data(user_data)
                                st.rerun()
                        else:
                            if st.button("🤍", key=f"rec_fav_{idx}"):
                                st.session_state.favorites.append(resto['nom'])
                                user_data["favorite_restaurants"] = st.session_state.favorites
                                save_user_data(user_data)
                                st.rerun()
            else:
                st.info("Nous n'avons pas trouvé de recommandations correspondant à vos préférences actuelles.")
        
        else:
            # Si l'utilisateur a des favoris, utiliser le premier pour les recommandations
            if st.session_state.favorites:
                favorite_id = df[df['nom'] == st.session_state.favorites[0]]['id'].values[0]
                st.write(f"Basés sur votre restaurant favori : **{st.session_state.favorites[0]}**")
                
                recommended_df = content_based_recommendations(df, restaurant_id=favorite_id, top_n=5)
                
                for i, (idx, resto) in enumerate(recommended_df.iterrows()):
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        st.write(f"**#{i+1}**")
                    
                    with col2:
                        st.write(f"**{resto['nom']}** - {resto['type_cuisine']}")
                        st.write(f"🏙️ {resto['arrondissement']} • 💰 {resto['prix_fourchette']} • ⭐ {resto['note_moyenne']}/5")
                        st.write(f"🌈 {resto['ambiance']}")
                    
                    with col3:
                        # Bouton pour ajouter aux favoris
                        if resto['nom'] in st.session_state.favorites:
                            if st.button("❤️", key=f"rec_pop_unfav_{idx}"):
                                st.session_state.favorites.remove(resto['nom'])
                                user_data["favorite_restaurants"] = st.session_state.favorites
                                save_user_data(user_data)
                                st.rerun()
                        else:
                            if st.button("🤍", key=f"rec_pop_fav_{idx}"):
                                st.session_state.favorites.append(resto['nom'])
                                user_data["favorite_restaurants"] = st.session_state.favorites
                                save_user_data(user_data)
                                st.rerun()# Fonction pour extraire les tags pertinents d'un restaurant

def extract_restaurant_tags(restaurant_text):
    """Extrait des tags pertinents depuis le texte descriptif d'un restaurant"""
    # Cette fonction serait plus sophistiquée avec NLP
    # Ici, c'est une simulation simplifiée
    
    tags = []
    
    # Dictionnaire de termes à chercher et leurs tags associés
    tag_dictionary = {
        'romantique': 'Romantique',
        'intime': 'Romantique',
        'couple': 'Romantique',
        'calme': 'Calme',
        'tranquille': 'Calme',
        'familial': 'Familial',
        'famille': 'Familial',
        'enfant': 'Familial',
        'convivial': 'Convivial',
        'ambiance': 'Bonne ambiance',
        'animé': 'Animé',
        'festif': 'Festif',
        'brunch': 'Brunch',
        'terrasse': 'Terrasse',
        'vue': 'Belle vue',
        'rapide': 'Service rapide',
        'business': 'Business',
        'travail': 'Business',
        'original': 'Original',
        'créatif': 'Créatif',
        'moderne': 'Moderne',
        'traditionnel': 'Traditionnel',
        'authentique': 'Authentique',
        'vintage': 'Vintage',
        'végétarien': 'Options végétariennes',
        'végan': 'Options véganes',
        'sans gluten': 'Sans gluten'
    }
    
    # Texte en minuscules pour la comparaison
    text_lower = restaurant_text.lower()
    
    # Rechercher les termes
    for term, tag in tag_dictionary.items():
        if term in text_lower and tag not in tags:
            tags.append(tag)
    
    return tags

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
                        "prix_fourchette": ["€€-€€€"],
                        "note_moyenne": 4.2
                    }
                }
            ]
        }
        with open("user_data.json", "w") as f:
            json.dump(default_user_data, f)
    
    main()