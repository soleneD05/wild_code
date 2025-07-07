# main.py
import os
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain

def load_and_split_file(file_path, chunk_size):
    loader = UnstructuredFileLoader(file_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=50)
    return splitter.split_documents(docs)

def embed_documents(docs, api_key, k):
    os.environ["OPENAI_API_KEY"] = api_key
    embeddings = OpenAIEmbeddings()
    db = Chroma.from_documents(docs, embeddings, persist_directory="./chroma_db")
    db.persist()
    return db.as_retriever(search_kwargs={"k": k})

def create_qa_chain(retriever, api_key):
    os.environ["OPENAI_API_KEY"] = api_key
    llm = ChatOpenAI(temperature=0)
    return ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, return_source_documents=True)
