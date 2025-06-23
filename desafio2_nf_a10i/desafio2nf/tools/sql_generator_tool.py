# ./tools/sql_generator_tool.py

import os
from crewai.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv() # Garante que as variáveis de ambiente sejam carregadas neste arquivo

@tool
def sql_generator_tool(question: str, table_schemas_context: str) -> str:
    """
    Gera um comando SQL válido e otimizado para SQLite com base em uma pergunta em linguagem natural
    e no contexto do esquema das tabelas disponíveis.

    Args:
        question (str): A pergunta em linguagem natural feita pelo usuário sobre os dados.
        table_schemas_context (str): Uma string formatada contendo o nome das tabelas e seus esquemas
                                     (nomes das colunas e tipos de dados) do banco de dados SQLite.
                                     Exemplo: "Tabela 'faturas': id INTEGER, valor REAL, data TEXT.
                                     Tabela 'clientes': id INTEGER, nome TEXT, cidade TEXT."

    Returns:
        str: O comando SQL gerado, pronto para ser executado.
             Em caso de erro na geração, retorna uma mensagem de erro começando com "[ERRO]".
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini", # Escolha um modelo adequado
        temperature=0, # Determinístico para geração de código
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    prompt = f"""
    Você é um experiente analista de banco de dados SQL e sua tarefa é gerar comandos SQL para um banco de dados SQLite.
    Seu objetivo é transformar perguntas em linguagem natural em consultas SQL precisas.

    **Contexto do Banco de Dados SQLite:**
    O banco de dados está localizado em './tmp/db.sqlite'.
    As tabelas e seus esquemas (colunas e tipos) são os seguintes:
    {table_schemas_context}

    **Regras para Geração de SQL:**
    - Gerar APENAS o comando SQL, sem qualquer texto adicional, explicações, aspas extras ou formatação que não seja o SQL puro.
    - O SQL deve ser válido para SQLite.
    - Se a pergunta for ambígua ou não puder ser respondida com as tabelas/colunas fornecidas, gere um SQL que retorne uma mensagem de erro ou um SELECT que retorne vazio, mas tente sempre gerar um SQL funcional.
    - Priorize o uso de `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `GROUP BY`, `ORDER BY`, `JOIN` conforme necessário pela pergunta.
    - Para contagens de valores distintos, use `COUNT(DISTINCT coluna)`.
    - Ao retornar texto, use aspas simples, por exemplo 'Valor'.
    - Use alias para colunas ou tabelas se isso melhorar a clareza.
    - Para comparações de texto (cláusulas WHERE, por exemplo), o valor deve ser convertido para MAIÚSCULAS e SEM ACENTOS, pois os dados no banco de dados já foram normalizados desta forma. Use a função `UPPER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(coluna, 'Á', 'A'), 'À', 'A'), 'Ã', 'A'), 'Â', 'A'), 'É', 'E'), 'È', 'E'), 'Ê', 'E'), 'Í', 'I'), 'Ó', 'O'), 'Õ', 'O'), 'Ô', 'O'), 'Ú', 'U'), 'Ü', 'U'), 'Ç', 'C'))` ou simplifique se a LLM entender, mas priorize a robustez.**
    - Exemplo de comparação de texto: `WHERE UPPER(REPLACE(REPLACE(nome_municipio, 'Á', 'A'), 'Ã', 'A')) = 'CAJAMAR'`


    **Exemplos (apenas para seu entendimento, não gere exemplos na resposta):**
    - Pergunta: "Quantas notas fiscais foram emitidas para o município de Cajamar?"
      SQL gerado: `SELECT COUNT(*) FROM `notas_fiscais` WHERE `municipio` = 'Cajamar';`

    - Pergunta: "Qual o valor total das vendas em janeiro de 2024?"
      SQL gerado: `SELECT SUM(`valor`) FROM `vendas` WHERE STRFTIME('%Y-%m', `data_venda`) = '2024-01';`

    - Pergunta: "Liste as 5 maiores vendas."
      SQL gerado: `SELECT * FROM `vendas` ORDER BY `valor` DESC LIMIT 5;`
      
    - Pergunta: "Quais cfop foram utilizadas para a cidade de São Paulo?"
      SQL gerado: SELECT DISTINCT `cfop` FROM `tabela` WHERE `municipio` = 'SAO PAULO';
      
    - Pergunta' "Quantas notas fiscais existem por natureza da operação de venda?"
      SQL gerado: SELECT COUNT(1) AS qt FROM `tabela` WHERE `natureza_da_operacao` LIKE '%VENDA%';

    **PERGUNTA PARA GERAR SQL:**
    "{question}"

    SQL:
    """

    try:
        sql_command = llm.predict(prompt).strip()
        # Validação simples para tentar capturar casos onde a LLM "explica" o SQL
        if "```sql" in sql_command.lower():
            sql_command = sql_command.replace("```sql", "").replace("```", "").strip()
        return sql_command
    except Exception as e:
        return f"[ERRO] Falha ao gerar SQL: {e}"