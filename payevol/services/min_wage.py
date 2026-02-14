import re
from datetime import date
import pandas as pd
import requests
import streamlit as st

SAL_MIN_URL = "https://previdenciarista.com/tabela-historica-dos-salarios-minimos/"

PT_BR_MONTH_ABBR = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12
}

@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def fetch_min_wage_changes() -> pd.DataFrame:
    """
    Mudanças do salário mínimo:
      ref_date (1º dia do mês), min_wage (float)
    Regra: só aceita valores que contenham 'R$' (evita pegar ano por engano).
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(SAL_MIN_URL, headers=headers, timeout=30)
    resp.raise_for_status()
    html = resp.text

    changes: list[tuple[date, float]] = []

    rx_mmmyyyy = re.compile(r"\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\s*/\s*(\d{4})\b", re.I)
    rx_brl = re.compile(r"R\$\s*([\d\.\,]+)")

    # 1) Via tabelas HTML (preferido)
    try:
        tables = pd.read_html(html)
        for t in tables:
            cols = [str(c).strip().lower() for c in t.columns]

            value_idx = next((i for i, c in enumerate(cols) if "valor" in c), None)
            if value_idx is None:
                continue
            value_col = t.columns[value_idx]

            ref_idx = next((i for i, c in enumerate(cols) if "desde" in c or "a partir" in c or "vig" in c), 0)
            ref_col = t.columns[ref_idx]

            for _, row in t.iterrows():
                ref_txt = "" if pd.isna(row.get(ref_col)) else str(row.get(ref_col))
                val_txt = "" if pd.isna(row.get(value_col)) else str(row.get(value_col))

                mref = rx_mmmyyyy.search(ref_txt)
                mval = rx_brl.search(val_txt)

                if not mref:
                    row_text = " ".join([str(x) for x in row.values if pd.notna(x)])
                    mref = rx_mmmyyyy.search(row_text)

                if not (mref and mval):
                    continue

                mm = PT_BR_MONTH_ABBR[mref.group(1).lower()]
                yyyy = int(mref.group(2))
                v = mval.group(1).replace(".", "").replace(",", ".")
                changes.append((date(yyyy, mm, 1), float(v)))

        if changes:
            df = pd.DataFrame(changes, columns=["ref_date", "min_wage"]).drop_duplicates()
            return df.sort_values("ref_date").reset_index(drop=True)
    except Exception:
        pass

    # 2) Fallback: regex no HTML inteiro (ancorado em "R$")
    rx_line = re.compile(
        r"\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\s*/\s*(\d{4})\b.*?R\$\s*([\d\.\,]+)",
        re.I
    )
    for mon, yyyy, val in rx_line.findall(html):
        mm = PT_BR_MONTH_ABBR[mon.lower()]
        v = val.replace(".", "").replace(",", ".")
        changes.append((date(int(yyyy), mm, 1), float(v)))

    if not changes:
        raise RuntimeError("Não consegui extrair a tabela de salário mínimo do site-fonte.")

    df = pd.DataFrame(changes, columns=["ref_date", "min_wage"]).drop_duplicates()
    return df.sort_values("ref_date").reset_index(drop=True)

def min_wage_at(ref: date, changes_df: pd.DataFrame) -> float:
    """
    Salário mínimo vigente na referência (ref = 1º dia do mês).
    """
    changes = changes_df.copy()
    changes["ref_date"] = pd.to_datetime(changes["ref_date"])
    changes = changes.sort_values("ref_date")

    q = pd.DataFrame({"ref_date": [pd.to_datetime(ref)]}).sort_values("ref_date")
    out = pd.merge_asof(q, changes, on="ref_date", direction="backward")
    v = float(out.loc[0, "min_wage"])
    if v <= 0:
        raise RuntimeError("Salário mínimo inválido na referência.")
    return v
