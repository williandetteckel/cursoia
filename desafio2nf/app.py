# data-zip-analyzer/app.py

import streamlit as st
import os
import shutil # Para operações de arquivo, como limpar diretório
from agents.data_loader_agent import DataLoaderAgent
from agents.query_analyzer_agent import QueryAnalyzerAgent
from agents.response_formatter_agent import ResponseFormatterAgent
from services.dataframe_store import DataFrameStore # Para exibir metadados
from services.logger_config import app_logger # Log
from dotenv import load_dotenv

load_dotenv() # Carrega as variáveis de ambiente do .env

# --- Configurações Iniciais ---
UPLOAD_DIR = "./tmp"
DB_PATH = os.path.join(UPLOAD_DIR, "db.sqlite")

# Garante que o diretório de uploads exista
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Inicializa os agentes
data_loader_agent_instance = DataLoaderAgent()
query_analyzer_agent_instance = QueryAnalyzerAgent()
response_formatter_agent_instance = ResponseFormatterAgent()

# Instância do DataFrameStore (singleton)
dataframe_store_instance = DataFrameStore()

# --- Funções Auxiliares ---
def clear_uploads_and_db():
    """Limpa o diretório de uploads e o banco de dados SQLite."""
    if os.path.exists(UPLOAD_DIR):
        shutil.rmtree(UPLOAD_DIR)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dataframe_store_instance.clear() # Limpa também os metadados em memória
    app_logger.info("Ambiente de uploads e DB limpo.")
    st.session_state.uploaded_zip_processed = False
    st.session_state.last_question = ""
    st.success("Ambiente limpo! Pronto para um novo upload.")

# --- Configuração da Página Streamlit ---
st.set_page_config(layout="wide", page_title="NOTAVIA")

st.title("Transformando dados brutos em estratégicos")
st.markdown("Faça upload de arquivos ZIP contendo CSVs e pergunte sobre seus dados em linguagem natural.")

# --- Estado da Sessão ---
# Usamos st.session_state para manter o estado entre as interações do Streamlit
if 'uploaded_zip_processed' not in st.session_state:
    st.session_state.uploaded_zip_processed = False
if 'last_question' not in st.session_state:
    st.session_state.last_question = ""

# --- Seção de Upload ---
st.sidebar.header("Upload de Arquivo ZIP")
uploaded_file = st.sidebar.file_uploader("Arraste e solte seu arquivo .zip aqui", type="zip")

