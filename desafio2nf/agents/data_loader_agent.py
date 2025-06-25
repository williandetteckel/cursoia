# ./agents/data_loader_agent.py

import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from services.logger_config import app_logger

# Importe as ferramentas que este agente usará
from tools.unzip_file_tool import unzip_file_tool
from tools.load_csv_tool import load_csv_to_sqlite_tool

load_dotenv()

class DataLoaderAgent:
    def __init__(self):
        # Inicializa o LLM que este agente usará.
        # Ele precisa de um LLM para raciocinar e decidir qual ferramenta usar.
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", # Usando o modelo especificado
            temperature=0,       # Determinístico para tarefas de carga de dados
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    def run(self, zip_file_path: str, destination_directory: str):
        app_logger.info(f"DataLoaderAgent: Iniciando execução para '{zip_file_path}'")
        
        # 1. Defina o Agente
        data_loader_agent = Agent(
            role="Engenheiro de Dados para Carga de Arquivos",
            goal="Gerenciar a descompactação de arquivos ZIP e o carregamento de arquivos CSV em um banco de dados SQLite, organizando seus metadados.",
            backstory=(
                "Sou um especialista em ingestão de dados, com proficiência em lidar com diversos formatos "
                "de arquivo e organizar informações para análise posterior. Garanto que todos os dados "
                "sejam carregados corretamente e que seus esquemas sejam devidamente registrados."
            ),
            tools=[unzip_file_tool, load_csv_to_sqlite_tool], # Passa as funções das ferramentas diretamente
            verbose=True,
            allow_delegation=False,
            llm=self.llm # Atribui o LLM ao agente
        )

        # 2. Defina as Tarefas
        unzip_task = Task(
            description=f"""
            Descompacte o arquivo ZIP localizado em '{zip_file_path}' para o diretório de destino '{destination_directory}'.
            Assegure-se de que todos os arquivos CSV contidos no ZIP sejam extraídos corretamente.
            """,
            expected_output=(
                "Uma mensagem de sucesso listando todos os arquivos que foram descompactados "
                "para o diretório de destino, ou uma mensagem clara de erro se a descompactação falhar."
            ),
            tools=[unzip_file_tool],
            agent=data_loader_agent
        )

        load_csv_task = Task(
            description=f"""
            Após a descompactação, carregue todos os arquivos CSV encontrados no diretório '{destination_directory}'
            para o banco de dados SQLite localizado em './tmp/db.sqlite'.
            Cada arquivo CSV deve se tornar uma tabela no SQLite com o mesmo nome do arquivo (ajustado para ser válido para SQL).
            Além disso, os metadados de cada tabela (nomes de colunas e tipos de dados) devem ser registrados no DataFrameStore.
            """,
            expected_output=(
                "Uma mensagem de sucesso confirmando a quantidade de arquivos CSV carregados no SQLite "
                "e que seus metadados foram atualizados no DataFrameStore, ou uma mensagem de erro detalhada."
            ),
            tools=[load_csv_to_sqlite_tool],
            agent=data_loader_agent
        )

        # 3. Crie a Crew para orquestrar o agente e as tarefas
        crew = Crew(
            agents=[data_loader_agent],
            tasks=[unzip_task, load_csv_task],
            verbose=True,
            process=Process.sequential # Garante que as tarefas sejam executadas em ordem
        )

        # 4. Inicie o processo da Crew
        try:
            result = crew.kickoff(inputs={
                "zip_file_path": zip_file_path,
                "destination_directory": destination_directory
            })
            app_logger.info(f"DataLoaderAgent: Processo CrewAI concluído com sucesso. Resultado: {result}")
            return result
        except Exception as e:
            app_logger.error(f"DataLoaderAgent: Erro durante a execução da Crew: {e}", exc_info=True)
            raise # Re-lança o erro para ser capturado no app.py
        