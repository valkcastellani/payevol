from datetime import date
import re
import pandas as pd
import requests
import streamlit as st

# SIDRA "values" no host correto (apisidra)
# Docs do SIDRA são referenciadas nesse domínio.  :contentReference[oaicite:2]{index=2}
IPCA_SIDRA_URL = "https://apisidra.ibge.gov.br/values/h/n/t/1737/p/all/n1/all/v/2266"

def _to_float_maybe_ptbr(s: str) -> float:
    s = s.strip()
    # Se vier "1.234,56" -> 1234.56
    if "," in s and "." in s:
        return float(s.replace(".", "").replace(",", "."))
    # Se vier "1234,56" -> 1234.56
    if "," in s:
        return float(s.replace(",", "."))
    return float(s)

def _find_period_key(item: dict) -> str | None:
    """
    No JSON do SIDRA, o período costuma vir em uma chave tipo D1C, D2C etc.
    Vamos achar a primeira chave D{n}C cujo valor pareça YYYYMM.
    """
    rx = re.compile(r"^D\d+C$")
    for k, v in item.items():
        if not rx.match(k):
            continue
        vv = str(v).strip()
        if vv.isdigit() and len(vv) == 6:  # YYYYMM
            return k
    return None

@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def fetch_ipca_number_index() -> pd.DataFrame:
    """
    IPCA - número-índice (mensal) via SIDRA.
    Saída: ref_date (1º dia do mês), ipca_index (float)

    Tabela: 1737 / Variável: 2266 (número-índice)
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(IPCA_SIDRA_URL, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()

    if not isinstance(data, list) or len(data) < 2:
        raise RuntimeError("Resposta inesperada do SIDRA (JSON não é uma lista com dados).")

    rows = []
    for item in data[1:]:  # 1ª linha geralmente é cabeçalho
        if not isinstance(item, dict):
            continue

        period_key = _find_period_key(item)
        if not period_key:
            continue

        period = str(item.get(period_key, "")).strip()  # YYYYMM
        val = str(item.get("V", "")).strip()

        if not (period.isdigit() and len(period) == 6 and val):
            continue

        try:
            y = int(period[:4])
            m = int(period[4:])
            v = _to_float_maybe_ptbr(val)
        except Exception:
            continue

        rows.append((date(y, m, 1), v))

    df = pd.DataFrame(rows, columns=["ref_date", "ipca_index"]).drop_duplicates()
    df = df.sort_values("ref_date").reset_index(drop=True)

    if df.empty:
        raise RuntimeError("Não foi possível obter a série do IPCA (número-índice) do SIDRA.")
    return df
