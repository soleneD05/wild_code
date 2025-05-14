# app.py
import streamlit as st
import pandas as pd
import os
from PIL import Image
import hashlib

# Configuration de la page
st.set_page_config(page_title="Mon Album Photo", layout="wide")

# Fonction pour charger les données utilisateurs
@st.cache_data
def load_users():
    try:
        return pd.read_csv('users.csv')
    except:
        # Créer un DataFrame par défaut si le fichier n'existe pas
        df = pd.DataFrame({
            'name': ['root'],
            'password': [hashlib.sha256('admin'.encode()).hexdigest()],
            'email': ['admin@example.com'],
            'failed_login_attempts': [0],
            'logged_in': [False],
            'role': ['admin']
        })
        df.to_csv('users.csv', index=False)
        return df

# Fonction de hachage pour le mot de passe
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Fonction d'authentification
def authenticate(username, password):
    users = load_users()
    user = users[users['name'] == username]
    if not user.empty:
        if user.iloc[0]['password'] == hash_password(password):
            users.loc[users['name'] == username, 'logged_in'] = True
            users.to_csv('users.csv', index=False)
            return True
    return False

# Gestion de la session
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

# Sidebar
with st.sidebar:
    if st.session_state.logged_in:
        st.write(f"Bienvenue {st.session_state.username}")
        if st.button("Déconnexion"):
            st.session_state.logged_in = False
            st.session_state.username = None
            users = load_users()
            users.loc[users['name'] == st.session_state.username, 'logged_in'] = False
            users.to_csv('users.csv', index=False)
            st.experimental_rerun()
        
        # Menu
        page = st.radio("Navigation", ["Accueil", "Les photos de mon chat"])

# Page de login
if not st.session_state.logged_in:
    st.title("Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.experimental_rerun()
        else:
            st.error("Username ou mot de passe incorrect")
            
    # Message d'erreur si les champs sont vides
    if username == "" or password == "":
        st.warning("Les champs username et mot de passe doivent être remplis")

# Pages principales
else:
    if 'page' not in locals():
        page = "Accueil"
        
    if page == "Accueil":
        st.title("Bienvenue sur ma page")
        st.image("https://static.streamlit.io/examples/crowd.jpg")
        
    elif page == "Les photos de mon chat":
        st.title("Bienvenue dans l'album de mon chat 🐱")
        
        # Création de 3 colonnes pour les images
        col1, col2, col3 = st.columns(3)
        
        # Images dans les colonnes
        with col1:
            st.image("https://static.streamlit.io/examples/cat.jpg")
        
        with col2:
            st.image("https://placekitten.com/400/400")
            
        with col3:
            st.image("https://placekitten.com/401/401")