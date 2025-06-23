# ./tools/metadata_query_tool.py

import pandas as pd
from crewai.tools import tool
from langchain_openai import ChatOpenAI
from services.dataframe_store import DataFrameStore # Para acessar os metadados
import os
from dotenv import load_dotenv

load_dotenv() # Garante que as variáveis de ambiente sejam carregadas

@tool
def metadata_query_tool(question: str) -> str:
    """
    Responde a perguntas sobre a estrutura e os metadados dos dados carregados
    (tabelas, colunas, tipos, arquivos de origem), gerando e executando código Python
    para consultar o DataFrameStore.

    Args:
        question (str): A pergunta em linguagem natural feita pelo usuário sobre os metadados.

    Returns:
        str: O resultado da consulta aos metadados, formatado em Markdown se for tabular,
             ou uma mensagem de erro.
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini", # Usando o modelo especificado
        temperature=0,       # Determinístico
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    store = DataFrameStore()
    all_metadata_df = store.get_all_metadata() # Obtém todos os metadados

    if all_metadata_df.empty:
        return "[INFO] Não há metadados carregados. Por favor, carregue os arquivos CSV primeiro."

    # Representação dos metadados para o LLM
    metadata_representation = f"""
    Os metadados disponíveis sobre as tabelas e suas colunas estão neste formato de DataFrame:
    {all_metadata_df.to_markdown(index=False)}

    Colunas do DataFrame de metadados:
    - 'table_name': Nome da tabela no SQLite e nome original do arquivo CSV (ex: 'vendas_2023').
    - 'column_name': Nome da coluna dentro da tabela (ex: 'valor_total').
    - 'data_type': Tipo de dado inferido da coluna (ex: 'int64', 'object', 'float64').
    - 'source_file': Nome do arquivo CSV original de onde a tabela foi carregada (ex: 'vendas_2023.csv').

    Você deve escrever APENAS o código Python para consultar este DataFrame 'all_metadata_df'.
    O DataFrame 'all_metadata_df' já está disponível no ambiente de execução.
    Você pode usar 'pandas' como 'pd'.

    **Exemplos de como usar o DataFrame 'all_metadata_df' (apenas para seu entendimento, não gere exemplos na resposta):**
    - Pergunta: "Quais são todas as tabelas carregadas?"
      Código Python: `all_metadata_df['table_name'].unique().tolist()`

    - Pergunta: "Quais colunas existem na tabela 'notas_fiscais'?"
      Código Python: `all_metadata_df[all_metadata_df['table_name'] == 'notas_fiscais']['column_name'].tolist()`

    - Pergunta: "Mostre todas as colunas e seus tipos para a tabela 'clientes'."
      Código Python: `all_metadata_df[all_metadata_df['table_name'] == 'clientes'][['column_name', 'data_type']]`

    **Sua tarefa é gerar APENAS o código Python que, quando executado, irá responder à seguinte pergunta sobre os metadados:**
    """

    full_prompt = f"{metadata_representation}\nPergunta: \"{question}\"\n\nCódigo Python:"

    try:
        generated_code = llm.predict(full_prompt).strip()

        # Limpeza básica para remover blocos de código Markdown
        if "```python" in generated_code.lower():
            generated_code = generated_code.replace("```python", "").replace("```", "").strip()

        # Executa o código Python gerado
        local_vars = {"all_metadata_df": all_metadata_df, "pd": pd, "DataFrameStore": DataFrameStore} # Inclui DataFrameStore caso o código gerado tente instanciá-lo
        exec_globals = {}
        exec_locals = {"result_exec": None, **local_vars} # result_exec para capturar o resultado

        exec(f"result_exec = {generated_code}", exec_globals, exec_locals)
        execution_result = exec_locals.get("result_exec")

        # Formata o resultado
        if isinstance(execution_result, pd.DataFrame):
            return execution_result.to_markdown(index=False)
        elif execution_result is not None:
            return str(execution_result)
        else:
            return f"[AVISO] O código Python foi executado, mas não retornou um resultado explícito ou reconhecível. Código: ```{generated_code}```"

    except Exception as e:
        return f"[ERRO] Falha ao gerar ou executar o código Python para metadados: {e}\nCódigo gerado: ```\n{generated_code}\n```"