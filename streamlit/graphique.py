import streamlit as st
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Configuration de la page
st.title("Manipulation de données et création de graphiques")

# Liste des datasets disponibles dans seaborn
dataset_names = ["flights", "tips", "iris", "titanic", "diamonds"]
dataset = st.selectbox(
    "Quel dataset veux-tu utiliser :",
    dataset_names
)
# Charger le dataset sélectionné
df = sns.load_dataset(dataset)
st.write(f"Vous avez choisi le dataset : **{dataset}**")
st.dataframe(df.head())

# Sélection des colonnes
numerical_cols = df.select_dtypes(include=['float64', 'int64']).columns
categorical_cols = df.select_dtypes(include=['object', 'category']).columns
all_cols = df.columns

col_x = st.selectbox("Choisissez la colonne X", all_cols)
col_y = st.selectbox("Choisissez la colonne Y", numerical_cols)

# Sélection du type de graphique
chart_type = st.selectbox(
    "Quel graphique veux-tu utiliser?",
    ['scatter_chart', 'bar_chart', 'line_chart']
)

# Création du graphique
if chart_type == 'scatter_chart':
    st.scatter_chart(data=df, x=col_x, y=col_y)
elif chart_type == 'bar_chart':
    st.bar_chart(data=df, x=col_x, y=col_y)
else:
    st.line_chart(data=df, x=col_x, y=col_y)

# Option pour afficher la matrice de corrélation
show_corr = st.checkbox("Afficher la matrice de corrélation")

if show_corr:
    st.subheader("Ma matrice de corrélation")
    # Calculer la matrice de corrélation pour les colonnes numériques
    corr_matrix = df.select_dtypes(include=['float64', 'int64']).corr()
    
    # Créer la heatmap avec Matplotlib
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='YlOrBr', center=0, ax=ax)
    st.pyplot(fig)
