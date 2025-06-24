# ./tools/load_csv_tool.py

import os
import pandas as pd
import sqlite3
from crewai.tools import tool # Importa o decorator 'tool'
from services.dataframe_store import DataFrameStore # Para armazenar metadados
import unicodedata # Para lidar com acentos e caracteres especiais
import re          # Para substituir caracteres não alfanuméricos


# --- NOVO: Função auxiliar para normalizar nomes de colunas e tabelas ---
def normalize_name(name: str) -> str:
    """
    Normaliza um nome (de coluna ou tabela) para ser compatível com SQL:
    - Converte para minúsculas.
    - Remove acentos.
    - Substitui espaços e caracteres especiais por underscores.
    - Remove múltiplos underscores e underscores no início/fim.
    """
    # 1. Converte para minúsculas
    name = name.lower()
    # 2. Remove acentos
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
    # 3. Substitui caracteres não alfanuméricos (exceto underscore) por underscore
    name = re.sub(r'[^a-z0-9_]+', '_', name)
    # 4. Remove múltiplos underscores
    name = re.sub(r'_+', '_', name)
    # 5. Remove underscores no início e no fim
    name = name.strip('_')
    return name

@tool
def load_csv_to_sqlite_tool(directory_path: str) -> str:
    """
    Lê arquivos CSV de um diretório especificado, importa seus dados para tabelas
    correspondentes em um banco de dados SQLite e armazena metadados (nome da tabela,
    colunas e tipos) em um DataFrameStore em memória.

    Args:
        directory_path (str): O caminho do diretório contendo os arquivos CSV.

    Returns:
        str: Uma mensagem de sucesso com a contagem de arquivos processados,
             ou uma mensagem de erro em caso de falha.
    """
    store = DataFrameStore()
    store.clear() # Limpa metadados de execuções anteriores, se houver.

    db_path = "./tmp/db.sqlite" # O caminho deve ser consistente com app.py
    os.makedirs(os.path.dirname(db_path), exist_ok=True) # Garante que o diretório exista

    conn = None # Inicializa conn para garantir que seja fechado em caso de erro
    arquivos_processados = 0
    erros_encontrados = []

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for filename in os.listdir(directory_path):
            if filename.endswith(".csv"):
                file_path = os.path.join(directory_path, filename)
                
                # Cria um nome de tabela válido para SQLite a partir do nome do arquivo
                # table_name = os.path.splitext(filename)[0].replace("-", "_").replace(" ", "_").lower()

                # --- ALTERAÇÃO AQUI: Normaliza o nome da tabela ---
                # A lógica de tratamento de nome de tabela já estava OK, mas agora usamos a função `normalize_name`
                table_name = normalize_name(os.path.splitext(filename)[0]) 


                try:
                    df = pd.read_csv(file_path)
                    
                    # --- NOVO: Normaliza os nomes das colunas do DataFrame ---
                    df.columns = [normalize_name(col) for col in df.columns]

                    # --- NOVO: Normaliza dados de colunas de texto ---
                    for col in df.columns:
                        # Verifica se a coluna é de tipo objeto (geralmente string)
                        if df[col].dtype == 'object':
                            # Aplica a normalização (maiúsculas e sem acentos)
                            df[col] = df[col].astype(str).apply(
                                lambda x: unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode('utf-8').upper().strip()
                            )

                    # Importa para o SQLite
                    df.to_sql(table_name, conn, if_exists="replace", index=False)

                    # Coleta e armazena metadados
                    # Usamos to_dict('records') para facilitar a passagem para um DataFrame de metadados
                    columns_metadata = []
                    for col in df.columns:  # Agora 'df.columns' já contém os nomes normalizados
                        columns_metadata.append({
                            "column_name": col,
                            "data_type": str(df[col].dtype),
                            "table_name": table_name,
                            "source_file": filename
                            # Podemos adicionar uma 'description' aqui se tivermos um LLM para inferir mais tarde
                            # por enquanto a descrição de cada campo estará no backstory do DataLoaderAgent
                        })
                    
                    # Converte para DataFrame para armazenar no DataFrameStore
                    meta_df = pd.DataFrame(columns_metadata)
                    store.add_metadata(table_name, meta_df)
                    
                    arquivos_processados += 1

                except pd.errors.EmptyDataError:
                    erros_encontrados.append(f"O arquivo CSV '{filename}' está vazio e foi ignorado.")
                except Exception as e:
                    erros_encontrados.append(f"Falha ao processar '{filename}': {e}")
                    
    except Exception as e:
        return f"Erro ao estabelecer conexão com o banco de dados ou listar diretório: {e}"
    finally:
        if conn:
            conn.close()

    status_message = f"{arquivos_processados} arquivos CSV carregados com sucesso no SQLite e metadados atualizados."
    if erros_encontrados:
        status_message += "\n\nErros/Avisos durante o processo:\n" + "\n".join(erros_encontrados)
    
    return status_message