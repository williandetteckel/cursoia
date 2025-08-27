import pandas as pd
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv
from sqlalchemy import create_engine
from .agente_tools import DatabaseTools

load_dotenv()

# --- FERRAMENTA FINAL: AGENTE DE CÁLCULO INTELIGENTE ---


def executar_calculo_final_vr(ano: int, mes: int) -> str:
    db_file = "database.db"
    engine = create_engine(f'sqlite:///{db_file}')
    print(f"\n[Agente de Cálculo] Iniciando processo para {ano}-{mes:02d}...")

    # --- 1. CHECKLIST E CARREGAMENTO (sem alterações) ---
    # ... (código do checklist e carregamento) ...
    inspector = inspect(engine)
    tabelas_existentes = inspector.get_table_names()
    tabelas_necessarias = ['ativos', 'ferias', 'desligados', 'admissao_abril', 'base_sindicato_x_valor',
                           'calendario_dias_uteis', 'aprendiz', 'estagio', 'exterior', 'afastamentos']
    tabelas_faltando = [
        t for t in tabelas_necessarias if t not in tabelas_existentes]
    if tabelas_faltando:
        return f"Pré-requisitos falharam. Tabelas faltando: {', '.join(tabelas_faltando)}."
    df_ativos = pd.read_sql_table('ativos', engine)
    df_ferias = pd.read_sql_table('ferias', engine)
    df_sindicato = pd.read_sql_table('base_sindicato_x_valor', engine)
    df_aprendiz = pd.read_sql_table('aprendiz', engine)
    df_estagio = pd.read_sql_table('estagio', engine)
    df_exterior = pd.read_sql_table('exterior', engine)
    df_afastados = pd.read_sql_table('afastamentos', engine)

    # --- 2. LÓGICA DE LIMPEZA (sem alterações) ---
    # ... (código da limpeza) ...
    matriculas_para_excluir = set()
    matriculas_para_excluir.update(df_aprendiz['matricula'].dropna().unique())
    matriculas_para_excluir.update(df_estagio['matricula'].dropna().unique())
    matriculas_para_excluir.update(df_exterior['cadastro'].dropna().unique())
    matriculas_para_excluir.update(df_afastados['matricula'].dropna().unique())
    df_elegiveis = df_ativos[~df_ativos['matricula'].isin(
        matriculas_para_excluir)].copy()
    filtro_diretores = df_elegiveis['titulo_do_cargo'].str.contains(
        'diretor', case=False, na=False)
    df_elegiveis = df_elegiveis[~filtro_diretores]

    # --- 3. LÓGICA DE CÁLCULO (com o novo diagnóstico) ---
    print("[Agente de Cálculo] Iniciando etapa de Cálculo...")
    df_elegiveis['dias_a_pagar'] = 22
    df_final = pd.merge(df_elegiveis, df_ferias[[
                        'matricula', 'dias_de_ferias']], on='matricula', how='left')
    df_final['dias_de_ferias'].fillna(0, inplace=True)
    df_final['dias_a_pagar'] -= df_final['dias_de_ferias']

    # a) Criar chave de junção na tabela de Sindicatos/Valores
    mapa_estados_para_sigla = {
        'São Paulo': 'SP',
        'Rio de Janeiro': 'RJ',
        'Rio Grande do Sul': 'RS',
        'Paraná': 'PR'
    }
    df_sindicato['chave_estado'] = df_sindicato['estado'].map(
        mapa_estados_para_sigla)

    # b) Criar chave de junção na tabela de Ativos
    df_final['chave_estado'] = df_final['sindicato'].str.extract(
        r'\b(SP|RS|PR|RJ)\b', expand=False)

    # --- INÍCIO DO DIAGNÓSTICO DE JUNÇÃO ---
    print("\n--- DIAGNÓSTICO DE JUNÇÃO ---")
    print("\n[DIAGNÓSTICO] Verificando as chaves de junção ('chave_estado') antes do merge:")

    # Mostra as chaves criadas na tabela de sindicatos
    print("\nChaves na tabela de Sindicatos (df_sindicato):")
    print(df_sindicato[['estado', 'chave_estado']].to_string())

    # Mostra as chaves extraídas da tabela de ativos/final
    print("\nChaves extraídas da tabela de Colaboradores (df_final):")
    chaves_extraidas_validas = df_final['chave_estado'].notna().sum()
    total_colaboradores = len(df_final)
    print(f"  - {chaves_extraidas_validas} de {total_colaboradores} colaboradores tiveram uma chave de estado extraída.")
    print("  - Amostra das chaves extraídas (as 10 primeiras):")
    print(df_final[['sindicato', 'chave_estado']].head(10).to_string())
    print("--- FIM DO DIAGNÓSTICO DE JUNÇÃO ---\n")
    # --- FIM DO DIAGNÓSTICO DE JUNÇÃO ---

    # c) Fazer o merge usando a nova CHAVE_ESTADO
    df_final = pd.merge(df_final, df_sindicato, on='chave_estado', how='left')

    # d) Calcula o Valor Final
    df_final['dias_a_pagar'] = df_final['dias_a_pagar'].clip(lower=0)
    df_final['valor_total_vr'] = df_final['dias_a_pagar'] * df_final['valor']
    df_final['custo_empresa_80'] = df_final['valor_total_vr'] * 0.8
    df_final['custo_colaborador_20'] = df_final['valor_total_vr'] * 0.2

    # --- 4. SALVAR RESULTADO ---
    # ... (código para salvar o resultado sem alterações) ...
    nome_tabela_resultado = f"resultado_vr"
    db_writer = DatabaseTools(db_file=db_file)
    resultado_escrita = db_writer.write_dataframe(
        df_final, nome_tabela_resultado)
    custo_total = df_final['valor_total_vr'].fillna(0).sum()
    return f"Cálculo concluído! {resultado_escrita}. O custo total para a empresa foi de R$ {custo_total:,.2f}."
