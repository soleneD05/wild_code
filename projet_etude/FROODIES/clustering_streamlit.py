import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from scipy.sparse import hstack, csr_matrix
import re
import warnings

# Ignorer les avertissements
warnings.filterwarnings('ignore')

# Fonction de prétraitement des données
def preprocess_data(df):
    """Prétraite les données pour le clustering"""
    df = df.copy()
    
    # Traitement des arrondissements
    if 'arrondissement' in df.columns:
        df['arrondissement'] = df['arrondissement'].astype(str)
        df['arrondissement_num'] = df['arrondissement'].apply(
            lambda x: re.search(r'750(\d{2})', x).group(1) if re.search(r'750(\d{2})', x) else x
        )
    else:
        df['arrondissement'] = ""
        df['arrondissement_num'] = ""
    
    # Traitement des prix
    if 'prix_fourchette' in df.columns:
        if df['prix_fourchette'].dtype == 'object':
            df['prix_num'] = df['prix_fourchette'].apply(
                lambda x: np.mean([float(n) for n in str(x).replace('€','').split('-')]) 
                if isinstance(x, str) and '-' in x 
                else float(str(x).replace('€','')) if pd.notnull(x) and str(x).replace('€','').replace('.','').isdigit() 
                else np.nan
            )
        else:
            df['prix_num'] = df['prix_fourchette']
    else:
        df['prix_num'] = np.nan
    
    # Traitement des notes
    for col in ['note_moyenne', 'qualite_nourriture']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = np.nan
    
    # Traitement des textes
    text_cols = ['type_cuisine', 'specialite', 'ambiance']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.lower()
        else:
            df[col] = [""] * len(df)
    
    # Traitement de la reconnaissance
    if 'reconnaissance' in df.columns:
        df['reconnaissance'] = df['reconnaissance'].fillna("Aucune").astype(str)
        # Échelle numérique pour la reconnaissance
        reconnaissance_map = {
            'aucune': 0, 
            'recommandé': 1,
            'bib gourmand': 2, 
            'une étoile': 3, 
            'deux étoiles': 4, 
            'trois étoiles': 5
        }
        df['reconnaissance_score'] = df['reconnaissance'].str.lower().map(
            lambda x: next((v for k, v in reconnaissance_map.items() if k in x), 0)
        )
    else:
        df['reconnaissance'] = "Aucune"
        df['reconnaissance_score'] = 0
    
    return df

