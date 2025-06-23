from utils.extract_zip import extract_zip
from utils.list_files import list_files
from utils.read_formats import read_txt, read_csv, read_json
from utils.analise_dataframe import criar_tool_analise_pandas
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import json
import pandas as pd
import streamlit as st
import os

from utils.valida_path import validar_caminho

load_dotenv()

prompt = """Você é um assistente de IA especializado em manipulação de arquivos no sistema de arquivos local.
Você responde em português.
Responda todas as perguntas em português, de forma clara e direta.

Seu papel é responder com clareza, objetividade e sem suposições. Sempre que receber um comando, 
execute logicamente e diretamente, sem desviar do assunto.

Você pode executar ações como:
- Listar arquivos e pastas
- Ler o conteúdo de arquivos texto, CSV, JSON etc.
- Extrair arquivos ZIP
- acessar caminhos de arquivos e pastas
- Informar o tipo de arquivo com base na extensão ou conteúdo
- Lembrar dos caminhos e arquivos mencionados na conversa
- Pegar os nomes dos arquivos e suas extensões
- Retornar mensagens de erro claras se algo não puder ser feito
- Retornar o caminho completo de arquivos ou pastas

Importante:
- Nunca invente arquivos, caminhos ou conteúdos.
- Se o caminho não existir, informe com precisão.
- Não faça perguntas. Apenas aja ou retorne uma resposta objetiva.
- Responda sempre de forma curta, clara e sem floreios.

Seja como um script shell com inteligência para entender comandos em linguagem natural.
"""
model = ChatGroq(
    model="llama3-8b-8192",
    temperature=0.2,
    max_retries=2

)
memory = ConversationBufferMemory(
    return_messages=True, memory_key="chat_history")

tools = [
    Tool(name="ListarArquivos", func=list_files,
         description="Use para Listar ou exibir arquivos de um diretório retorne o nome e extensão dos arquivos.",
         return_direct=True),
    Tool(name="LerArquivoTXT", func=read_txt,
         description="Use para ler o conteúdo de um arquivo TXT. Caminho completo deve ser fornecido.",
         return_direct=True),
    Tool(name="LerArquivoCSV", func=read_csv,
         description="Use para ler o conteúdo de um arquivo CSV. Caminho completo deve ser fornecido.",
         return_direct=True),
    Tool(name="LerArquivoJSON", func=read_json,
         description="Use para ler o conteúdo de um arquivo JSON. Caminho completo deve ser fornecido.",
         return_direct=True),
    Tool(name="ExtrairZip", func=extract_zip,
         description="Use para Extrair os arquivo ZIP para uma pasta",
         return_direct=True),
    Tool(name="ValidarCaminho", func=validar_caminho,
         description="Use para Extrair os arquivo ZIP para uma pasta",
         return_direct=True),
    # validar_caminho
]


agente = initialize_agent(
    tools=tools,
    llm=model,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True,
    agent_kwargs={
        "prefix": prompt
    }
)

st.title("📂 Agente Inteligente de Arquivos com IA")

user_input = st.chat_input(
    "Digite o que deseja fazer (ex: listar arquivos da pasta X):")

st.markdown(
    """
    <div style="margin-top: 10px; color: gray; font-size: 0.9em;">
        💡 <b>Dica:</b> Para extrair um arquivo ZIP, digite algo como <code>extrair zip + caminho</code><br>
        📁 Exemplos:<br> 
         - <code>extrair zip C:\\pasta\\arquivo.zip\</code><br>
         - <code>listar arquivos C:\\pasta\\</code><br>
         - <code>carregar arquivos C:\\pasta\\arquivo.csv\</code>
    </div>
    """,
    unsafe_allow_html=True
)

if user_input:
    with st.spinner("Processando..."):
        response = agente.run(user_input)
        st.session_state.response = response

        # Tenta carregar como JSON e salvar o DataFrame
        try:
            data = json.loads(response)
            if isinstance(data, list) and isinstance(data[0], dict):
                st.session_state.df = pd.DataFrame(data)
                st.success(
                    "✅ Dados processados! Acesse a aba '📄 Dataframe view' para visualizar.")

            else:
                st.session_state.df = None
                st.info(response)
        except Exception:
            st.session_state.df = None
            st.info(response)
