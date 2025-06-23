import os
import json
import pandas as pd
import zipfile
from langchain.tools import tool


# 📤 Extrai arquivos de um .zip
def extract_zip(path: str) -> str:
    """
    Extracts all files from a .zip into a subfolder within the same directory.
    The subfolder will be named 'extracted_<zip_name>'.

    Args:
        path (str): Path to the .zip file.

    Returns:
        str: List of extracted files or error messages.
    """
    if not path or path.strip() == "":
        return "❗ Por favor, informe o caminho completo do arquivo .zip para que eu possa extrair."

    path = os.path.abspath(os.path.normpath(path.strip('"')))

    if not os.path.exists(path):
        return f"❌ Caminho não encontrado: {path}"
    if not path.lower().endswith(".zip"):
        return "⚠️ O arquivo informado não é um .zip válido."

    try:
        extract_dir = os.path.join(
            os.path.dirname(path),
            f"extraido_{os.path.basename(path).replace('.zip', '')}"
        )
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            arquivos = zip_ref.namelist()

        if not arquivos:
            return f"📦 Arquivo .zip extraído, mas estava vazio. Pasta: {extract_dir}"

        resposta = f"✅ Arquivo .zip extraído com sucesso para: {extract_dir}\n"
        resposta += "📄 Arquivos extraídos:\n" + \
            "\n".join(f"- {a}" for a in arquivos)
        return resposta

    except Exception as e:
        return f"❌ Erro ao extrair o zip: {str(e)}"
