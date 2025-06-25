# data-zip-analyzer/agents/query_analyzer_agent.py

import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Importe as ferramentas que este agente usará
from tools.sql_generator_tool import sql_generator_tool
from tools.metadata_query_tool import metadata_query_tool
from services.dataframe_store import DataFrameStore # Para obter o contexto dos metadados
from services.logger_config import app_logger

load_dotenv()

class QueryAnalyzerAgent:
    def __init__(self):
        # O LLM para este agente, com temperatura mais baixa para precisão
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0, # Crucial para geração de código determinística
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.dataframe_store = DataFrameStore() # Instancia o Singleton para acesso aos metadados

    def run(self, question: str):
        app_logger.info(f"QueryAnalyzerAgent: Iniciando análise para a pergunta: '{question}'")

        # 1. Obtenha o contexto do esquema das tabelas do DataFrameStore
        # Isso será passado para o SQLGeneratorTool
        all_metadata_df = self.dataframe_store.get_all_metadata()
        table_schemas_context = "Não há metadados de tabelas carregados no momento."
        if not all_metadata_df.empty:
            # Formata os metadados de forma que o LLM possa entender o esquema
            # Ex: "Tabela 'nome_tabela': coluna1 TIPO, coluna2 TIPO. "
            # Agrupa por nome de tabela e constrói a string do esquema
            grouped_metadata = all_metadata_df.groupby('table_name').apply(
                lambda x: f"Tabela '{x.name}': " + 
                          ", ".join([f"{row['column_name']} {row['data_type']}" 
                                     for idx, row in x.iterrows()]) + "."
            )
            table_schemas_context = "\n".join(grouped_metadata.tolist())

        app_logger.debug(f"QueryAnalyzerAgent: Contexto de metadados:\n{table_schemas_context}")


        # 2. Defina o Agente
        query_analyzer_agent = Agent(
            role="Analista de Perguntas e Gerador de Consultas",
            goal="Converter perguntas do usuário sobre dados ou metadados em comandos SQL ou código Python executável, utilizando o contexto do esquema das tabelas.",
            backstory=(
                "Sou um expert em tradução de linguagem natural para consultas de banco de dados e metadados. "
                "Minha função é entender a intenção por trás de cada pergunta e gerar o código exato "
                "necessário para extrair a informação, seja de dados tabulares (via SQL) ou de metadados (via Python). "
                "Tenho acesso ao esquema de todas as tabelas e metadados carregados para garantir a precisão."
                "No caso de comparações de texto, converter os campos e o valor procurado para maiúsculo e sem acentos."
                "chave_de_acesso: valor único na tabela 202401_nfs_cabecalho e, utilizado como chave estrangeira na tabela 202401_nfs_itens;"
                "modelo: define o modelo do documento;"
                "serie: é um número de classificação de documento, portanto, não utilizado para cálculo, somente para busca, ordenação ou identificação;"
                "numero: é um número de identificação de documento, portanto, não utilizado para cálculo, somente para busca, ordenação ou identificação;"
                "natureza_da_operacao: categorias relacionadas ao motivo da emissão do documento;"
                "data_emissao: campo de data e hora do momento em que o documento foi gerado;"
                "evento_mais_recente: campo de categorização do evento relacionado a emissão do documento;"
                "data_hora_evento_mais_recente: campo de data e hora do evento relacionado a emissão do documento;"
                "cpf_cnpj_emitente: dígitos de documento de pessoa física (CPF) ou pessoa jurídica (CNPJ) que emitiu o documento, campo não utilizado para cálculo, somente para busca, ordenação ou identificação;"
                "razao_social_emitente: nome ou descrição relacionado a quem emitiu o documento;"
                "inscricao_estadual_emitente: número da inscrição estadual do emissor do documento, não utilizado para cálculo, somente para busca, ordenação ou identificação;"
                "uf_emitente: estado brasileiro onde foi emitido o documento;"
                "municipio_emitente: cidade brasileira onde foi emitido o documento;"
                "cnpj_destinatario: dígitos de documento de pessoa jurídica (CNPJ) para a qual foi emitido e entregue o documento, campo não utilizado para cálculo, somente para busca, ordenação ou identificação;"
                "nome_destinatario: nome ou descrição para a qual foi emitido e entregue o documento;"
                "uf_destinatario: estado brasileiro para a qual foi emitido e entregue o documento;"
                "indicador_ie_destinatario: classificação da inscrição estadual para a qual foi emitido e entregue o documento;"
                "destino_da_operacao: classificação do tipo de operação, se foi dentro do próprio estado ou não, para fins de tributos fiscais;"
                "consumidor_final: classificação do tipo de utilização dos itens presentes no documento, se são para uso de consumidor final, se são para transformação, para fins de análise de retenções, subsídios e até mesmo proibições;"
                "presenca_do_comprador: classificação da presença do comprador na emissão do documento;"
                "valor_nota_fiscal: valor monetário total do documento na moeda Real do Brasil;"
                "numero_produto: número de ordem do produto no documento, não utilizado para cálculo, somente para busca, ordenação ou identificação;"
                "descricao_do_produto_servico: nome ou descrição relacionado ao produto ou serviço adquirido pelo destinatário do documento;"
                "codigo_ncm_sh: código de classificação do tipo de produto ou serviço para fins fiscais (NCM - Nomenclatura Comum do Mercosul ou SH – Sistema Harmonizado), não utilizado para cálculo, somente para busca, ordenação ou identificação;"
                "ncm_sh_tipo_de_produto: descrição do tipo de produto ou serviço para fins fiscais (NCM - Nomenclatura Comum do Mercosul ou SH – Sistema Harmonizado);"
                "cfop: o Código Fiscal de Operações e Prestações (CFOP) trata-se de um sistema de códigos usado no Brasil para identificar e classificar as diversas naturezas de operações e prestações de serviços sujeitas à incidência do Imposto sobre Circulação de Mercadorias e Serviços (ICMS), não utilizado para cálculo, somente para busca, ordenação ou identificação;"
                "quantidade: valor numérico para cálculo, tendo como dimensão o campo UNIDADE;"
                "unidade: dimensão relacionada ao valor do campo QUANTIDADE;"
                "valor_unitario: valor monetário da unidade (quantidade = 1) do produto ou serviço especificado, na moeda Real do Brasil;"
                "valor_total: valor total calculado do produto ou serviço, multiplicando os campos QUANTIDADE e VALOR UNITÁRIO, resultando  em valor monetário na moeda Real do Brasil;"
            ),
            tools=[sql_generator_tool, metadata_query_tool], # Passa as funções das ferramentas
            verbose=True,
            allow_delegation=False, # Não delega, pois é o responsável primário pela geração de consultas
            llm=self.llm
        )

        # 3. Defina a Tarefa
        # A tarefa é que o agente decida qual ferramenta usar e gere o código.
        # O prompt precisa ser muito claro para que ele gere o código e não apenas uma descrição.
        analyze_and_generate_task = Task(
            description=f"""
            Analise a seguinte pergunta do usuário: "{question}".

            **Contexto das tabelas SQLite e seus esquemas:**
            {table_schemas_context}

            Com base nesta pergunta e no contexto, você deve fazer o seguinte:
            1. **Se a pergunta for sobre os DADOS das tabelas** (ex: "Quantas notas?", "Qual o valor total?"), use o `sql_generator_tool` para gerar um comando SQL.
            2. **Se a pergunta for sobre os METADADOS/ESTRUTURA das tabelas** (ex: "Quais tabelas existem?", "Quais colunas tem 'faturas'?"), use o `metadata_query_tool` para gerar um código Python.

            Sua saída deve ser **APENAS o código gerado (SQL ou Python)**, sem introdução, explicações ou qualquer texto adicional.
            A ferramenta que você escolher (sql_generator_tool ou metadata_query_tool) irá lidar com a execução do LLM para gerar o código.
            Apenas chame a ferramenta apropriada com a pergunta e o contexto (se aplicável) e retorne o resultado bruto da ferramenta.
            """,
            expected_output=(
                "O comando SQL puro ou o código Python puro gerado pela ferramenta apropriada (sql_generator_tool ou metadata_query_tool), "
                "sem qualquer texto explicativo adicional. Por exemplo: 'SELECT COUNT(*) FROM tabela;' ou 'all_metadata_df.head()'."
                "Se nenhuma tabela estiver carregada, a saída esperada é 'Não há metadados de tabelas carregados no momento.'"
            ),
            tools=[sql_generator_tool, metadata_query_tool], # Ambas as ferramentas são relevantes para esta tarefa
            agent=query_analyzer_agent
        )

        # 4. Crie a Crew (apenas com este agente para esta parte do fluxo)
        crew = Crew(
            agents=[query_analyzer_agent],
            tasks=[analyze_and_generate_task],
            verbose=True,
            process=Process.sequential # Apenas uma tarefa aqui, mas manter para consistência
        )

        # 5. Inicie o processo da Crew
        try:
            generated_code = crew.kickoff(inputs={"question": question})
            app_logger.info(f"QueryAnalyzerAgent: Código gerado pela CrewAI: \n```\n{generated_code}\n```")
            return generated_code
        except Exception as e:
            app_logger.error(f"QueryAnalyzerAgent: Erro durante a geração do código pela Crew: {e}", exc_info=True)
            raise # Re-lança o erro