# Fonction de clustering
def cluster_restaurants(df, n_clusters=5):
    """Version simplifiée du clustering"""
    df_processed = preprocess_data(df)
    
    # Préparation des features textuelles
    text_data = df_processed['type_cuisine'] + " " + df_processed['specialite'] + " " + df_processed['ambiance']
    
    # Utiliser un vectoriseur TF-IDF pour les données textuelles
    tfidf = TfidfVectorizer(max_features=50)
    X_text = tfidf.fit_transform(text_data)
    
    # Préparation des features numériques
    num_cols = ['prix_num', 'note_moyenne', 'qualite_nourriture', 'reconnaissance_score']
    available_num_cols = [col for col in num_cols if col in df_processed.columns]
    
    if available_num_cols:
        # Imputation des valeurs manquantes
        num_data = df_processed[available_num_cols].copy()
        imputer = SimpleImputer(strategy='mean')
        X_num = imputer.fit_transform(num_data)
        
        # Standardisation
        scaler = StandardScaler()
        X_num_scaled = scaler.fit_transform(X_num)
        X_num_sparse = csr_matrix(X_num_scaled)
        
        # Fusion des features textuelles et numériques
        X = hstack([X_text, X_num_sparse])
    else:
        X = X_text
    
    # Remplacement des NaN éventuels
    if hasattr(X, 'data'):
        X.data = np.nan_to_num(X.data)
    
    # Application de K-means avec n_init défini explicitement pour les versions plus récentes de scikit-learn
    try:
        # Pour scikit-learn >= 1.0
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, algorithm='elkan')
    except TypeError:
        # Pour les versions antérieures de scikit-learn
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    
    # Fitting du modèle
    try:
        df_processed['cluster'] = kmeans.fit_predict(X)
    except Exception as e:
        st.error(f"Erreur lors du clustering K-means: {e}")
        
        # Alternative plus simple si K-means échoue
        if X.shape[0] > 10000:  # Si le dataset est très grand
            # Utiliser un échantillon pour trouver les centroïdes
            sample_idx = np.random.choice(X.shape[0], min(5000, X.shape[0]), replace=False)
            X_sample = X[sample_idx]
            kmeans.fit(X_sample)
            # Assigner des clusters aux points complets
            df_processed['cluster'] = kmeans.predict(X)
        else:
            # Tenter avec moins de features
            if X.shape[1] > 20:
                # Réduire les dimensions avec PCA
                pca = PCA(n_components=20)
                X_dense = X.toarray() if hasattr(X, 'toarray') else X
                X_reduced = pca.fit_transform(X_dense)
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                df_processed['cluster'] = kmeans.fit_predict(X_reduced)
            else:
                # En dernier recours, assigner des clusters aléatoires
                df_processed['cluster'] = np.random.randint(0, n_clusters, size=len(df_processed))
    
    # Analyse des clusters pour nommer chaque cluster
    cluster_stats = {}
    for cluster_id in range(n_clusters):
        cluster_data = df_processed[df_processed['cluster'] == cluster_id]
        
        if len(cluster_data) == 0:
            continue
            
        # Statistiques de base
        price_mean = cluster_data['prix_num'].mean() if 'prix_num' in cluster_data else np.nan
        rating_mean = cluster_data['note_moyenne'].mean() if 'note_moyenne' in cluster_data else np.nan
        
        # Top cuisines
        top_cuisines = []
        if 'type_cuisine' in cluster_data.columns:
            top_cuisines = cluster_data['type_cuisine'].value_counts().head(3).index.tolist()
        
        # Nommer le cluster
        features = []
        
        if not np.isnan(price_mean):
            if price_mean < 20:
                features.append("Économique")
            elif price_mean < 40:
                features.append("Milieu de gamme")
            else:
                features.append("Haut de gamme")
        
        if not np.isnan(rating_mean) and rating_mean > 4.2:
            features.append("Bien noté")
        
        if top_cuisines:
            features.append(top_cuisines[0].capitalize())
        
        cluster_name = " & ".join(features[:3]) if features else f"Cluster {cluster_id}"
        cluster_stats[cluster_id] = {
            'name': cluster_name,
            'count': len(cluster_data),
            'price_mean': price_mean,
            'rating_mean': rating_mean,
            'top_cuisines': top_cuisines
        }
    
    # Assigner les noms de clusters au dataframe
    df_processed['cluster_name'] = df_processed['cluster'].map(lambda x: cluster_stats.get(x, {}).get('name', f"Cluster {x}"))
    
    return df_processed, cluster_stats

# Fonction pour obtenir des recommandations
def get_recommendations(df_clustered, restaurant_name, n_recommendations=3):
    """Obtenir des recommandations de restaurants similaires"""
    # Trouver le cluster du restaurant sélectionné
    selected_restaurant = df_clustered[df_clustered['nom'] == restaurant_name]
    
    if len(selected_restaurant) == 0:
        return pd.DataFrame()  # Restaurant non trouvé
    
    cluster_id = selected_restaurant['cluster'].iloc[0]
    
    # Obtenir d'autres restaurants du même cluster
    similar_restaurants = df_clustered[
        (df_clustered['cluster'] == cluster_id) & 
        (df_clustered['nom'] != restaurant_name)
    ]
    
    # Trier par note et retourner les n meilleurs
    if 'note_moyenne' in similar_restaurants.columns:
        recommendations = similar_restaurants.sort_values('note_moyenne', ascending=False).head(n_recommendations)
    else:
        recommendations = similar_restaurants.sample(min(n_recommendations, len(similar_restaurants)))
    
    return recommendations

