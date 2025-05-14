import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

# Configuration pour les graphiques
try:
    import seaborn as sns
    sns.set_style("whitegrid")
except:
    pass
plt.rcParams['figure.figsize'] = [12, 8]

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

def cluster_restaurants(df, n_clusters=5):
    """Version simplifiée du clustering pour éviter les problèmes de threadpool"""
    print("Prétraitement des données...")
    df_processed = preprocess_data(df)
    
    # Préparation des features textuelles
    print("Traitement des données textuelles...")
    text_data = df_processed['type_cuisine'] + " " + df_processed['specialite'] + " " + df_processed['ambiance']
    
    # Utiliser un vectoriseur TF-IDF pour les données textuelles
    tfidf = TfidfVectorizer(max_features=50)  # Réduit pour éviter les problèmes de mémoire
    X_text = tfidf.fit_transform(text_data)
    
    # Préparation des features numériques
    print("Traitement des données numériques...")
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
    print(f"Application de K-means avec {n_clusters} clusters...")
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
        print(f"Erreur lors du clustering K-means: {e}")
        print("Tentative de clustering avec une méthode alternative...")
        
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
            print("Tentative avec moins de features...")
            if X.shape[1] > 20:
                # Réduire les dimensions avec PCA
                pca = PCA(n_components=20)
                X_dense = X.toarray() if hasattr(X, 'toarray') else X
                X_reduced = pca.fit_transform(X_dense)
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                df_processed['cluster'] = kmeans.fit_predict(X_reduced)
            else:
                # En dernier recours, assigner des clusters aléatoires
                print("Problème persistant, assignation de clusters aléatoires...")
                df_processed['cluster'] = np.random.randint(0, n_clusters, size=len(df_processed))
    
    # Réduction de dimension pour visualisation
    print("Création de visualisation...")
    try:
        pca = PCA(n_components=2)
        X_dense = X.toarray() if hasattr(X, 'toarray') else X
        X_reduced = pca.fit_transform(X_dense)
        df_processed['x'] = X_reduced[:, 0]
        df_processed['y'] = X_reduced[:, 1]
    except Exception as e:
        print(f"Erreur lors de la réduction de dimension: {e}")
        # Coordonnées par défaut en cas d'erreur
        df_processed['x'] = np.random.normal(0, 1, size=len(df_processed))
        df_processed['y'] = np.random.normal(0, 1, size=len(df_processed))
    
    # Analyse des clusters
    cluster_stats = []
    for cluster_id in range(n_clusters):
        cluster_data = df_processed[df_processed['cluster'] == cluster_id]
        
        if len(cluster_data) == 0:
            continue
            
        # Statistiques de base
        stats = {
            'cluster_id': cluster_id,
            'count': len(cluster_data),
            'price_mean': cluster_data['prix_num'].mean() if 'prix_num' in cluster_data else np.nan,
            'rating_mean': cluster_data['note_moyenne'].mean() if 'note_moyenne' in cluster_data else np.nan
        }
        
        # Top cuisines
        if 'type_cuisine' in cluster_data.columns:
            top_cuisines = cluster_data['type_cuisine'].value_counts().head(3).index.tolist()
            stats['top_cuisines'] = top_cuisines
        
        # Nommer le cluster
        features = []
        
        if not np.isnan(stats.get('price_mean', np.nan)):
            if stats['price_mean'] < 20:
                features.append("Économique")
            elif stats['price_mean'] < 40:
                features.append("Milieu de gamme")
            else:
                features.append("Haut de gamme")
        
        if not np.isnan(stats.get('rating_mean', np.nan)) and stats['rating_mean'] > 4.2:
            features.append("Bien noté")
        
        if 'top_cuisines' in stats and stats['top_cuisines']:
            features.append(stats['top_cuisines'][0].capitalize())
        
        stats['name'] = " & ".join(features[:3]) if features else f"Cluster {cluster_id}"
        cluster_stats.append(stats)
    
    # Assigner les noms de clusters au dataframe
    cluster_name_map = {stat['cluster_id']: stat['name'] for stat in cluster_stats}
    df_processed['cluster_name'] = df_processed['cluster'].map(lambda x: cluster_name_map.get(x, f"Cluster {x}"))
    
    return df_processed, cluster_stats

