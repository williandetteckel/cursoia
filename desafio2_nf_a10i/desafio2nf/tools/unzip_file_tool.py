# ./tools/unzip_file_tool.py

import os
import zipfile
from crewai.tools import tool # Importa o decorator 'tool'

@tool # Aplica o decorator para transformar a função em uma ferramenta
def unzip_file_tool(zip_file_path: str, destination_directory: str) -> str:
    """
    Descompacta um arquivo ZIP para um diretório de destino especificado.

    Args:
        zip_file_path (str): O caminho completo para o arquivo ZIP a ser descompactado.
        destination_directory (str): O caminho do diretório onde os arquivos serão extraídos.

    Returns:
        str: Uma mensagem de sucesso listando os arquivos extraídos ou uma mensagem de erro.
    """
    if not zip_file_path.endswith(".zip"):
        return f"Erro: O arquivo '{zip_file_path}' não é um arquivo ZIP válido."

    os.makedirs(destination_directory, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(destination_directory)

        extracted_files = zip_ref.namelist()
        if not extracted_files:
            return f"Aviso: O arquivo ZIP '{zip_file_path}' foi descompactado, mas nenhum arquivo foi encontrado. Diretório de destino: {destination_directory}"

        return f"Arquivos extraídos com sucesso para '{destination_directory}': {', '.join(extracted_files)}"
    except zipfile.BadZipFile:
        return f"Erro: O arquivo ZIP '{zip_file_path}' está corrompido ou é inválido."
    except Exception as e:
        return f"Erro inesperado ao descompactar '{zip_file_path}': {e}"