# Fonction pour afficher un restaurant
def display_restaurant_card(restaurant):
    """Affiche les informations d'un restaurant dans une carte"""
    with st.container():
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Afficher une icône ou un emoji selon le type de cuisine
            if 'type_cuisine' in restaurant:
                cuisine = restaurant['type_cuisine']
                emoji = "🍽️"  # Emoji par défaut
                
                # Attribuer un emoji selon le type de cuisine
                cuisine_emojis = {
                    'française': '🐓',
                    'italienne': '🍕',
                    'japonaise': '🍣',
                    'chinoise': '🥢',
                    'indienne': '🍛',
                    'mexicaine': '🌮',
                    'libanaise': '🧆',
                    'américaine': '🍔',
                    'espagnole': '🥘',
                    'thaïlandaise': '🍲',
                    'végétarienne': '🥗',
                    'végane': '🌱'
                }
                
                for key, value in cuisine_emojis.items():
                    if key in str(cuisine).lower():
                        emoji = value
                        break
                
                st.markdown(f"<h1 style='text-align: center; font-size: 3em;'>{emoji}</h1>", unsafe_allow_html=True)
        
        with col2:
            # Nom du restaurant
            if 'nom' in restaurant:
                st.markdown(f"### {restaurant['nom']}")
            
            # Type de cuisine
            if 'type_cuisine' in restaurant and restaurant['type_cuisine']:
                st.write(f"**Cuisine :** {restaurant['type_cuisine'].capitalize()}")
            
            # Prix
            if 'prix_num' in restaurant and not np.isnan(restaurant['prix_num']):
                prix = restaurant['prix_num']
                price_str = "€" * min(5, max(1, int(prix / 20))) if prix > 0 else "€"
                st.write(f"**Prix moyen :** {price_str} ({prix:.0f}€)")
            
            # Note
            if 'note_moyenne' in restaurant and not np.isnan(restaurant['note_moyenne']):
                note = restaurant['note_moyenne']
                stars = "★" * int(note) + "☆" * (5 - int(note))
                st.write(f"**Note :** {stars} ({note}/5)")
            
            # Adresse
            if 'arrondissement' in restaurant and restaurant['arrondissement']:
                st.write(f"**Arrondissement :** {restaurant['arrondissement']}")
            
            # Ambiance
            if 'ambiance' in restaurant and restaurant['ambiance']:
                st.write(f"**Ambiance :** {restaurant['ambiance'].capitalize()}")
        
        st.markdown("---")

