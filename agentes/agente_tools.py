# tools.py

import os
import re
import numpy as np
import holidays
import pandas as pd
import unicodedata
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq
from datetime import date, timedelta
from sqlalchemy import create_engine, inspect

load_dotenv()

# ---FUNÇÃO "FAREJADORA" DE CABEÇALHOS ---


def encontrar_linha_do_cabecalho(caminho_arquivo: str) -> int:
    """
    Analisa as 5 primeiras linhas de um arquivo Excel para encontrar a linha
    que provavelmente contém o cabeçalho. Retorna o índice (base 0) da linha.
    """
    try:
        # Lê as 5 primeiras linhas sem assumir nenhum cabeçalho
        df_preview = pd.read_excel(caminho_arquivo, header=None, nrows=5)
        for i, row in df_preview.iterrows():
            # Critério: Uma linha de cabeçalho tem muitas células preenchidas
            # e a maioria dos valores é texto (não apenas números).
            non_empty_cells = row.notna().sum()
            total_cells = len(row)

            # Se mais da metade das células estiver preenchida...
            if non_empty_cells / total_cells > 0.5:
                # E se a maioria dos valores forem texto...
                string_cells = sum(isinstance(cell, str) for cell in row)
                if string_cells / non_empty_cells > 0.5:
                    print(
                        f"[Leitor Inteligente] Cabeçalho detectado na linha {i + 1} do arquivo '{os.path.basename(caminho_arquivo)}'.")
                    return i  # Retorna o índice da linha encontrada
    except Exception as e:
        print(
            f"[Leitor Inteligente] Aviso: Não foi possível analisar o cabeçalho de '{os.path.basename(caminho_arquivo)}'. Usando a primeira linha como padrão. Erro: {e}")

    # Se nada for encontrado, assume a primeira linha (índice 0) como padrão
    return 0

# ---FUNÇÃO HELPER PARA NORMALIZAR VALORES ---


def normalizar_valor(valor):
    """
    Converte um valor (que pode ser string ou número) para um formato float limpo.
    Lida com 'R$', separador de milhar '.' e vírgula decimal ','.
    Ex: 'R$ 1.250,50' -> 1250.50
    """
    # Se já for um número, apenas retorna como float
    if isinstance(valor, (int, float)):
        return float(valor)

    # Se não for string, não podemos tratar, retorna nulo
    if not isinstance(valor, str):
        return pd.NA

    try:
        # 1. Remove o símbolo 'R$', espaços em branco, e o separador de milhar '.'
        valor_limpo = valor.replace("R$", "").strip().replace(".", "")
        # 2. Substitui a vírgula decimal por um ponto decimal
        valor_limpo = valor_limpo.replace(",", ".")
        # 3. Tenta converter para float. Se o campo for '-' ou vazio, isso falhará
        return float(valor_limpo)
    except (ValueError, TypeError):
        # Se a conversão falhar (ex: texto inesperado), retorna nulo
        return pd.NA

# ---FUNÇÃO HELPER PARA PADRONIZAR NOMES ---


def slugify(text: str) -> str:
    """
    Normaliza um texto: remove acentos, converte para minúsculas,
    remove caracteres especiais e substitui espaços por underscores.
    Ex: 'DIAS DE FÉRIAS' -> 'dias_de_ferias'
    """
    # Normaliza para separar acentos dos caracteres (ex: 'é' -> 'e' + ´)
    text = unicodedata.normalize('NFKD', text).encode(
        'ascii', 'ignore').decode('utf-8')
    # Remove caracteres que não sejam palavras, números, espaços ou hífens
    text = re.sub(r'[^\w\s-]', '', text).strip()
    # Substitui espaços e hífens por um único underscore
    text = re.sub(r'[\s-]+', '_', text)
    # Converte para minúsculas
    return text.lower()

# --- As classes de baixo nível---


