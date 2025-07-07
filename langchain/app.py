# app.py
import streamlit as st
import tempfile
from main import load_and_split_file, embed_documents, create_qa_chain

st.set_page_config(page_title="Dojo IA - Q/R sur documents", layout="wide")
st.title("🧠 Dojo IA : Q/R sur vos documents")

api_key = st.text_input("🔑 Entrez votre clé API OpenAI", type="password")
uploaded_file = st.file_uploader("📄 Uploadez un document (PDF, DOCX ou TXT)", type=["pdf", "docx", "txt"])
chunk_size = st.slider("📏 Taille des chunks", 100, 2000, 500, 100)
k = st.slider("🔍 Nombre de documents à récupérer", 1, 10, 3)

if uploaded_file and api_key:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    docs = load_and_split_file(tmp_path, chunk_size)
    retriever = embed_documents(docs, api_key, k)
    qa_chain = create_qa_chain(retriever, api_key)

    st.session_state.chat_history = st.session_state.get("chat_history", [])

    question = st.text_input("❓ Posez votre question")

    if question:
        result = qa_chain({"question": question, "chat_history": st.session_state.chat_history})
        st.session_state.chat_history.append((question, result["answer"]))

        st.markdown("### Réponse :")
        st.write(result["answer"])

        st.markdown("### Historique :")
        for i, (q, a) in enumerate(st.session_state.chat_history):
            st.markdown(f"**Q{i+1} :** {q}")
            st.markdown(f"**A{i+1} :** {a}")
