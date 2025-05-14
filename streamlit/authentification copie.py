import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Mon Album Photo", layout="wide")

# Initialisation des variables de session
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Charger les données utilisateurs
def load_users():
    try:
        return pd.read_csv('fichier.csv')
    except:
        return pd.DataFrame({
            'name': ['root'],
            'password': ['admin'],
            'email': ['admin@example.com'],
            'failed_login_attempts': [0],
            'logged_in': [False],
            'role': ['admin']
        })

# Fonction d'authentification
def authenticate(username, password):
    users = load_users()
    user = users[users['name'] == username]
    if not user.empty:
        if user.iloc[0]['password'] == password:
            return True
    return False

# Sidebar (toujours présente)
with st.sidebar:
    if st.session_state.logged_in:
        st.write(f"Bienvenue {st.session_state.username}")
        if st.button("Déconnexion"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
        
        # Menu uniquement si connecté
        st.radio("Navigation", ["Accueil", "Les photos de mon chat"], key='navigation')

# Contenu principal
if not st.session_state.logged_in:
    st.title("Login")
    col1, col2 = st.columns([1, 2])
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Username ou mot de passe incorrect")
        
        if username == "" or password == "":
            st.warning("Les champs username et mot de passe doivent être remplis")

else:
    if st.session_state.get('navigation') == "Accueil":
        st.title("Bienvenue sur ma page")
        st.image("https://static.streamlit.io/examples/crowd.jpg")
        
    elif st.session_state.get('navigation') == "Les photos de mon chat":
        st.title("Bienvenue dans l'album de mon chat 🐱")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.image("https://static.streamlit.io/examples/cat.jpg")
        with col2:
            st.image("https://static.streamlit.io/examples/dog.jpg")
        with col3:
            st.image("https://static.streamlit.io/examples/owl.jpg")