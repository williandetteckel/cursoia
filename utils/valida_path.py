import os


def validar_caminho(path: str) -> str:
    if os.path.exists(path):
        return f"✅ Caminho válido: {path}"
    return f"❌ Caminho inválido ou inexistente: {path}"
