from langchain_mistralai import MistralAIEmbeddings

# Remplace par ta clé réelle
API_KEY = "iE3A20aMxy6Cg0EfYW1Fj2fxcr3VCqHr"  # ← ajoute ici ta clé Mistral

# Instanciation de l'embedding
embedding = MistralAIEmbeddings(model="mistral-embed", mistral_api_key=API_KEY)

try:
    # Test simple
    result = embedding.embed_query("Bonjour, comment ça va ?")
    print("✅ Embedding réussi !")
    print("Premier vecteur :", result[:5])  # On affiche les premiers éléments
except Exception as e:
    print("❌ Erreur pendant l'embedding :")
    print(e)