if uploaded_file is not None:
    zip_temp_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(zip_temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.sidebar.success(f"Arquivo '{uploaded_file.name}' carregado para processamento!")
    app_logger.info(f"Arquivo ZIP '{uploaded_file.name}' carregado para '{zip_temp_path}'.")

    # Processa o ZIP APENAS SE AINDA NÃO FOI PROCESSADO NESTA SESSÃO OU UM NOVO FOI UPLOADED
    if not st.session_state.uploaded_zip_processed or \
       st.session_state.get('current_zip_name') != uploaded_file.name:
        
        st.session_state.current_zip_name = uploaded_file.name
        
        with st.spinner("Processando ZIP e carregando dados... Isso pode levar um momento."):
            try:
                # Chama o DataLoaderAgent
                loader_result = data_loader_agent_instance.run(
                    zip_file_path=zip_temp_path,
                    destination_directory=UPLOAD_DIR
                )
                
                # Acessamos o atributo 'raw' ou o que for o resultado textual final.
                # CrewOutput geralmente tem um atributo .raw ou .result
                # Se for uma string, .raw deve funcionar.
                display_loader_result = loader_result.raw if hasattr(loader_result, 'raw') else str(loader_result)

                st.write("---")
                st.subheader("Processamento de Carga Concluído!")
                # st.success(loader_result)
                st.success(display_loader_result)
                app_logger.info(f"Processamento de carga concluído: {display_loader_result}")
                st.session_state.uploaded_zip_processed = True
            except Exception as e:
                st.error(f"Erro no processo de carga: {e}")
                app_logger.error(f"Erro no processo de carga: {e}", exc_info=True)
                st.session_state.uploaded_zip_processed = False
    else:
        st.info("Arquivo ZIP já processado nesta sessão. Limpe para enviar um novo.")

# Botão para limpar o ambiente
if st.sidebar.button("Limpar Ambiente"):
    clear_uploads_and_db()
    st.rerun() # Recarrega a página para refletir o estado limpo

# --- Seções Principais da Aplicação ---
if st.session_state.uploaded_zip_processed:
    st.write("---")
    st.header("Metadados das Tabelas Carregadas")
    
    all_metadata_df = dataframe_store_instance.get_all_metadata()
    if not all_metadata_df.empty:
        # Agrupa metadados por tabela para exibir de forma organizada
        table_names = all_metadata_df['table_name'].unique().tolist()
        for table_name in table_names:
            with st.expander(f"Tabela: **`{table_name}`**"):
                st.dataframe(
                    all_metadata_df[all_metadata_df['table_name'] == table_name]
                    [['column_name', 'data_type', 'source_file']],
                    hide_index=True
                )
    else:
        st.info("Nenhum metadado de tabela encontrado. Verifique o processo de carga.")

    st.write("---")
    st.header("Faça uma Pergunta sobre os Dados")

    # Adicione uma chave única ao text_area e use o valor diretamente dele.
    # O valor padrão é carregado do session_state, mas qualquer alteração no widget
    # será refletida no 'question_input' nesta execução. => AINDA NÃO FUNCIONA COMO DESEJADO
    question = st.text_area(
        "Digite sua pergunta aqui (ex: 'Quantas CHAVE DE ACESSO distintas existem?', 'Quais as colunas da tabela de notas_fiscais?')",
        value=st.session_state.last_question,
        height=100,
        key="user_question_input"
    )

    if st.button("Perguntar"):
        # Garanta que a pergunta usada seja a do text_area e não apenas a do session_state
        # O valor do 'question' já estará atualizado aqui se o widget foi interatado.
        if question:
            st.session_state.last_question = question # Atualiza o session_state com o valor atual do text_area
            app_logger.info(f"Pergunta do usuário: '{question}'")
            with st.spinner("Analisando e gerando resposta..."):
                try:
                    # 1. Chama o QueryAnalyzerAgent para gerar o código (SQL ou Python)
                    st.info("Agente de Análise está gerando a consulta...")
                    # generated_code = query_analyzer_agent_instance.run(question=question)
                    generated_code_crew_output = query_analyzer_agent_instance.run(question=question)
                    
                    # st.subheader("Código Gerado (SQL ou Python):")
                    # st.code(generated_code, language='sql' if generated_code.strip().lower().startswith('select') else 'python')

                    # CORREÇÃO: Extrair a string do CrewOutput
                    # O QueryAnalyzerAgent.run() retorna a saída da sua crew.kickoff,
                    # que é o resultado da última tarefa (GenerateQueryTask).
                    # Essa tarefa espera "APENAS o código gerado".
                    # Se o crew.kickoff retorna um CrewOutput object, precisamos extrair a string.
                    # Por padrão, CrewAI tenta retornar o resultado da última tarefa diretamente se process=sequential.
                    # Vamos garantir que estamos pegando o valor correto.
                    if hasattr(generated_code_crew_output, 'raw'):
                        generated_code = generated_code_crew_output.raw
                    elif isinstance(generated_code_crew_output, str):
                        generated_code = generated_code_crew_output
                    else:
                        # Fallback se não for string nem CrewOutput esperado
                        generated_code = str(generated_code_crew_output) 
                        app_logger.warning(f"Tipo de retorno inesperado do QueryAnalyzerAgent: {type(generated_code_crew_output)}")

                    st.subheader("Código Gerado (SQL ou Python):")
                    # No .code, o método .strip() deve ser aplicado na string
                    # st.code(generated_code.strip(), language='sql' if generated_code.strip().lower().startswith('select') else 'python')

                    # ALTERAÇÃO AQUI: Usar st.text_area para exibir o código gerado => NÃO ESTÁ FUNCIONANDO PARA METADADOS
                    # Com height fixo e read_only para que não seja editável
                    st.text_area(
                        "Código Gerado:", # Título do text_area
                        value=generated_code.strip(),
                        height=250, # Altura fixa em pixels
                        help="Este é o código SQL ou Python gerado pelos agentes.",
                        key="generated_code_display", # Chave única para o widget
                        disabled=True # Torna o campo somente leitura
                    )
                    app_logger.info(f"Código gerado pelo QueryAnalyzerAgent: \n```\n{generated_code.strip()}\n```")

                    # 2. Chama o ResponseFormatterAgent para executar o código e formatar a resposta
                    st.info("Agente de Formatação está executando e preparando a resposta...")
                    # final_response = response_formatter_agent_instance.run(generated_code=generated_code)
                    final_response_crew_output = response_formatter_agent_instance.run(generated_code=generated_code)
                    
                    # st.write("---")
                    # st.subheader("Resposta Final:")
                    # st.markdown(final_response) # Usa markdown para exibir tabelas, etc.

                    # CORREÇÃO: Extrair a string do CrewOutput
                    if hasattr(final_response_crew_output, 'raw'):
                        final_response = final_response_crew_output.raw
                    elif isinstance(final_response_crew_output, str):
                        final_response = final_response_crew_output
                    else:
                        final_response = str(final_response_crew_output)
                        app_logger.warning(f"Tipo de retorno inesperado do ResponseFormatterAgent: {type(final_response_crew_output)}")

                    st.write("---")
                    st.subheader("Resposta Final:")
                    st.markdown(final_response)
                    app_logger.info(f"Resposta final formatada: \n```\n{final_response}\n```")

                except Exception as e:
                    # st.error(f"Ocorreu um erro ao processar sua pergunta: {e}")
                    # st.info("Tente reformular a pergunta ou verificar os logs.")
                    
                    st.error(f"Ocorreu um erro ao processar sua pergunta: {e}")
                    st.info("Verifique os logs em './tmp/agent_activity.log' para mais detalhes.")
                    app_logger.error(f"Erro ao processar pergunta: {e}", exc_info=True)

        else:
            st.warning("Por favor, digite uma pergunta.")
            app_logger.warning("Tentativa de consulta com pergunta vazia.")

else:
    st.info("Faça o upload de um arquivo ZIP para começar a analisar os dados.")