import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Chargement des données 
def load_data():
    url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/mpg.csv"
    df = pd.read_csv(url)
    return df

df = load_data()

# Titre
st.title("🚘 Analyse des voitures : Corrélations et Distributions")

# Boutons de filtrage par région
region = st.radio("Sélectionner une région :", ["⭐️ Toutes", "🇺🇸 US", "🇪🇺 Europe", "🇯🇵 Japon"])

if region != "Toutes":
    if region == "US":
        df = df[df['origin'] == 'usa']
    elif region == "Europe":
        df = df[df['origin'] == 'europe']
    else:
        df = df[df['origin'] == 'japan']

# Affichage des données
st.write("Aperçu des données :", df.head())

# Analyse de corrélation
st.subheader("Matrice de Corrélation")
plt.figure(figsize=(8, 6))
sns.heatmap(df.corr(), annot=True, cmap='coolwarm', fmt='.2f')
st.pyplot(plt)

# Distribution des variables principales
st.subheader("Distribution des variables")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
sns.histplot(df['mpg'], bins=20, kde=True, ax=axes[0])
axes[0].set_title("Distribution du MPG")
sns.histplot(df['horsepower'].dropna(), bins=20, kde=True, ax=axes[1])
axes[1].set_title("Distribution des chevaux (horsepower)")
st.pyplot(fig)
