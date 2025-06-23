import os
import json
import pandas as pd
import zipfile
from langchain.tools import tool

# 📁 Lista arquivos e extensões
def list_files(path: str) -> str:
    """
    Lists the files in a directory and shows their extensions.
    Also indicates if there are any .zip files present in the folder.

    Args:
        path (str): Directory path.

    Returns:
        str: List of files and their extensions.
    """
    path = os.path.normpath(path.strip('"'))
    if not os.path.exists(path):
        return f"❌ Caminho não encontrado: {path}"
    if not os.path.isdir(path):
        return "⚠️ Esse caminho não é um diretório."

    arquivos = os.listdir(path)
    if not arquivos:
        return "📂 O diretório está vazio."

    resposta = "📄 Arquivos encontrados:\n"
    for f in arquivos:
        nome, ext = os.path.splitext(f)
        linha = f"- {f} (extensão: {ext or 'sem extensão'})"
        if ext.lower() == ".zip":
            linha += " [🔒 ZIP]"
        resposta += linha + "\n"
    return resposta
