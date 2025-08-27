from datetime import date
from dotenv import load_dotenv

# Importações da Agno (usando o caminho mais comum e simples)
from agno.agent import Agent
from agno.team import Team
from agno.models.groq import Groq

# Importa as ferramentas dos seus arquivos de agentes
# Garanta que a pasta 'agentes' tenha um arquivo __init__.py vazio
from agentes.agente_vr import executar_calculo_final_vr
from agentes.agente_tools import (
    carregar_arquivo_para_db,
    carregar_todos_os_arquivos_de_uma_pasta,
    gerar_calendario_de_dias_uteis,
    exportar_tabela_para_excel,
    auditar_processo_de_calculo
)

load_dotenv()

# --- 1. DEFINIÇÃO DOS AGENTES ESPECIALISTAS (WORKERS) ---
# Suas definições para os workers estão perfeitas.

data_engineer_agent = Agent(
    name="Engenheiro_de_Dados",
    model=Groq(id="llama3-8b-8192"),
    tools=[
        carregar_arquivo_para_db,
        carregar_todos_os_arquivos_de_uma_pasta,
        gerar_calendario_de_dias_uteis,
        exportar_tabela_para_excel
    ],
    description="""Você é o 'Engenheiro de Dados', um agente de IA especialista em ETL. Sua missão é gerenciar o fluxo de dados entre arquivos e um banco de dados SQLite, incluindo carregar, gerar e exportar dados."""
)

rh_analyst_agent = Agent(
    name="Analista_de_RH",
    model=Groq(id="llama3-70b-8192"),
    tools=[executar_calculo_final_vr, auditar_processo_de_calculo ],
    description="""Você é um Analista de RH especialista em regras de negócio. 
    Sua função é executar o cálculo final e completo do benefício de VR, lendo os dados que já estão no banco de dados.
    Você também pode auditar o processo de cálculo para garantir que tudo esteja correto.
    """
)

# --- 2. DEFINIÇÃO DO AGENTE GERENTE (A PEÇA CENTRAL) ---
# Este agente não tem ferramentas de trabalho. Sua única função é delegar.
# As instruções detalhadas pertencem a ele.

# manager_agent = Agent(
#     name="Gerente_RH",
#     model=Groq(id="llama3-70b-8192"),
#     tools=[], # O gerente não tem ferramentas de execução
#     description=f"""Você é o Gerente de uma equipe de agentes de IA de alta performance para o departamento de RH. Hoje é {date.today().strftime('%d de %B de %Y')}.
# Sua responsabilidade é analisar os pedidos do usuário e delegar as tarefas para o especialista correto em sua equipe.

# **Sua Equipe de Especialistas:**
# - **Engenheiro_de_Dados:** Delegue para ele QUALQUER tarefa relacionada a carregar arquivos, gerar calendários e exportar tabelas.
# - **Analista_de_RH:** Delegue para ele QUALQUER tarefa relacionada a executar o cálculo final do VR.

# **Seu Fluxo de Trabalho (SOP):**
# 1. Receba o pedido do usuário.
# 2. Determine qual especialista é o mais qualificado para a tarefa.
# 3. Delegue a tarefa. Para pedidos complexos (ex: "carregue e depois calcule"), orquestre a sequência de delegações.
# 4. Comunique o resultado final da operação de forma clara para o usuário.
# """
# )

# --- 3. MONTAGEM DA EQUIPE (A ESTRUTURA CORRETA) ---
# A Team é criada com os papéis claros de 'manager' e 'workers'.
# Ela não tem sua própria 'description' ou 'model', pois usa os do gerente.

team = Team(
    name="Equipe_RH",
    mode="coordinate",  # Usamos o modo de roteamento
    model=Groq(id="llama3-70b-8192"),
    members=[
        data_engineer_agent,
        rh_analyst_agent,
    ],
    # As instruções agora pertencem à Equipe, que as usará para rotear a tarefa.
    instructions=[f"""Você é um Roteador de tarefas de alta precisão para uma equipe de RH. Sua única função é analisar o pedido do usuário e roteirizá-lo para o especialista correto, SEM EXCEÇÃO.

**Regras de Roteamento Estritas:**
- Se o pedido do usuário envolver as palavras-chave **'carregar', 'importar', 'salvar arquivo', 'exportar', 'excel', 'calendário'**, roteirize IMEDIATAMENTE para o **Engenheiro_de_Dados**.
- Se o pedido do usuário envolver as palavras-chave **'calcular', 'processar vr', 'executar o cálculo', 'análise', 'resultado final'**, roteirize IMEDIATAMENTE para o **Analista_de_RH**.

Analise as palavras-chave no pedido do usuário e escolha o especialista cujo papel corresponde à tarefa. Não tente executar a tarefa você mesmo. Apenas roteirize.
"""]
)

# --- 4. LOOP DE CHAT (CORRIGIDO) ---
if __name__ == "__main__":
    print("🤖 Equipe de Agentes de RH iniciada. Fale com o Gerente.")
    print("Ex: 'Carregue os arquivos da pasta dados_para_teste e depois execute o cálculo para o mês 5 de 2025'")

    while True:
        try:
            prompt = input("Você: ")
            if prompt.lower() == 'sair':
                print("Encerrando a sessão. Adeus!")
                break

            # Interagimos com a equipe toda através do método .run()
            response = team.run(prompt)
            print("-" * 60)
            # CORREÇÃO: A resposta é um texto direto, não um objeto com .content
            print(f"Gerente: {response.content}")

        except KeyboardInterrupt:
            print("\nSessão encerrada pelo usuário. Adeus!")
            break
        except Exception as e:
            print(f"Erro inesperado: {e}")
            break
