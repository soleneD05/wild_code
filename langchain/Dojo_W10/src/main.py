import os
from dotenv import load_dotenv
import tempfile
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_mistralai import MistralAIEmbeddings
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Vérifier les clés
load_dotenv()

# 1.Document_loader & Text_Splitter
def load_and_split_file(uploaded_file, chunk_size: int = 500, chunk_overlap: int = 50):
    extension = os.path.splitext(uploaded_file.name)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name
    
    if extension == ".pdf":
        loader = PyPDFLoader(tmp_path)
    elif extension == ".txt":
        loader = TextLoader(tmp_path, encoding="utf-8")
    elif extension == ".docx":
        loader = Docx2txtLoader(tmp_path)
    else:
        raise ValueError(
            f"Format du fichier est {extension}, il faut être en PDF, TXT ou DOCX."
        )
    
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', '', ' ', '.', ','],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False
    )
    docs_split = splitter.split_documents(docs)
    return docs_split

def create_vetordb(chunks, api_key):
    # CORRECTION: Utiliser les bons paramètres comme dans votre code qui fonctionne
    embeddings = MistralAIEmbeddings(
        model="mistral-embed", 
        mistral_api_key=api_key
    )
    vectordb = Chroma.from_documents(chunks, embedding=embeddings)
    return vectordb

def get_retriever(vectordb: Chroma, top_k: int = 3):
    retriever = vectordb.as_retriever(search_kwargs={"k": top_k})
    return retriever

def get_chain(retriever, api_key):
    # Liste des modèles par ordre de préférence (du plus accessible au plus performant)
    models_to_try = [
        "open-mistral-7b",
        "mistral-tiny", 
        "mistral-small-latest",
        "mistral-medium-latest"
    ]
    
    llm = None
    for model in models_to_try:
        try:
            llm = ChatMistralAI(
                api_key=api_key,
                model=model,
                temperature=0.3
            )
            # Test simple pour vérifier que le modèle fonctionne
            print(f"✅ Utilisation du modèle: {model}")
            break
        except Exception as e:
            print(f"Modèle {model} non accessible: {str(e)}")
            continue
    
    if llm is None:
        raise Exception("Aucun modèle Mistral accessible avec votre clé API")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Tu réponds des questions de manière directe et claire. "
         "Appuie-toi seulement sur les informations fournies dans la documentation. "
         "Ne commence jamais par des formules de politesse. "
         "Ne dis pas 'Voici ce que j'ai trouvé', 'D'après la documentation', etc. Donne directement les informations demandées."
        ),
        ("human",
         "Voici ma question : {question}. Je te fournis ci-dessous la documentation : {context}")
    ])
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain
    
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Tu réponds des questions de manière directe et claire. "
         "Appuie-toi seulement sur les informations fournies dans la documentation. "
         "Ne commence jamais par des formules de politesse. "
         "Ne dis pas 'Voici ce que j'ai trouvé', 'D'après la documentation', etc. Donne directement les informations demandées."
        ),
        ("human",
         "Voici ma question : {question}. Je te fournis ci-dessous la documentation : {context}")
    ])
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain

def run_chain(chain, question):
    # CORRECTION: Simplifier l'appel de la chaîne
    return chain.invoke(question)