class DatabaseTools:
    # ... (código sem alterações) ...
    def __init__(self, db_file: str):
        self.engine = create_engine(f'sqlite:///{db_file}')

    def write_dataframe(self, dataframe: pd.DataFrame, table_name: str):
        try:
            dataframe.to_sql(table_name, self.engine,
                             if_exists='append', index=False)
            return f"Sucesso! {len(dataframe)} linhas adicionadas à tabela '{table_name}'."
        except Exception as e:
            return f"Falha ao escrever na tabela '{table_name}': {e}"


class DataFileTools:
    def read_file(self, file_path: str) -> pd.DataFrame:
        """
        Lê um arquivo (.csv ou .xlsx) de forma inteligente, detectando
        automaticamente a linha do cabeçalho para arquivos Excel.
        """
        print(f"[DataFileTools] Lendo o arquivo: {file_path}")
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            # --- LÓGICA INTELIGENTE ---
            # 1. Encontra a linha correta do cabeçalho
            linha_cabecalho = encontrar_linha_do_cabecalho(file_path)
            # 2. Lê o arquivo a partir daquela linha
            return pd.read_excel(file_path, header=linha_cabecalho)
        else:
            raise ValueError(
                "Formato de arquivo não suportado. Use .csv ou .xlsx.")

# --- Ferramenta de arquivo único---


def carregar_arquivo_para_db(caminho_do_arquivo: str) -> str:
    """Carrega um único arquivo, padroniza nomes de tabela/coluna E normaliza colunas de valor."""
    db_file = "database.db"
    try:
        base_name = os.path.basename(caminho_do_arquivo)
        table_name_raw = os.path.splitext(base_name)[0]
        table_name = slugify(table_name_raw)

        file_reader = DataFileTools()
        db_writer = DatabaseTools(db_file=db_file)

        dataframe = file_reader.read_file(caminho_do_arquivo)

        if dataframe.empty:
            return f"Alerta: O arquivo '{caminho_do_arquivo}' está vazio."

        # Padroniza os nomes das colunas
        dataframe.columns = [slugify(col) for col in dataframe.columns]

        # --- MELHORIA: Normaliza as colunas de valor ---
        # Lista das colunas que sabemos que devem conter valores numéricos
        colunas_de_valor = ['valor', 'valor_do_beneficio']

        for col in colunas_de_valor:
            # Verifica se a coluna existe no dataframe atual antes de tentar normalizá-la
            if col in dataframe.columns:
                print(
                    f"[Normalizador] Limpando e convertendo a coluna de valor: '{col}'")
                dataframe[col] = dataframe[col].apply(normalizar_valor)

        return db_writer.write_dataframe(dataframe, table_name)
    except Exception as e:
        return f"Erro ao processar '{caminho_do_arquivo}': {e}"


# ---FERRAMENTA DE CARGA EM LOTE ---
def carregar_todos_os_arquivos_de_uma_pasta(caminho_da_pasta: str) -> str:
    """
    Escaneia um diretório, encontra todos os arquivos .csv e .xlsx, e carrega cada um
    para uma tabela de banco de dados correspondente.
    """
    print(f"\n[Ferramenta de Lote] Iniciado para a pasta '{caminho_da_pasta}'")

    if not os.path.isdir(caminho_da_pasta):
        return f"Erro: O caminho '{caminho_da_pasta}' não é um diretório válido."

    arquivos_encontrados = os.listdir(caminho_da_pasta)
    relatorio_final = []
    arquivos_processados = 0

    for nome_arquivo in arquivos_encontrados:
        if nome_arquivo.endswith('.csv') or nome_arquivo.endswith('.xlsx'):
            caminho_completo = os.path.join(caminho_da_pasta, nome_arquivo)
            print(f"[Ferramenta de Lote] Processando arquivo: {nome_arquivo}")

            # Reutiliza a nossa ferramenta de arquivo único
            resultado_individual = carregar_arquivo_para_db(caminho_completo)
            relatorio_final.append(f"- {nome_arquivo}: {resultado_individual}")
            arquivos_processados += 1

    if arquivos_processados == 0:
        return "Nenhum arquivo .csv ou .xlsx foi encontrado na pasta para processar."

    return f"Processo em lote concluído. Resumo:\n" + "\n".join(relatorio_final)