def main():
    print("CLUSTERING DE RESTAURANTS PARISIENS (VERSION SIMPLIFIÉE)")
    print("-" * 50)
    
    # Chargement des données
    print("Chargement des données...")
    file_path = "paris_restaurants_enrichi.csv"
    try:
        df = pd.read_csv(file_path)
        print(f"Données chargées avec succès: {len(df)} restaurants")
    except Exception as e:
        print(f"Erreur lors du chargement des données: {str(e)}")
        print("Vérifiez que le fichier 'paris_restaurants_enrichi.csv' existe dans le répertoire courant.")
        return
    
    # Aperçu des données
    print("\nAperçu des colonnes:")
    for col in df.columns:
        missing = df[col].isnull().sum()
        pct_missing = (missing / len(df)) * 100
        print(f"- {col}: {missing} valeurs manquantes ({pct_missing:.1f}%)")
    
    # Nombre de clusters
    n_clusters = 5
    print(f"\nClustering avec {n_clusters} clusters...")
    
    # Exécution du clustering
    try:
        df_clustered, cluster_stats = cluster_restaurants(df, n_clusters)
        
        # Affichage des résultats
        print("\n" + "="*50)
        print("RÉSULTATS DU CLUSTERING")
        print("="*50)
        
        for stats in cluster_stats:
            print(f"\nCluster {stats['cluster_id']}: {stats['name']} ({stats['count']} restaurants)")
            print("-" * 40)
            if 'price_mean' in stats and not np.isnan(stats['price_mean']):
                print(f"Prix moyen: {stats['price_mean']:.2f} €")
            if 'rating_mean' in stats and not np.isnan(stats['rating_mean']):
                print(f"Note moyenne: {stats['rating_mean']:.2f}/5")
            if 'top_cuisines' in stats:
                print(f"Cuisines dominantes: {', '.join([c.capitalize() for c in stats['top_cuisines']])}")
        
        # Sauvegarde des résultats
        output_file = "restaurants_clusters_simple.csv"
        df_clustered.to_csv(output_file, index=False)
        print(f"\nRésultats sauvegardés dans {output_file}")
        
        # Visualisation simple
        plt.figure(figsize=(12, 8))
        for cluster_id in range(n_clusters):
            cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]
            if not cluster_data.empty:
                plt.scatter(
                    cluster_data['x'], 
                    cluster_data['y'], 
                    s=50, 
                    alpha=0.7,
                    label=f"{cluster_data['cluster_name'].iloc[0]} ({len(cluster_data)})"
                )
        
        plt.title("Clustering des restaurants parisiens", fontsize=16)
        plt.xlabel("Dimension 1", fontsize=12)
        plt.ylabel("Dimension 2", fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        # Sauvegarde du graphique
        plt.savefig("clusters_restaurants.png", dpi=300, bbox_inches='tight')
        print("Visualisation sauvegardée dans clusters_restaurants.png")
        
        # Afficher quelques exemples de restaurants par cluster
        print("\nEXEMPLES DE RESTAURANTS PAR CLUSTER:")
        for cluster_id in range(n_clusters):
            cluster_examples = df_clustered[df_clustered['cluster'] == cluster_id].head(3)
            if not cluster_examples.empty:
                cluster_name = cluster_examples['cluster_name'].iloc[0]
                print(f"\nCluster {cluster_id}: {cluster_name}")
                for _, row in cluster_examples.iterrows():
                    restaurant_info = []
                    if 'nom' in row:
                        restaurant_info.append(f"{row['nom']}")
                    if 'type_cuisine' in row and row['type_cuisine']:
                        restaurant_info.append(f"{row['type_cuisine'].capitalize()}")
                    if 'prix_num' in row and not np.isnan(row['prix_num']):
                        restaurant_info.append(f"{row['prix_num']:.0f}€")
                    if 'note_moyenne' in row and not np.isnan(row['note_moyenne']):
                        restaurant_info.append(f"{row['note_moyenne']}/5")
                    
                    print(f"- {' | '.join(restaurant_info)}")
        
    except Exception as e:
        print(f"Erreur lors du clustering: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()