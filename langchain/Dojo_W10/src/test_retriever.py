import os
from langchain.schema import Document
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import Chroma

API_KEY = "iE3A20aMxy6Cg0EfYW1Fj2fxcr3VCqHr"

def main():
    documents = [
        Document(page_content="Une infection pulmonaire est une inflammation des poumons causée par un agent pathogène."),
        Document(page_content="Le traitement dépend du type d'infection et de la gravité des symptômes."),
        Document(page_content="Les antibiotiques sont souvent prescrits pour les infections bactériennes."),
    ]

    embedding = MistralAIEmbeddings(model="mistral-embed", mistral_api_key=API_KEY)

    vectordb = Chroma.from_documents(
        documents=documents,
        embedding=embedding,
        persist_directory=None
    )

    retriever = vectordb.as_retriever()

    query = "Qu'est-ce qu'une infection pulmonaire ?"

    try:
        results = retriever.invoke(query)
        print(f"✅ Résultats pour la requête '{query}':")
        for i, doc in enumerate(results):
            print(f"{i+1}. {doc.page_content}")
    except Exception as e:
        print("❌ Erreur lors de la récupération des documents :", e)

if __name__ == "__main__":
    main()
