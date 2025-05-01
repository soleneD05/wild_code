import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import plotly.express as px
import plotly.graph_objects as go

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
            tooltip=row['nom']
        ).add_to(marker_cluster)
    
    return m

def main():
    # Chargement des données
    df = load_data()
    
    # Sidebar pour les filtres
    st.sidebar.title("🔍 Filtres de recherche")
    
    # Filtres
    price_filter = st.sidebar.multiselect(
        "Budget",
        options=sorted(df['prix_fourchette'].unique()),
        default=[]
    )
    
    cuisine_filter = st.sidebar.multiselect(
        "Type de cuisine",
        options=sorted(df['type_cuisine'].unique()),
        default=[]
    )
    
    arrond_filter = st.sidebar.multiselect(
        "Arrondissement",
        options=sorted(df['arrondissement'].unique()),
        default=[]
    )
    
    note_min = st.sidebar.slider(
        "Note minimum",
        min_value=float(df['note_moyenne'].min()),
        max_value=float(df['note_moyenne'].max()),
        value=4.0,
        step=0.1
    )
    
    # Filtrage des données
    mask = df['note_moyenne'] >= note_min
    
    if price_filter:
        mask &= df['prix_fourchette'].isin(price_filter)
    if cuisine_filter:
        mask &= df['type_cuisine'].isin(cuisine_filter)
    if arrond_filter:
        mask &= df['arrondissement'].isin(arrond_filter)
    
    df_filtered = df[mask]
    
    # Interface principale
    st.title("🍕FROODIES")
    st.markdown("Trouve ton resto préféré à Paris !")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Restaurants trouvés", len(df_filtered))
    with col2:
        st.metric("Note moyenne", f"{df_filtered['note_moyenne'].mean():.1f}/5")
    with col3:
        st.metric("Prix moyen", df_filtered['prix_fourchette'].mode()[0])
    with col4:
        st.metric("Cuisines différentes", df_filtered['type_cuisine'].nunique())
    
    # Onglets pour différentes vues
    tab1, tab2, tab3 = st.tabs(["🗺️ Carte", "📊 Statistiques", "📋 Liste"])
    
    # Onglet Carte
    with tab1:
        st.subheader("Carte des restaurants")
        map_fig = create_restaurant_map(df_filtered)
        folium_static(map_fig, width=1200)
    
    # Onglet Statistiques
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution des types de cuisine
            fig_cuisine = px.pie(
                df_filtered['type_cuisine'].value_counts().reset_index(),
                values='count',
                names='type_cuisine',
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
    
    # Onglet Liste
    with tab3:
        for idx, resto in df_filtered.iterrows():
            with st.expander(f"🍽️ {resto['nom']} - {resto['type_cuisine']}"):
                col1, col2 = st.columns([2,1])
                
                with col1:
                    st.markdown(f"**Adresse:** {resto['adresse']}")
                    st.markdown(f"**Spécialité:** {resto['specialite']}")
                    st.markdown(f"**Ambiance:** {resto['ambiance']}")
                    if resto['vegetarien_friendly']:
                        st.markdown("✅ Options végétariennes")
                    if resto['reservation_recommandee']:
                        st.markdown("📞 Réservation recommandée")
                
                with col2:
                    st.metric("Note", f"{resto['note_moyenne']}/5")
                    st.metric("Nombre d'avis", resto['nb_avis'])
                    st.markdown(f"**Prix:** {resto['prix_fourchette']}")

if __name__ == "__main__":
    main()