from pathlib import Path
import pandas as pd
from utils.ajusta_valores import ajustar_valores_numericos

# Mapeamento de nomes de colunas diferentes para nomes padrão
COLMAP = {
    "matricula": ["matricula", "matrícula", "id", "employee id", "registro"],
    "admissao": ["admissão", "data admissão", "data_admissao", "admissao"],
    "sindicato": ["sindicato", "sindicato do colaborador"],
    "dias": ["dias", "dias úteis", "dias_uteis"],
    "valor_diario": ["valor diário vr", "valor_diario", "valor sindicato"],
    "competencia": ["competência", "competencia"],
    "inicio": ["inicio", "início", "data inicio"],
    "fim": ["fim", "data fim"],
    "data": ["data", "data desligamento"],
}

def canon(colname: str) -> str:
    """Normaliza o nome da coluna (lowercase e trim)."""
    return str(colname).strip().lower()

def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas do DataFrame para o padrão do COLMAP."""
    ren = {}
    cols = [canon(c) for c in df.columns]
    for k, variants in COLMAP.items():
        for v in variants:
            if canon(v) in cols:
                orig = df.columns[cols.index(canon(v))]
                ren[orig] = k
                break
    return df.rename(columns=ren)

def read_excel_safe(path: Path, sheet_name=0) -> pd.DataFrame:
    """Lê uma planilha Excel e normaliza suas colunas."""
    df = pd.read_excel(path, sheet_name=sheet_name)
    df = ajustar_valores_numericos(df, ["valor_diario", "TOTAL"])
    return norm_cols(df)
