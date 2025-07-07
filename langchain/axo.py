import os
import requests
import streamlit as st

from langchain.agents import Tool
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent

def reload_env():
    load_dotenv(override=True)
    return os.getenv("SERPER_API_KEY")

SERP_API_KEY = reload_env()

def reload_env2():
    load_dotenv(override=True)
    return os.getenv("OPENAI_API_KEY")

OPENAI_API_KEY = reload_env2()

def query(q):
    print(q)
    url = "https://serpapi.com/search.json"
    full_url = f"{url}?engine=google&q={q}&api_key={SERP_API_KEY}"
    response = requests.get(full_url)
    return response.json()

from langchain.agents import Tool

tools = [
    Tool(
        name="search",
        func=query,
        description="Utile pour rechercher sur le web avec l'API Serper"
    )
]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """Vous êtes un assistant de recherche. Utilisez vos outils pour répondre aux questions.
        Si vous n'avez pas d'outil pour répondre à la question, dites-le.
        Vous recevrez un sujet et votre objectif est de trouver des points saillants ou des sujets 'accrocheurs' qui peuvent être utiles pour expliquer ce sujet à quelqu'un qui n'est pas technique.
        Dans les documents que vous analyserez, veuillez mettre en évidence dans votre résumé tous les slogans possibles et dire où vous les avez trouvés.
        Fournissez votre réponse sous forme de points de balle avec ces sujets accrocheurs."""),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def search_and_summarize(query):
    input_data = {"input": query}
    result = agent_executor.invoke(input_data)
    return result["output"] if "output" in result else "Aucun résultat disponible"


def main():
    st.set_page_config(page_title="Agent de Newsletter", page_icon=":parrot:", layout="wide")
    st.header("Générer une Newsletter avec IA :parrot:")

    query = st.text_input("Entrez un sujet à rechercher et à résumer...")

    if query:
        with st.spinner(f"Génération des résultats pour '{query}'"):
            try:
                response = search_and_summarize(query)
                st.subheader("Résultats")
                st.write(response)
            except Exception as e:
                st.error(f"Une erreur est survenue : {str(e)}")

if __name__ == '__main__':
    main()