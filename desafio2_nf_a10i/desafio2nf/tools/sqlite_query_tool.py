# ./tools/sqlite_query_tool.py

import sqlite3
import pandas as pd
import os
from crewai.tools import tool

@tool
def sqlite_query_tool(sql_query: str) -> str:
    """
    Executa um comando SQL no banco de dados SQLite localizado em './tmp/db.sqlite'.
    Retorna os resultados da consulta em formato de tabela Markdown.

    Args:
        sql_query (str): O comando SQL a ser executado.

    Returns:
        str: Os resultados da consulta formatados como uma tabela Markdown,
             ou uma mensagem de erro se a execução falhar.
    """
    db_path = "./tmp/db.sqlite"

    if not os.path.exists(db_path):
        return f"[ERRO] Banco de dados SQLite não encontrado em '{db_path}'. Certifique-se de que os dados foram carregados."

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        # Para SELECTs, pandas.read_sql_query é excelente
        if sql_query.strip().lower().startswith("select"):
            df = pd.read_sql_query(sql_query, conn)
            if df.empty:
                return "A consulta SQL foi executada com sucesso, mas não retornou resultados."
            return df.to_markdown(index=False) # Formata o DataFrame como tabela Markdown
        else:
            # Para comandos DDL/DML como CREATE, INSERT, DELETE, UPDATE
            cursor = conn.cursor()
            cursor.execute(sql_query)
            conn.commit()
            return f"Comando SQL (não SELECT) executado com sucesso."

    except sqlite3.Error as e:
        return f"[ERRO] Erro ao executar SQL: {e}\nSQL tentado: ```{sql_query}```"
    except Exception as e:
        return f"[ERRO] Erro inesperado ao executar SQL: {e}\nSQL tentado: ```{sql_query}```"
    finally:
        if conn:
            conn.close()