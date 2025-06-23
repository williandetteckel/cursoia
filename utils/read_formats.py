import os
import json
import zipfile
import pandas as pd
import streamlit as st
from langchain_community.document_loaders.csv_loader import CSVLoader

# 📄 Lê arquivos .txt


def read_txt(path: str) -> str:
    """
    Reads the content of a .txt file.

    Args:
        path (str): Path to the .txt file.
    Returns:
        str: Content of the file.
    """
    if not os.path.isfile(path) or not path.endswith(".txt"):
        return "❌ Arquivo inválido ou não é .txt"
    with open(path, "r", encoding="utf-8") as f:
        return f.read(3).to_json(orient="records", force_ascii=False)


def read_csv(path: str) -> str:
    """
    Lê o conteúdo de um arquivo .csv e retorna as primeiras linhas em JSON.

    Args:
        path (str): Caminho para o arquivo .csv

    Returns:
        str: JSON com os dados do arquivo ou mensagem de erro
    """
    if not os.path.isfile(path) or not path.endswith(".csv"):
        return "❌ Arquivo inválido ou não é .csv"
    df = pd.read_csv(path)
    st.session_state["ultimo_csv_path"] = path
    return df.to_json(orient="records", force_ascii=False)

# 🧾 Lê arquivos .json


def read_json(path: str) -> str:
    """
    Reads the content of a .json file.

    Args:
        path (str): Path to the .txt file.
    Returns:
        str: Content of the file.
    """
    if not os.path.isfile(path) or not path.endswith(".json"):
        return "❌ Arquivo inválido ou não é .json"
    df = pd.read_json(path)
    return df.head(3).to_json(orient="records", force_ascii=False)
