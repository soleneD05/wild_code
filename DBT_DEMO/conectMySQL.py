import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

# Paramètres de connexion.
username = "root"
password = "xx"
host = "localhost"
port = 3306
database = "my_dbt_db"

# On créée la connexion vers la base de données.
DATABASE_URI = f'mysql+pymysql://{username}:{password}@{host}:{port}/{database}'
engine = create_engine(DATABASE_URI)

# On créée la base de données si elle n'existe pas.
if not database_exists(engine.url):
    create_database(engine.url)

# On créée un DataFrame pour chaque fichier CSV de la base de données.
liste_tables = ["customers", "items", "orders", "products", "stores", "supplies"]

for table in liste_tables:
    csv_url = f"https://raw.githubusercontent.com/dsteddy/jaffle_shop_data/main/raw_{table}.csv"
    df = pd.read_csv(csv_url)
    # On ajoute les informations de de dataframe à la table dans MySQL.
    df.to_sql(f"raw_{table}", engine, if_exists="replace", index=False)