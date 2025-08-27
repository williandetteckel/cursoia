from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as date_parse
import numpy as np
import pandas as pd

def ensure_date(x):
    """Converte valores em objetos datetime.date."""
    if pd.isna(x):
        return None
    if isinstance(x, (datetime, date)):
        return x.date() if isinstance(x, datetime) else x
    try:
        return date_parse(str(x), dayfirst=True).date()
    except:
        return None

def month_bounds(competencia: str):
    """Recebe 'MM/YYYY' e retorna o primeiro e o último dia do mês."""
    m, y = competencia.split("/")
    start = date(int(y), int(m), 1)
    end = (start + relativedelta(months=1)) - relativedelta(days=1)
    return start, end

def business_days(start: date, end: date):
    """Conta dias úteis entre duas datas (segunda a sexta)."""
    return int(np.busday_count(start, end + relativedelta(days=1)))

def overlap_days(a_start, a_end, b_start, b_end):
    """Calcula sobreposição de dias úteis entre dois intervalos."""
    if any(x is None for x in [a_start, a_end, b_start, b_end]):
        return 0
    s, e = max(a_start, b_start), min(a_end, b_end)
    return business_days(s, e) if e >= s else 0
