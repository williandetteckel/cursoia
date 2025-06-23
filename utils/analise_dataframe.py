from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import Tool


def criar_tool_analise_pandas(df, llm):
    """
    Cria uma ferramenta do LangChain para permitir consultas em linguagem natural 
    sobre um DataFrame do pandas, útil para explorar dados de notas fiscais.

    Args:
        df (pd.DataFrame): O DataFrame carregado com os dados.
        llm: O modelo de linguagem (como ChatGroq ou OpenAI).

    Returns:
        Tool: Ferramenta pronta para ser usada em um agente LangChain.
    """

    agent_pandas = create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        verbose=True,
        handle_parsing_errors=True,
        allow_dangerous_code=True,
        return_direct=True
    )

    return Tool(
        name="PerguntarSobreDataFrame",
        func=lambda query: agent_pandas.run(query),
        description=(
            "Use esta ferramenta para responder perguntas sobre os dados da planilha carregada. "
            "Ela entende linguagem natural e pode realizar análises como somatórios, filtragens, "
            "agrupamentos, contagens, médias, ou listagens, com base nos dados disponíveis no DataFrame."
        )
    )
