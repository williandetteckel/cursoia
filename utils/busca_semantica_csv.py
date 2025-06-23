import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.tools import Tool
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.schema import Document


def tool_busca_semantica_csv(path_csv: str) -> Tool:
    df = pd.read_csv(path_csv)

    # Remove colunas com objetos complexos e converte tudo pra string
    df = df.astype(str)

    # Cria documentos com base no DataFrame
    loader = DataFrameLoader(df, page_content_column=df.columns[0])  # Usa a primeira coluna como conteúdo base
    documents = loader.load()

    # Garante que page_content é texto simples
    for d in documents:
        if not isinstance(d.page_content, str):
            d.page_content = str(d.page_content)

    embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")

    vectordb = FAISS.from_documents(documents, embeddings)

    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatGroq(model="llama3-8b-8192", temperature=0.2),
        retriever=vectordb.as_retriever()
    )

    return Tool(
        name="PerguntarSobreNotas",
        func=qa_chain.run,
        description="Use para responder perguntas sobre o conteúdo da nota fiscal CSV carregada.",
        return_direct=True
    )
