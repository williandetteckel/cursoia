# semantica.py

import streamlit as st
from langchain.agents import initialize_agent, AgentType
from langchain_groq import ChatGroq

from utils.analise_dataframe import criar_tool_analise_pandas

st.set_page_config(page_title="📚 Semântica", page_icon="📚")
st.title("📚 Perguntas sobre o arquivo")

# Verifica se o DataFrame está carregado no session_state
if "df" not in st.session_state or st.session_state.df is None:
    st.warning(
        "⚠️ Nenhum DataFrame carregado. Vá até a aba agente e carregue um arquivo CSV.")
    st.stop()

# Inicializa LLM
llm = ChatGroq(model="llama3-8b-8192", temperature=0.2)

# Cria a ferramenta com base no DataFrame já carregado
df = st.session_state.df
tool_busca = criar_tool_analise_pandas(df, llm)

# Caixa de entrada do usuário
pergunta = st.text_input("🧠 Faça sua pergunta sobre os dados:")

if pergunta:
    with st.spinner("Pensando..."):
        resposta = tool_busca.run(pergunta)
        st.success("✅ Resposta:")
        st.write(resposta)