# Application Streamlit
def main():
    st.set_page_config(
        page_title="Froodies - Recommandation de Restaurants",
        page_icon="🍽️",
        layout="wide"
    )
    
    st.title("🍽️ Froodies - Découvrez des restaurants similaires")
    st.markdown("Sélectionnez un restaurant que vous aimez pour découvrir des recommandations similaires!")
    
    # Chargement des données
    try:
        file_path = "paris_restaurants_enrichi.csv"
        df = pd.read_csv(file_path)
        
        # Vérifier si les clusters existent déjà dans le fichier
        if 'cluster' not in df.columns:
            with st.spinner("Analyse en cours... Veuillez patienter."):
                df_clustered, cluster_stats = cluster_restaurants(df, n_clusters=5)
        else:
            df_clustered = df
            # Créer des statistiques minimales pour l'affichage
            cluster_stats = {}
            for cluster_id in df_clustered['cluster'].unique():
                cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]
                cluster_name = cluster_data['cluster_name'].iloc[0] if 'cluster_name' in cluster_data else f"Cluster {cluster_id}"
                cluster_stats[cluster_id] = {
                    'name': cluster_name,
                    'count': len(cluster_data)
                }
        
        # Sélectionner 3 restaurants populaires aléatoirement
        if 'note_moyenne' in df_clustered.columns:
            # Filtrer les restaurants avec une bonne note
            popular_restaurants = df_clustered[df_clustered['note_moyenne'] >= 4.0]
            if len(popular_restaurants) < 3:
                popular_restaurants = df_clustered  # Fallback si pas assez de restaurants bien notés
        else:
            popular_restaurants = df_clustered
        
        # Sélectionner 3 restaurants aléatoires parmi les populaires
        sample_size = min(3, len(popular_restaurants))
        featured_restaurants = popular_restaurants.sample(sample_size)
        
        # Afficher les trois restaurants proposés
        st.subheader("📍 Choisissez un restaurant que vous aimez")
        
        # Diviser en 3 colonnes pour les restaurants à choisir
        cols = st.columns(sample_size)
        
        for i, (_, restaurant) in enumerate(featured_restaurants.iterrows()):
            with cols[i]:
                with st.container():
                    # Nom du restaurant
                    if 'nom' in restaurant:
                        st.markdown(f"### {restaurant['nom']}")
                    
                    # Type de cuisine
                    if 'type_cuisine' in restaurant and restaurant['type_cuisine']:
                        st.write(f"**Cuisine :** {restaurant['type_cuisine'].capitalize()}")
                    
                    # Prix
                    if 'prix_num' in restaurant and not np.isnan(restaurant['prix_num']):
                        prix = restaurant['prix_num']
                        price_str = "€" * min(5, max(1, int(prix / 20))) if prix > 0 else "€"
                        st.write(f"**Prix moyen :** {price_str} ({prix:.0f}€)")
                    
                    # Note
                    if 'note_moyenne' in restaurant and not np.isnan(restaurant['note_moyenne']):
                        note = restaurant['note_moyenne']
                        stars = "★" * int(note) + "☆" * (5 - int(note))
                        st.write(f"**Note :** {stars} ({note}/5)")
                    
                    # Bouton pour choisir ce restaurant
                    if st.button(f"Choisir", key=f"btn_{i}"):
                        st.session_state.selected_restaurant = restaurant['nom']
                        try:
                            st.rerun()  # Nouvelle méthode dans Streamlit récent
                        except:
                            try:
                                st.experimental_rerun()  # Ancienne méthode
                            except:
                                st.warning("Veuillez actualiser la page pour voir les recommandations.")
        
        # Si un restaurant est sélectionné, afficher les recommandations
        if 'selected_restaurant' in st.session_state:
            selected_name = st.session_state.selected_restaurant
            
            # Afficher le restaurant sélectionné
            st.markdown("---")
            st.subheader("🎯 Votre choix")
            
            selected_restaurant = df_clustered[df_clustered['nom'] == selected_name].iloc[0]
            display_restaurant_card(selected_restaurant)
            
            # Obtenir des recommandations
            recommendations = get_recommendations(df_clustered, selected_name, n_recommendations=3)
            
            if len(recommendations) > 0:
                st.subheader("✨ Recommandations similaires")
                
                # Afficher le cluster du restaurant
                cluster_id = selected_restaurant['cluster']
                cluster_name = cluster_stats.get(cluster_id, {}).get('name', f"Cluster {cluster_id}")
                
                st.info(f"Ces recommandations font partie du même univers culinaire : **{cluster_name}**")
                
                # Afficher les recommandations
                for _, restaurant in recommendations.iterrows():
                    display_restaurant_card(restaurant)
            else:
                st.warning("Désolé, nous n'avons pas trouvé de restaurants similaires.")
            
            # Bouton pour réinitialiser le choix
            if st.button("Choisir un autre restaurant"):
                del st.session_state.selected_restaurant
                try:
                    st.rerun()  # Nouvelle méthode dans Streamlit récent
                except:
                    try:
                        st.experimental_rerun()  # Ancienne méthode
                    except:
                        st.warning("Veuillez actualiser la page pour revenir à la sélection.")
            
    except Exception as e:
        st.error(f"Une erreur s'est produite: {str(e)}")
        st.info("Vérifiez que le fichier 'paris_restaurants_enrichi.csv' est présent dans le répertoire.")

if __name__ == "__main__":
    main()