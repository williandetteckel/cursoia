import pandas as pd
import numpy as np
import re

def ajustar_valores_numericos(df: pd.DataFrame, colunas: list) -> pd.DataFrame:
    """
    Ajusta valores inconsistentes em colunas numéricas de um DataFrame.
    
    - Converte valores no formato brasileiro (ex: '1.234,56') para float (1234.56).
    - Remove caracteres inválidos como 'R$', 'USD', espaços ou texto não numérico.
    - Preenche valores inválidos com NaN, mantendo a coerência do DataFrame.
    
    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame que contém as colunas a ajustar.
    colunas : list
        Lista com os nomes das colunas que devem ser tratadas.
    
    Retorna:
    --------
    pd.DataFrame
        DataFrame com as colunas corrigidas.
    """
    
    def limpar_valor(x):
        if pd.isna(x):  # se o valor já é nulo, mantém
            return np.nan
        if isinstance(x, (int, float)):  # se já é numérico, mantém
            return float(x)
        x_str = str(x).strip()
        
        # Remove caracteres não numéricos (exceto dígitos, ponto e vírgula)
        x_str = re.sub(r'[^0-9,.-]', '', x_str)
        
        # Converte vírgula decimal para ponto se necessário
        if ',' in x_str and '.' in x_str:
            # Ex: 1.234,56 (padrão BR) -> remover separador de milhar (ponto) e trocar vírgula por ponto
            x_str = x_str.replace('.', '').replace(',', '.')
        elif ',' in x_str and '.' not in x_str:
            # Ex: 123,45 -> troca vírgula por ponto
            x_str = x_str.replace(',', '.')
        
        try:
            return float(x_str)
        except:
            return np.nan  # se não conseguir converter, devolve NaN
    
    for col in colunas:
        if col in df.columns:
            df[col] = df[col].apply(limpar_valor)
    
    return df
