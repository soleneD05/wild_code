import streamlit as st
from main import load_and_split_file, create_vetordb, get_retriever, get_chain, run_chain

st.set_page_config(
    page_title="🧠 Dojo IA - Q&A sur documents",
    layout="wide"
)

# Page principale
st.title("🧠 Dojo IA - Q/R sur Documents")
question = st.text_input("❓ Posez votre question :")

# Sidebar
with st.sidebar:
    # Entrée de la clé API
    api_key = st.text_input("🔑 Entrez votre clé API:", type="password")
    
    # Upload de fichier(s) - MODIFIÉ pour accepter plusieurs fichiers
    uploaded_files = st.file_uploader(
        "📄 Importez un ou plusieurs documents (PDF, DOCX, TXT):", 
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True  # ✅ Permet plusieurs fichiers
    )
    
    # Paramètre : chunk size & Nb de documents à récuprérer
    chunk_size = st.slider("🧩 Taille des chunks", 100, 2000, 500, step=100)
    chunk_overlap = st.slider("🧩 Taille des chevauchement", 100, 500, 50, step=50)
    top_k = st.slider("📚 Nombre de documents à récupérer", 1, 10, 3)

# Initialisation
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if uploaded_files and api_key:
    try:
        # 1. Traitement et vectorisation de TOUS les fichiers
        with st.spinner(f"🔄 Traitement de {len(uploaded_files)} document(s)..."):
            all_chunks = []
            
            # Traitement de chaque fichier
            for i, uploaded_file in enumerate(uploaded_files, 1):
                st.write(f"📄 Traitement du fichier {i}/{len(uploaded_files)}: {uploaded_file.name}")
                chunks = load_and_split_file(uploaded_file, chunk_size, chunk_overlap)
                all_chunks.extend(chunks)  # Ajouter tous les chunks à la liste globale
            
            # Créer une base vectorielle avec TOUS les chunks
            vectordb = create_vetordb(all_chunks, api_key)
            retriever = get_retriever(vectordb, top_k)
            qa_chain = get_chain(retriever, api_key)
        
        st.success(f"✅ {len(uploaded_files)} document(s) traité(s) avec succès! ({len(all_chunks)} chunks au total)")
        
        # Afficher les fichiers traités
        with st.expander("📋 Fichiers traités"):
            for file in uploaded_files:
                st.write(f"• {file.name}")
        
        # 2. Traitement de la question
        if question:
            with st.spinner("🤔 Recherche de la réponse..."):
                response = run_chain(qa_chain, question)
                st.session_state.chat_history.append((question, response))
    
    except Exception as e:
        st.error(f"❌ Erreur lors du traitement: {str(e)}")
        st.info("Vérifiez votre clé API et le format de vos documents.")

elif not api_key:
    st.warning("🔑 Veuillez entrer votre clé API Mistral dans la barre latérale.")
elif not uploaded_files:
    st.warning("📄 Veuillez télécharger un ou plusieurs documents dans la barre latérale.")

# Afficher de l'historique (ordre inversé - dernière question en haut)
if st.session_state.chat_history:
    st.markdown("### 🗂️ Historique de conversation")
    for q, a in reversed(st.session_state.chat_history):
        with st.container():
            st.markdown(f"**❓ Question:** {q}")
            st.markdown(f"**🤖 Réponse:** {a}")
            st.divider()