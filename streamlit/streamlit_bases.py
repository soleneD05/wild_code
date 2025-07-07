import streamlit as st
import os

# Titre du site
st.title("Bienvenue sur le site web de Solène")

# Chemin du dossier contenant les images
image_folder = "image"

# Liste des arrondissements et noms des fichiers d'image associés
arrondissements = {
    "Brooklyn": "brooklyn.jpg",
    "Bronx": "bronx.jpg",
    "Manhattan": "manhattan.jpg",
    "Queens": "queens.jpg",
    "nan": None
}

# Sélection de l'arrondissement
arrondissement = st.selectbox(
    "Indiquez votre arrondissement de récupération :",
    ["Brooklyn", "Bronx", "Manhattan", "Queens", "nan"]
)

# Afficher le choix de l'utilisateur
st.write(f"Vous avez choisi : **{arrondissement}**")

# Afficher l'image de l'arrondissement choisi
if arrondissements[arrondissement]:
    image_path = os.path.join(image_folder, arrondissements[arrondissement])
    if os.path.exists(image_path):
        st.image(image_path)
    else:
        st.write("Image non trouvée pour cet arrondissement.")
else:
    st.write("Veuillez sélectionner un arrondissement valide.")
