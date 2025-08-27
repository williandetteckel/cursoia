# Agente de IA para Automação de Cálculo de Benefícios (VR)
Este projeto implementa um sistema multiagente de IA, construído com as frameworks Agno e Groq, para automatizar completamente o processo de cálculo de Vale Refeição (VR) de uma empresa. O sistema gere todo o ciclo de vida dos dados: ingestão de ficheiros, geração de dados de referência, limpeza, aplicação de regras de negócio complexas, cálculo, auditoria e exportação.

## 🎯 Objetivo do Projeto
O objetivo principal é substituir um processo manual, demorado e sujeito a erros de cálculo de VR, que dependia da consolidação de múltiplas folhas de cálculo. O sistema de agentes automatiza essa tarefa, garantindo precisão, velocidade e rastreabilidade.

## 🏛️ Arquitetura
A solução é baseada numa Equipa de Agentes (agno.Team) com uma estrutura de roteamento, onde a própria equipa atua como um orquestrador inteligente que delega tarefas para agentes especialistas.

Equipa_RH (Roteador): É a interface principal com o utilizador. Ele recebe os pedidos, entende o objetivo geral e encaminha a tarefa para o especialista correto na sua equipa.

Engenheiro_de_Dados (Especialista): Responsável por operações de ETL (Extração, Transformação e Carga). As suas habilidades incluem carregar dados de ficheiros (.xlsx, .csv), gerar calendários de referência e exportar os resultados para Excel.

Analista_de_RH (Especialista): Responsável pela lógica de negócio. A sua habilidade é executar o cálculo final e completo do benefício, aplicando todas as regras de exclusão e de negócio sobre os dados já presentes na base de dados, além de auditar os resultados.

## ✨ Funcionalidades (Habilidades do Agente)
A equipa de agentes, em conjunto, é capaz de:

Carregar Dados: Ler ficheiros .xlsx e .csv e guardá-los como tabelas numa base de dados SQLite, padronizando nomes de tabelas/colunas e normalizando valores.

Carga em Lote: Carregar todos os ficheiros de uma pasta de uma só vez.

Gerar Calendário: Criar uma tabela de calendário para qualquer período, identificando dias úteis e feriados (baseado nos feriados nacionais e de São Paulo).

Executar Cálculo de VR: Aplicar todas as regras de negócio complexas para calcular o valor do VR de cada colaborador elegível.

Auditar o Processo: Validar o resultado do cálculo contra uma checklist de regras para garantir a precisão e conformidade.

Exportar Resultados: Guardar qualquer tabela da base de dados num ficheiro .xlsx.

## 📂 Estrutura de Ficheiros do Projeto
```
├── agentes/
│   ├── __init__.py
│   ├── agente_tools.py      # Contém as funções-ferramenta de carga e calendário
│   └── agente_vr.py         # Contém a ferramenta de cálculo final e auditoria
├── app.py                   # Ponto de entrada principal (executa a equipa)
├── dados_para_teste/        # Pasta para colocar os ficheiros de dados
│   ├── ATIVOS.xlsx
│   └── ...
├── .env                     # Ficheiro para as chaves de API (NÃO versionar)
├── .gitignore               # Ficheiros a serem ignorados pelo Git
├── README.md                # Este ficheiro
└── requirements.txt         # Dependências do projeto
```
## 🚀 Instalação e Configuração
Siga os passos abaixo para executar o projeto localmente.

1. Clone o Repositório (se estiver no Git)

`git clone [URL_DO_SEU_REPOSITORIO]
cd [NOME_DA_PASTA]`

2. Crie o Ficheiro de Ambiente (.env)
Na raiz do projeto, crie um ficheiro chamado .env e adicione a sua chave da API da Groq:

`GROQ_API_KEY="a_sua_chave_secreta_aqui"`

3. Instale as Dependências
Certifique-se de que tem o Python 3.10+ instalado. Em seguida, instale todas as bibliotecas necessárias:

`pip install -r requirements.txt`

## ▶️ Como Executar o Agente
Para iniciar a interface de chat com a equipa de agentes, execute o ficheiro principal no seu terminal:

`python app.py`

## 💬 Como Usar (Exemplos de Comandos)
Converse com a Equipa_RH usando linguagem natural.

Para preparar os dados:

`Carregue todos os ficheiros da pasta dados_para_teste
Gere o calendário de dias úteis de 2025-04-15 até 2025-05-15`

Para executar o cálculo:

`Execute o cálculo final do VR para o mês 5 do ano 2025`

Para auditar o resultado:

`Agora, audite o processo de cálculo para o mês 5 de 2025`

Para exportar uma tabela:

`Exporte a tabela resultado_vr_2025_05 para um ficheiro excel`

Exemplo de um comando complexo (multi-etapas):

`Prepare o ambiente para maio de 2025: carregue os ficheiros da pasta dados_para_teste e gere o calendário. Depois, execute o cálculo final e, por fim, audite o processo.`

## 🛠️ Tecnologias Utilizadas

* Python 3

* Agno: Framework para construção e orquestração de agentes de IA.

* Groq: Plataforma de inferência de LLMs para o "cérebro" dos agentes (Llama 3).

* Pandas: Para manipulação e análise de dados.

* SQLAlchemy: Para interação com a base de dados SQLite.

* Holidays: Biblioteca para consulta de feriados no Brasil.