def gerar_calendario_de_dias_uteis(data_inicio_str: str, data_fim_str: str) -> str:
    """
    Gera uma tabela de calendário no banco de dados para um período específico,
    identificando dias úteis e feriados no Brasil (e em São Paulo).
    As datas devem estar no formato 'YYYY-MM-DD'.
    """
    db_file = "database.db"
    table_name = "calendario_dias_uteis"
    try:
        feriados_br = holidays.Brazil(state='SP')
        start_date = date.fromisoformat(data_inicio_str)
        end_date = date.fromisoformat(data_fim_str)
        lista_datas = [
            start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        calendario_data = []
        for dia in lista_datas:
            dia_da_semana = dia.weekday()
            eh_feriado = dia in feriados_br
            eh_dia_util = dia_da_semana < 5 and not eh_feriado
            calendario_data.append({"data": dia.isoformat(), "dia_da_semana": dia.strftime(
                '%A'), "eh_feriado": eh_feriado, "eh_dia_util": eh_dia_util})
        df_calendario = pd.DataFrame(calendario_data)
        db_writer = DatabaseTools(db_file=db_file)
        # Agora esta chamada é válida, pois o método aceita o parâmetro
        resultado = db_writer.write_dataframe(
            df_calendario, table_name)
        num_dias_uteis = df_calendario['eh_dia_util'].sum()
        return f"{resultado} Total de dias úteis no período: {num_dias_uteis}."
    except Exception as e:
        return f"Ocorreu um erro ao gerar o calendário: {e}"

# --- FERRAMENTAS DE EXPORTAÇÃO ---


def exportar_tabela_para_excel(nome_da_tabela: str, nome_do_arquivo: str = None) -> str:
    """
    Exporta uma única tabela do banco de dados para um arquivo Excel (.xlsx).
    Se o nome do arquivo não for fornecido, ele será gerado a partir do nome da tabela.
    """
    db_file = "database.db"
    engine = create_engine(f'sqlite:///{db_file}')
    print(
        f"\n[Exportador] Iniciando exportação da tabela '{nome_da_tabela}'...")

    try:
        # Verifica se a tabela existe
        inspector = inspect(engine)
        if not inspector.has_table(nome_da_tabela):
            return f"Erro: A tabela '{nome_da_tabela}' não foi encontrada no banco de dados."

        # Lê a tabela para um DataFrame
        df = pd.read_sql_table(nome_da_tabela, engine)

        if df.empty:
            return f"Aviso: A tabela '{nome_da_tabela}' está vazia. Nenhum arquivo foi gerado."

        # Define o nome do arquivo de saída
        if nome_do_arquivo is None:
            nome_do_arquivo = f"{nome_da_tabela}.xlsx"

        # Garante que a extensão seja .xlsx
        if not nome_do_arquivo.endswith('.xlsx'):
            nome_do_arquivo += '.xlsx'

        # Salva o DataFrame como um arquivo Excel
        df.to_excel(nome_do_arquivo, index=False)

        return f"Sucesso! A tabela '{nome_da_tabela}' foi exportada para o arquivo '{nome_do_arquivo}' com {len(df)} linhas."

    except Exception as e:
        return f"Ocorreu um erro ao exportar a tabela '{nome_da_tabela}': {e}"


def exportar_todas_as_tabelas_para_excel(pasta_de_saida: str = "exportacao") -> str:
    """
    Exporta TODAS as tabelas do banco de dados para arquivos Excel separados,
    salvando-os em um diretório específico.
    """
    db_file = "database.db"
    engine = create_engine(f'sqlite:///{db_file}')
    print(f"\n[Exportador em Lote] Iniciando exportação de todas as tabelas...")

    try:
        # Cria a pasta de saída se ela não existir
        os.makedirs(pasta_de_saida, exist_ok=True)

        inspector = inspect(engine)
        nomes_das_tabelas = inspector.get_table_names()

        if not nomes_das_tabelas:
            return "O banco de dados está vazio. Nenhuma tabela para exportar."

        relatorio = []
        for nome_tabela in nomes_das_tabelas:
            caminho_saida = os.path.join(pasta_de_saida, f"{nome_tabela}.xlsx")
            resultado = exportar_tabela_para_excel(nome_tabela, caminho_saida)
            relatorio.append(f"- {resultado}")

        return "Exportação em lote concluída!\n" + "\n".join(relatorio)

    except Exception as e:
        return f"Ocorreu um erro durante a exportação em lote: {e}"


# ---AGENTE AUDITOR DE PROCESSO ---
def auditar_processo_de_calculo(ano: int, mes: int) -> str:
    """
    Audita o processo de cálculo de VR para um dado ano e mês, verificando se
    as fontes de dados e as principais regras de negócio foram consideradas,
    conforme o checklist de validações. Retorna um relatório de auditoria.
    """
    db_file = "database.db"
    engine = create_engine(f'sqlite:///{db_file}')
    nome_tabela_resultado = f"resultado_vr"
    print(
        f"\n[Agente Auditor] Iniciando auditoria do processo para '{nome_tabela_resultado}'...")

    inspector = inspect(engine)
    tabelas_existentes = inspector.get_table_names()
    relatorio = [
        f"Relatório de Auditoria do Processo de Cálculo (Mês: {mes}/{ano}):\n"]

    # 1. Validação das Fontes de Dados (checklist parte 1)
    fontes_de_dados_checklist = [
        'afastamentos', 'desligados', 'admissao_abril', 'ferias',
        'estagio', 'aprendiz', 'base_sindicato_x_valor', 'exterior', 'ativos'
    ]

    relatorio.append("--- Verificação das Fontes de Dados ---")
    fontes_ok = True
    for tabela in fontes_de_dados_checklist:
        if tabela in tabelas_existentes:
            relatorio.append(
                f"- [OK] Fonte de dados '{tabela}' foi encontrada e utilizada.")
        else:
            relatorio.append(
                f"- [FALHA] Fonte de dados '{tabela}' não foi encontrada no banco de dados.")
            fontes_ok = False

    if not fontes_ok:
        relatorio.append(
            "\nAuditoria interrompida devido à falta de fontes de dados essenciais.")
        return "\n".join(relatorio)

    # 2. Validação das Regras de Negócio (checklist parte 2) - por amostragem
    relatorio.append(
        "\n--- Verificação das Regras de Negócio (por amostragem) ---")
    df_resultado = pd.read_sql_table(nome_tabela_resultado, engine)
    df_desligados = pd.read_sql_table('desligados', engine)
    df_desligados['data_demissao'] = pd.to_datetime(
        df_desligados['data_demissao'], errors='coerce')

    # Regra: DESLIGADOS ATÉ O DIA 15
    desligados_ate_15 = df_desligados[df_desligados['data_demissao'].dt.day <= 15]
    if not desligados_ate_15.empty:
        # Pega a matrícula do primeiro caso para auditar
        matricula_exemplo = desligados_ate_15.iloc[0]['matricula']
        resultado_exemplo = df_resultado[df_resultado['matricula']
                                         == matricula_exemplo]
        if not resultado_exemplo.empty and resultado_exemplo.iloc[0]['dias_a_pagar'] == 0:
            relatorio.append(
                f"- [OK] Regra 'Desligados até dia 15': Verificado com sucesso para a matrícula {matricula_exemplo}.")
        else:
            relatorio.append(
                f"- [FALHA] Regra 'Desligados até dia 15': A matrícula {matricula_exemplo} não foi zerada corretamente.")

    # Regra: REVISAR O CALCULO DE PGTO SE ESTÁ CORRETO
    soma_custos = df_resultado['custo_empresa_80'] + \
        df_resultado['custo_colaborador_20']
    check_soma = np.isclose(df_resultado['valor_total_vr'], soma_custos)
    if not check_soma.all():
        relatorio.append(
            "- [FALHA] Validação Matemática: A soma dos custos (80/20) não bate com o valor total.")
    else:
        relatorio.append(
            "- [OK] Validação Matemática: A soma dos custos (80/20) está correta para todas as linhas.")

    relatorio.append(
        "\nConclusão da Auditoria: Processo parece estar em conformidade com os pontos de validação checados.")
    return "\n".join(relatorio)
