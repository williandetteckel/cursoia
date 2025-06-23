# ./agents/response_formatter_agent.py

import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from services.logger_config import app_logger

# Importe as ferramentas que este agente usará para execução
from tools.sqlite_query_tool import sqlite_query_tool
from tools.metadata_query_tool import metadata_query_tool

load_dotenv()

class ResponseFormatterAgent:
    def __init__(self):
        # O LLM para este agente, para raciocinar sobre a formatação e execução
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", # Usando o modelo especificado
            temperature=0.2,     # Um pouco mais de temperatura aqui pode ajudar na formatação amigável
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    def run(self, generated_code: str):
        app_logger.info(f"ResponseFormatterAgent: Iniciando formatação para o código: \n```\n{generated_code}\n```") # <--- NOVO: Adiciona log

        # 1. Defina o Agente
        response_formatter_agent = Agent(
            role="Formatador e Apresentador de Respostas",
            goal="Executar o código de consulta fornecido (SQL ou Python) e formatar seus resultados de maneira clara, concisa e fácil de entender para o usuário final.",
            backstory=(
                "Sou um especialista em transformar dados brutos de consultas em respostas inteligíveis. "
                "Minha expertise está em executar comandos SQL ou Python e apresentar os resultados "
                "de forma organizada, seja em tabelas Markdown, listas ou resumos diretos, "
                "garantindo que a informação seja acessível e útil."
            ),
            tools=[sqlite_query_tool, metadata_query_tool], # Ambas as ferramentas de execução
            verbose=True,
            allow_delegation=False, # Não delega, pois é o responsável final pela apresentação
            llm=self.llm
        )

        # 2. Defina a Tarefa
        format_and_present_task = Task(
            description=f"""
            Você recebeu o seguinte código gerado:
            ```
            {generated_code}
            ```

            **Sua tarefa é executar este código utilizando a ferramenta apropriada e, em seguida, formatar o resultado para o usuário.**

            Siga estes passos rigorosamente:
            1. **Determine o tipo de código:**
               - Se o código começar com 'SELECT' (ignorando case e espaços), é SQL. Use o `sqlite_query_tool`.
               - Se o código contiver 'all_metadata_df' ou 'DataFrameStore', é Python para metadados. Use o `metadata_query_tool`.
               - Caso contrário, você pode indicar que o código não é reconhecível para execução.
            2. **Execute o código** usando a ferramenta identificada.
            3. **Apresente o resultado da execução.** Se o resultado for uma tabela (detectada pela formatação Markdown ou pela presença de múltiplas linhas de dados), exiba-a claramente. Se for um valor único ou uma lista/texto, apresente-o diretamente.
            4. Sua **saída final** deve ser o resultado formatado, com uma breve introdução se for necessário para contexto (ex: "Resultado da sua consulta:"), mas sempre priorizando a clareza e a concisão.

            **Exemplo de Saída Esperada:**
            "Resultado da sua consulta:\n\n```markdown\n| coluna1 | coluna2 |\n|---------|---------|\n| dado1   | dado2   |\n```"
            Ou
            "O número total de itens é: 12345"
            """,
            expected_output=(
                "O resultado formatado da execução do código fornecido (SQL ou Python), "
                "apresentado de forma clara e concisa para o usuário final. "
                "Deve incluir o resultado bruto da execução, preferencialmente em formato tabular Markdown "
                "se aplicável, ou como um valor/texto direto."
            ),
            tools=[sqlite_query_tool, metadata_query_tool], # Passa as ferramentas de execução
            agent=response_formatter_agent
        )

        # 3. Crie a Crew para orquestrar o agente e a tarefa
        crew = Crew(
            agents=[response_formatter_agent],
            tasks=[format_and_present_task],
            verbose=True,
            process=Process.sequential
        )

        # 4. Inicie o processo da Crew
        # print("Iniciando processo de execução e formatação da resposta...")
        # final_response = crew.kickoff(inputs={"generated_code": generated_code})
        # print("Processo de formatação da resposta concluído.")
        
        # return final_response
        
        try:
            final_response = crew.kickoff(inputs={"generated_code": generated_code})
            app_logger.info(f"ResponseFormatterAgent: Resposta final da CrewAI: \n```\n{final_response}\n```") # <--- NOVO: Adiciona log
            return final_response
        except Exception as e:
            app_logger.error(f"ResponseFormatterAgent: Erro durante a formatação da resposta pela Crew: {e}", exc_info=True) # <--- NOVO: Adiciona log de erro
            raise # Re-lança o erro
